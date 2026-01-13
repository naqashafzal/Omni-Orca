import customtkinter as ctk
import asyncio
import threading
import sys
from browser_agent import BrowserAgent
from voice_commander import VoiceCommander
from gemini_client import GeminiClient
from config_manager import ConfigManager

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Futuristic Palette
COLOR_BG = "#0f0f0f"        
COLOR_PANEL = "#1a1a1a"     
COLOR_ACCENT = "#00e5ff"    
COLOR_ACCENT_HOVER = "#00b8cc"
COLOR_TEXT = "#ffffff"
COLOR_LOG = "#2b2b2b"
COLOR_ERROR = "#ff3333"
COLOR_SUCCESS = "#00ff66"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("A U T O M A T E R  //  V 1 . 1")
        self.geometry("950x750")
        self.configure(fg_color=COLOR_BG)

        self.cfg = ConfigManager()

        # --- Asyncio & Application State ---
        self.agent = BrowserAgent(headless=False)
        self.loop = asyncio.new_event_loop()
        self.agent_thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.agent_thread.start()
        
        try:
            self.commander = VoiceCommander()
            self.voice_available = True
        except:
            self.voice_available = False

        self.gemini = GeminiClient()
        
        # Load API Key from Config
        saved_key = self.cfg.get("api_key")
        self.use_ai = False
        if saved_key:
            self.gemini.configure(saved_key)
            self.use_ai = True

        self.is_listening = False

        # --- TABVIEW ---
        self.tab_view = ctk.CTkTabview(self, fg_color=COLOR_BG)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_cmd = self.tab_view.add("COMMAND CENTER")
        self.tab_settings = self.tab_view.add("SYSTEM SETTINGS")

        self._setup_command_tab()
        self._setup_settings_tab()

        self.log(">> SYSTEM INITIALIZED...")
        if self.use_ai:
            self.log(">> NEURAL LINK ESTABLISHED (API KEY LOADED).")
        else:
            self.log(">> WARNING: NO API KEY LINKED. AI MODULE OFFLINE.")

    def _setup_command_tab(self):
        parent = self.tab_cmd
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # 1. Header is technically the tab title, but we can add a sub-header
        self.label_title = ctk.CTkLabel(
            parent, 
            text="A U T O M A TE R   N E U R A L   L I N K", 
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=COLOR_ACCENT
        )
        self.label_title.grid(row=0, column=0, pady=10)

        # 2. Controls Dashboard
        self.dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.dashboard_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.dashboard_frame.grid_columnconfigure((0, 1), weight=1)

        # Left Panel: Core
        self.panel_core = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_PANEL, corner_radius=10, border_color="#333", border_width=1)
        self.panel_core.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.panel_core, text="SYSTEM CONTROLS", font=("Consolas", 12, "bold"), text_color="gray").pack(pady=5)
        
        self.btn_start = ctk.CTkButton(self.panel_core, text="INITIALIZE BROWSER", command=self.start_browser, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black", font=("Consolas", 12, "bold"))
        self.btn_start.pack(fill="x", padx=10, pady=5)
        self.btn_close = ctk.CTkButton(self.panel_core, text="TERMINATE SESSION", command=self.close_browser, fg_color=COLOR_PANEL, border_color=COLOR_ERROR, border_width=1, hover_color="#330000", text_color=COLOR_ERROR, font=("Consolas", 12, "bold"))
        self.btn_close.pack(fill="x", padx=10, pady=5)

        # Right Panel: Rec
        self.panel_rec = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_PANEL, corner_radius=10, border_color="#333", border_width=1)
        self.panel_rec.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(self.panel_rec, text="MEMORY MODULE", font=("Consolas", 12, "bold"), text_color="gray").pack(pady=5)
        self.btn_rec_save = ctk.CTkButton(self.panel_rec, text="SAVE SEQUENCE", command=self.save_recording, fg_color=COLOR_PANEL, border_color=COLOR_ACCENT, border_width=1, text_color=COLOR_ACCENT)
        self.btn_rec_save.pack(side="left", fill="both", expand=True, padx=5, pady=10)
        self.btn_replay = ctk.CTkButton(self.panel_rec, text="EXECUTE REPLAY", command=self.replay_recording, fg_color=COLOR_PANEL, border_color=COLOR_SUCCESS, border_width=1, text_color=COLOR_SUCCESS)
        self.btn_replay.pack(side="right", fill="both", expand=True, padx=5, pady=10)

        # 3. Log Console
        self.log_textbox = ctk.CTkTextbox(parent, fg_color=COLOR_LOG, text_color=COLOR_SUCCESS, font=("Consolas", 13), corner_radius=10)
        self.log_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # 4. Mode Selection (New)
        self.frame_mode = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_mode.grid(row=3, column=0, sticky="ew", padx=10)
        
        ctk.CTkLabel(self.frame_mode, text="ACTIVE PERSONA:", font=("Consolas", 12, "bold"), text_color="gray").pack(side="left", padx=5)
        self.option_mode = ctk.CTkOptionMenu(self.frame_mode, values=["GENERAL", "SOCIAL_MEDIA", "CRYPTO_TRADER"], fg_color=COLOR_PANEL, button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER, text_color="white")
        self.option_mode.pack(side="left", padx=5)
        self.option_mode.set("GENERAL")

        # 5. Command Bar
        self.cmd_frame = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, height=80, corner_radius=10)
        self.cmd_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.btn_voice = ctk.CTkButton(self.cmd_frame, text="🎤 VOX: OFF", command=self.toggle_listening, width=100, fg_color=COLOR_PANEL, border_color="#555", border_width=1, font=("Consolas", 11, "bold"))
        self.btn_voice.pack(side="left", padx=20, pady=20)
        if not self.voice_available: self.btn_voice.configure(state="disabled", text="VOX N/A")

        self.entry_cmd = ctk.CTkEntry(self.cmd_frame, placeholder_text="ENTER COMMAND SEQUENCE...", font=("Consolas", 14), fg_color="#000000", border_color="#333", text_color="white")
        self.entry_cmd.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=20)
        self.entry_cmd.bind("<Return>", lambda event: self.submit_text_command())
        self.btn_submit = ctk.CTkButton(self.cmd_frame, text="EXECUTE", command=self.submit_text_command, width=100, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
        self.btn_submit.pack(side="right", padx=20, pady=20)

    def _setup_settings_tab(self):
        parent = self.tab_settings
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(parent, text="CONFIGURATION MATRIX", font=("Consolas", 18, "bold"), text_color="gray").pack(pady=20)

        # API Key Section
        self.frame_api = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
        self.frame_api.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.frame_api, text="GOOGLE GEMINI API KEY", font=("Consolas", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.entry_settings_api = ctk.CTkEntry(self.frame_api, placeholder_text="Paste your API key here", show="*", width=400)
        self.entry_settings_api.pack(anchor="w", padx=20, pady=(0, 10))
        if self.cfg.get("api_key"):
            self.entry_settings_api.insert(0, self.cfg.get("api_key"))

        self.btn_test_api = ctk.CTkButton(self.frame_api, text="TEST CONNECTION & SAVE", command=self.test_and_save_api, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
        self.btn_test_api.pack(anchor="w", padx=20, pady=(10, 20))
        
        self.lbl_api_status = ctk.CTkLabel(self.frame_api, text="", font=("Consolas", 12))
        self.lbl_api_status.pack(anchor="w", padx=20, pady=(0, 20))

        # Model Config Section (Optional future expansion)
        self.frame_model = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
        self.frame_model.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.frame_model, text="MODEL CONFIGURATION", font=("Consolas", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.lbl_model = ctk.CTkLabel(self.frame_model, text=f"CURRENT MODEL: {self.cfg.get('model_name')}", font=("Consolas", 12))
        self.lbl_model.pack(anchor="w", padx=20, pady=(0, 20))


    # --- Settings Logic ---
    def test_and_save_api(self):
        key = self.entry_settings_api.get().strip()
        if not key:
            self.lbl_api_status.configure(text="STATUS: EMPTY KEY", text_color=COLOR_ERROR)
            return

        self.lbl_api_status.configure(text="STATUS: TESTING...", text_color="white")
        
        # Test in thread
        threading.Thread(target=self._test_api_thread, args=(key,)).start()

    def _test_api_thread(self, key):
        # Temp configure to test
        previous_key = self.gemini.api_key
        try:
            self.gemini.configure(key)
            # Try a dummy generation
            self.gemini.model.generate_content("ping")
            
            # success
            self.cfg.set("api_key", key)
            self.use_ai = True
            self.after(0, lambda: self.lbl_api_status.configure(text="STATUS: CONNECTION SUCCESSFUL. SAVED.", text_color=COLOR_SUCCESS))
            self.log("SETTINGS: API KEY UPDATED AND VERIFIED.")
        except Exception as e:
            # Revert if failed (optional, or leave broken)
            # self.gemini.configure(previous_key) 
            error_msg = str(e)
            self.after(0, lambda: self.lbl_api_status.configure(text=f"STATUS: FAILED - {error_msg}", text_color=COLOR_ERROR))


    # --- Utilities ---
    def log(self, message):
        self.log_textbox.insert("end", f">> {message}\n")
        self.log_textbox.see("end")

    def update_log_from_thread(self, message):
         self.after(0, lambda: self.log(message))

    # --- Async Infrastructure ---
    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async(self, coroutine):
        asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    # --- Browser Control ---
    def start_browser(self):
        self.run_async(self._start_browser_task())

    async def _start_browser_task(self):
        try:
            await self.agent.start()
            self.update_log_from_thread("BROWSER ONLINE.")
        except Exception as e:
            self.update_log_from_thread(f"INIT ERROR: {e}")

    def close_browser(self):
        self.run_async(self._close_browser_task())

    async def _close_browser_task(self):
        await self.agent.close()
        self.update_log_from_thread("SESSION TERMINATED.")

    # --- Command Processing ---
    def submit_text_command(self):
        text = self.entry_cmd.get()
        if not text: return
        self.entry_cmd.delete(0, 'end')
        self.log(f"MANUAL INPUT: {text}")
        
        if self.use_ai:
            self.process_ai_command(text)
        else:
            self.process_command(text.lower())

    def process_ai_command(self, text):
        self.log("ANALYZING INTENT via GEMINI (VISION ACTIVE)...")
        # Capture screenshot first (sync or async?)
        # Since we are in main thread callback, we need to schedule async capture, or do it in the thread?
        # Browser access should be thread-safe(ish) or done via loop.
        # Safest: run entire flow in async task, then update UI.
        self.run_async(self._ai_pipeline(text))

    async def _ai_pipeline(self, text):
        # 0. Get Mode
        mode = self.option_mode.get()
        
        # 1. Capture Screen
        screenshot = await self.agent.get_screenshot_bytes()
        
        # 2. Call API (in thread executor to not block loop?)
        # Multimodal upload might be slow.
        # We can run sync blocking call in a thread executor provided by asyncio
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, self.gemini.interpret_command, text, screenshot, mode)
        
        self.update_log_from_thread(f"AI PLAN ({mode}): {response}")
        
        if "error" in response:
            self.update_log_from_thread(f"AI ERROR: {response['error']}")
            return

        action = response.get("action")
        
        # 3. Execute Action
        if action == "navigate":
            await self._navigate_task(response.get("url")) # Reuse existing task logic (checking if valid)
            # Actually _navigate_task is async, so we can await it directly.
            # But _navigate_task updates log via thread-safe call, which is fine.
        elif action == "click":
            await self.agent.click(response.get("selector"))
        elif action == "type":
            await self.agent.type(response.get("selector"), response.get("text"))
        elif action == "back":
             pass
        else:
            self.update_log_from_thread("AI UNCLEAR. FALLING BACK TO REGEX.")
            self.after(0, lambda: self.process_command(text.lower()))

    # Deprecated threaded method
    def _ai_thread(self, text):
        pass 

    def process_command(self, command):
        if "go to" in command or "goto" in command:
            url = command.replace("go to", "").replace("goto", "").strip()
            if not url.startswith("http"): url = "https://" + url
            self.run_async(self._navigate_task(url))
        elif "click" in command:
            selector = command.replace("click", "").strip()
            if selector: self.run_async(self.agent.click(selector))
            else: self.log("ERROR: MISSING TARGET SELECTOR.")
        elif "stop listening" in command:
             self.toggle_listening()
        elif "type" in command:
            if " into " in command:
                parts = command.replace("type", "").split(" into ")
                self.run_async(self.agent.type(parts[1].strip(), parts[0].strip()))
            else:
                 self.log("SYNTAX ERROR: USE 'type [text] into [selector]'")
        else:
             self.update_log_from_thread("UNKNOWN COMMAND SEQUENCE.")

    async def _navigate_task(self, url):
        try:
            self.update_log_from_thread(f"NAVIGATING TO: {url}")
            await self.agent.navigate(url)
            self.update_log_from_thread(f"ARRIVAL CONFIRMED.")
        except Exception as e:
            self.update_log_from_thread(f"NAV ERROR: {e}")

    # --- Recorder ---
    def save_recording(self):
        self.agent.save_recording("recording.json")
        self.log("SEQUENCE SAVED TO DISK.")

    def replay_recording(self):
        self.log("EXECUTING STORED SEQUENCE...")
        self.run_async(self._replay_task("recording.json"))

    async def _replay_task(self, filename):
        await self.agent.replay_recording(filename)
        self.update_log_from_thread("EXECUTION COMPLETE.")

    # --- Voice ---
    def toggle_listening(self):
        if not self.voice_available: return
        if self.is_listening:
            self.is_listening = False
            self.btn_voice.configure(text="🎤 VOX: OFF", fg_color=COLOR_PANEL, border_color="#555", text_color="white")
            self.log("AUDIO INPUT SEVERED.")
        else:
            self.is_listening = True
            self.btn_voice.configure(text="🔴 VOX: LIVE", fg_color=COLOR_LOG, border_color=COLOR_ERROR, text_color=COLOR_ERROR)
            self.log("AUDIO INPUT ACTIVE.")
            threading.Thread(target=self._continuous_listen_thread, daemon=True).start()

    def _continuous_listen_thread(self):
        while self.is_listening:
            command = self.commander.listen()
            if command:
                self.update_log_from_thread(f"VOICE INPUT: {command}")
                if "stop listening" in command:
                     self.is_listening = False
                     self.after(0, lambda: self.btn_voice.configure(text="🎤 VOX: OFF", fg_color=COLOR_PANEL, border_color="#555", text_color="white"))
                     self.update_log_from_thread("VOX TERMINATED BY USER.")
                     break
                
                if self.use_ai:
                    self.process_ai_command(command)
                else:
                    self.process_command(command)

    def on_closing(self):
        self.run_async(self.agent.close())
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
