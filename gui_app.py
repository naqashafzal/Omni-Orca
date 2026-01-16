import customtkinter as ctk
import asyncio
import threading
import sys
from browser_agent import BrowserAgent
from voice_commander import VoiceCommander
from llm_provider import LLMClient
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

        self.llm = LLMClient()
        
        # Load API Key from Config and configure provider
        saved_key = self.cfg.get("api_key")
        saved_provider = self.cfg.get("llm_provider") or "gemini"  # Default to gemini
        self.use_ai = False
        
        if saved_key and saved_provider == "gemini":
            self.llm.configure_gemini(saved_key)
            self.use_ai = True
        elif saved_provider == "ollama":
            ollama_model = self.cfg.get("ollama_model") or "llava:latest"
            self.llm.configure_ollama(ollama_model)
            self.use_ai = True

        self.is_listening = False
        self.autopilot_active = False
        self.autopilot_stop_requested = False
        self.autopilot_max_iterations = 20

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

        self.autopilot_checkbox = ctk.CTkCheckBox(self.cmd_frame, text="🤖 AUTO-PILOT", font=("Consolas", 11, "bold"), text_color=COLOR_ACCENT)
        self.autopilot_checkbox.pack(side="left", padx=10, pady=20)

        self.btn_stop_autopilot = ctk.CTkButton(self.cmd_frame, text="⏹ STOP", command=self.stop_autopilot, width=80, fg_color=COLOR_ERROR, hover_color="#990000", text_color="white", font=("Consolas", 11, "bold"))
        self.btn_stop_autopilot.pack(side="left", padx=5, pady=20)
        self.btn_stop_autopilot.pack_forget()  # Hide initially

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

        # Model Config Section
        self.frame_model = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
        self.frame_model.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.frame_model, text="LLM PROVIDER", font=("Consolas", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        # Provider selection
        self.provider_var = ctk.StringVar(value=self.cfg.get("llm_provider") or "gemini")
        provider_frame = ctk.CTkFrame(self.frame_model, fg_color="transparent")
        provider_frame.pack(anchor="w", padx=20, pady=5)
        
        self.radio_gemini = ctk.CTkRadioButton(provider_frame, text="Google Gemini (Cloud)", variable=self.provider_var, value="gemini", command=self.on_provider_change)
        self.radio_gemini.pack(side="left", padx=10)
        
        self.radio_ollama = ctk.CTkRadioButton(provider_frame, text="Ollama (Local)", variable=self.provider_var, value="ollama", command=self.on_provider_change)
        self.radio_ollama.pack(side="left", padx=10)
        
        # Ollama configuration
        self.frame_ollama = ctk.CTkFrame(self.frame_model, fg_color="transparent")
        self.frame_ollama.pack(anchor="w", padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(self.frame_ollama, text="Ollama Model:", font=("Consolas", 10)).pack(side="left", padx=5)
        self.ollama_model_entry = ctk.CTkEntry(self.frame_ollama, width=200, placeholder_text="llava:latest")
        self.ollama_model_entry.pack(side="left", padx=5)
        if self.cfg.get("ollama_model"):
            self.ollama_model_entry.insert(0, self.cfg.get("ollama_model"))
        
        self.btn_save_ollama = ctk.CTkButton(self.frame_ollama, text="SAVE & CONNECT", command=self.save_ollama_config, width=120, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
        self.btn_save_ollama.pack(side="left", padx=5)
        
        # Show/hide based on selection
        self.on_provider_change()
        
        # Current status
        self.lbl_model = ctk.CTkLabel(self.frame_model, text=f"CURRENT: {self.llm.get_provider_name().upper()}", font=("Consolas", 12))
        self.lbl_model.pack(anchor="w", padx=20, pady=(10, 20))


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
        try:
            # Test by configuring Gemini
            self.llm.configure_gemini(key)
            # Try a dummy generation (access the provider directly for testing)
            if hasattr(self.llm.provider, 'model'):
                self.llm.provider.model.generate_content("ping")
            
            # success
            self.cfg.set("api_key", key)
            self.cfg.set("llm_provider", "gemini")
            self.use_ai = True
            self.after(0, lambda: self.lbl_api_status.configure(text="STATUS: CONNECTION SUCCESSFUL. SAVED.", text_color=COLOR_SUCCESS))
            self.after(0, lambda: self.lbl_model.configure(text=f"CURRENT: {self.llm.get_provider_name().upper()}"))
            self.log("SETTINGS: API KEY UPDATED AND VERIFIED.")
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.lbl_api_status.configure(text=f"STATUS: FAILED - {error_msg}", text_color=COLOR_ERROR))

    def on_provider_change(self):
        """Show/hide provider-specific settings"""
        provider = self.provider_var.get()
        if provider == "ollama":
            self.frame_ollama.pack(anchor="w", padx=20, pady=10, fill="x")
            self.frame_api.pack_forget()
        else:
            self.frame_ollama.pack_forget()
            self.frame_api.pack(fill="x", padx=20, pady=10)

    def save_ollama_config(self):
        """Save and connect to Ollama"""
        model = self.ollama_model_entry.get().strip() or "llava:latest"
        
        try:
            self.llm.configure_ollama(model)
            self.cfg.set("llm_provider", "ollama")
            self.cfg.set("ollama_model", model)
            self.use_ai = True
            self.lbl_model.configure(text=f"CURRENT: OLLAMA ({model})")
            self.log(f"SETTINGS: OLLAMA CONFIGURED ({model})")
        except Exception as e:
            self.log(f"ERROR: Failed to configure Ollama - {str(e)}")


    # --- Utilities ---
    def log(self, message):
        self.log_textbox.insert("end", f">> {message}\n")
        self.log_textbox.see("end")

    def update_log_from_thread(self, message, color=None):
        """Thread-safe log update with optional color."""
        if color:
            self.after(0, lambda: self._log_colored(message, color))
        else:
            self.after(0, lambda: self.log(message))

    def _log_colored(self, message, color):
        """Log with custom color."""
        self.log_textbox.insert("end", f">> {message}\n", color)
        self.log_textbox.tag_config(color, foreground=color)
        self.log_textbox.see("end")

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
        
        # Check if auto-pilot mode is enabled
        if self.autopilot_checkbox.get():
            if not self.use_ai:
                self.log("ERROR: AUTO-PILOT REQUIRES API KEY.")
                return
            self.log("INITIATING AUTO-PILOT MODE...")
            self.run_async(self._autopilot_loop(text))
        elif self.use_ai:
            self.process_ai_command(text)
        else:
            self.process_command(text)

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
        response = await loop.run_in_executor(None, self.llm.interpret_command, text, screenshot, mode)
        
        self.update_log_from_thread(f"AI PLAN ({mode}): {response}")
        
        # 3. Execute Action Sequence
        if isinstance(response, dict) and "error" in response:
             self.update_log_from_thread(f"AI ERROR: {response['error']}")
             return

        if not isinstance(response, list):
             self.update_log_from_thread("AI ERROR: INVALID RESPONSE FORMAT.")
             return

        for step in response:
            action = step.get("action")
            self.update_log_from_thread(f"EXECUTING: {action.upper()}")
            
            if action == "navigate":
                await self._navigate_task(step.get("url"))
            elif action == "click":
                await self.agent.click(step.get("selector"))
            elif action == "type":
                await self.agent.type(step.get("selector"), step.get("text"))
            elif action == "wait":
                sec = step.get("seconds", 1)
                await asyncio.sleep(sec)
            elif action == "back":
                 pass # Implement back if needed
            elif action == "mouse_click":
                await self.agent.mouse_click(step.get("x"), step.get("y"), 
                                             step.get("button", "left"), 
                                             step.get("click_count", 1))
            elif action == "mouse_move":
                await self.agent.mouse_move(step.get("x"), step.get("y"))
            elif action == "hover":
                await self.agent.hover(step.get("selector"))
            elif action == "right_click":
                await self.agent.right_click(step.get("selector"))
            elif action == "double_click":
                await self.agent.double_click(step.get("selector"))
            elif action == "scroll":
                await self.agent.scroll(step.get("x", 0), step.get("y", 0))
            elif action == "press_key":
                await self.agent.press_key(step.get("key"))
            elif action == "get_text":
                text = await self.agent.get_text(step.get("selector"))
                self.update_log_from_thread(f"EXTRACTED TEXT: {text[:100] if text else 'None'}...")
            elif action == "copy_to_clipboard":
                await self.agent.copy_to_clipboard(step.get("text"))
            elif action == "paste_from_clipboard":
                await self.agent.paste_from_clipboard(step.get("selector"))
            elif action == "extract_data":
                data = await self.agent.extract_data(step.get("selector"), step.get("attribute", "textContent"))
                self.update_log_from_thread(f"EXTRACTED {len(data)} ITEMS")
            elif action == "wait_for_text":
                await self.agent.wait_for_text(step.get("text"))
            else:
                self.update_log_from_thread(f"UNKNOWN AI ACTION: {action}")
            
            # Small delay between steps
            await asyncio.sleep(0.5)

    # Deprecated threaded method
    def _ai_thread(self, text):
        pass 

    def process_command(self, command):
        import re
        command_stripped = command.strip()
        
        # Regex patterns (case-insensitive for keywords)
        match_goto = re.search(r"^(?:go\s*to|goto)\s+(.+)", command_stripped, re.IGNORECASE)
        match_click = re.search(r"^click\s+(.+)", command_stripped, re.IGNORECASE)
        match_type = re.search(r"^type\s+(.+)\s+into\s+(.+)", command_stripped, re.IGNORECASE)
        match_stop = re.search(r"stop\s+listening", command_stripped, re.IGNORECASE)

        if match_goto:
            url = match_goto.group(1).strip()
            if not url.startswith("http"): url = "https://" + url
            self.run_async(self._navigate_task(url))
        
        elif match_click:
            selector = match_click.group(1).strip()
            self.run_async(self._click_task(selector))
            
        elif match_stop:
             self.toggle_listening()
             
        elif match_type:
            text_to_type = match_type.group(1).strip()
            selector = match_type.group(2).strip()
            self.run_async(self._type_task(selector, text_to_type))
            
        else:
             self.update_log_from_thread("UNKNOWN COMMAND SEQUENCE.")

    async def _click_task(self, selector):
        try:
            await self.agent.click(selector)
            self.update_log_from_thread(f"CLICKED: {selector}")
        except Exception as e:
            self.update_log_from_thread(f"CLICK ERROR: {e}")

    async def _type_task(self, selector, text):
        try:
            await self.agent.type(selector, text)
            self.update_log_from_thread(f"TYPED '{text}' INTO {selector}")
        except Exception as e:
            self.update_log_from_thread(f"TYPE ERROR: {e}")

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

    # --- Auto-Pilot ---
    def stop_autopilot(self):
        """Stops the auto-pilot loop."""
        self.autopilot_stop_requested = True
        self.log("AUTO-PILOT STOP REQUESTED...")

    async def _autopilot_loop(self, goal):
        """Main auto-pilot loop: observe, decide, act, repeat."""
        self.autopilot_active = True
        self.autopilot_stop_requested = False
        self.after(0, lambda: self.btn_stop_autopilot.pack(side="left", padx=5, pady=20))
        
        # Start recording
        self.agent.start_recording(name=goal, mode="autopilot")
        
        iteration = 0
        success = False
        
        try:
            while iteration < self.autopilot_max_iterations and not self.autopilot_stop_requested:
                iteration += 1
                self.update_log_from_thread(f"AUTO-PILOT [{iteration}/{self.autopilot_max_iterations}]")
                
                # Capture screenshot
                screenshot = await self.agent.get_screenshot_bytes()
                
                # Get AI decision
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, self.llm.autopilot_step, goal, screenshot)
                
                # Check for errors
                if "error" in response:
                    self.update_log_from_thread(f"AUTO-PILOT ERROR: {response['error']}")
                    break
                
                # Log reasoning
                reasoning = response.get("reasoning", "")
                self.update_log_from_thread(f"AI REASONING: {reasoning}", color=COLOR_ACCENT)
                
                # Check if completed
                if response.get("completed", False):
                    self.update_log_from_thread("AUTO-PILOT: GOAL ACHIEVED!")
                    success = True
                    break
                
                # Execute actions
                actions = response.get("actions", [])
                for step in actions:
                    action = step.get("action")
                    self.update_log_from_thread(f"  → {action.upper()}")
                    
                    try:
                        if action == "navigate":
                            await self._navigate_task(step.get("url"))
                        elif action == "click":
                            await self.agent.click(step.get("selector"))
                        elif action == "type":
                            await self.agent.type(step.get("selector"), step.get("text"))
                        elif action == "wait":
                            sec = step.get("seconds", 1)
                            await asyncio.sleep(sec)
                        elif action == "back":
                            pass  # Implement if needed
                        elif action == "mouse_click":
                            await self.agent.mouse_click(step.get("x"), step.get("y"), 
                                                         step.get("button", "left"), 
                                                         step.get("click_count", 1))
                        elif action == "mouse_move":
                            await self.agent.mouse_move(step.get("x"), step.get("y"))
                        elif action == "hover":
                            await self.agent.hover(step.get("selector"))
                        elif action == "right_click":
                            await self.agent.right_click(step.get("selector"))
                        elif action == "double_click":
                            await self.agent.double_click(step.get("selector"))
                        elif action == "scroll":
                            await self.agent.scroll(step.get("x", 0), step.get("y", 0))
                        elif action == "press_key":
                            await self.agent.press_key(step.get("key"))
                        elif action == "get_text":
                            text = await self.agent.get_text(step.get("selector"))
                            self.update_log_from_thread(f"EXTRACTED: {text[:100] if text else 'None'}...")
                        elif action == "copy_to_clipboard":
                            await self.agent.copy_to_clipboard(step.get("text"))
                        elif action == "paste_from_clipboard":
                            await self.agent.paste_from_clipboard(step.get("selector"))
                        elif action == "extract_data":
                            data = await self.agent.extract_data(step.get("selector"), step.get("attribute", "textContent"))
                            self.update_log_from_thread(f"EXTRACTED {len(data)} ITEMS")
                        elif action == "wait_for_text":
                            await self.agent.wait_for_text(step.get("text"))
                    except Exception as e:
                        self.update_log_from_thread(f"ACTION ERROR: {e}")
                
                # Delay between iterations
                await asyncio.sleep(1.5)
            
            if iteration >= self.autopilot_max_iterations:
                self.update_log_from_thread("AUTO-PILOT: MAX ITERATIONS REACHED.")
            
            if self.autopilot_stop_requested:
                self.update_log_from_thread("AUTO-PILOT: STOPPED BY USER.")
                
        finally:
            # Save recording
            filename = self.agent.save_recording(success=success)
            self.update_log_from_thread(f"RECORDING SAVED: {filename}")
            
            # Reset state
            self.autopilot_active = False
            self.after(0, lambda: self.btn_stop_autopilot.pack_forget())

    def on_closing(self):
        self.run_async(self.agent.close())
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
