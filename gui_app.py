import customtkinter as ctk
ctk.set_appearance_mode("dark")
import asyncio
import threading
import sys
from agents.browser_agent import BrowserAgent
from utils.voice_commander import VoiceCommander
from core.llm_provider import LLMClient
from core.config_manager import ConfigManager
import schedule
import time
import pandas as pd
from utils.tts_engine import TTSEngine
from utils.auth_handler import perform_login, PLATFORM_MAP
from tools.content_engine import ContentGenerator
from PIL import Image, ImageTk
from trading.trading_engine import TradingEngine, MarketData
from trading.trading_strategies import STRATEGIES
from trading.risk_manager import RiskManager, Portfolio, Position
from trading.exchange_client import ExchangeClient
from trading.browser_trading_client import BrowserTradingClient, HybridTradingClient
from tools.social_media_manager import SocialMediaManager
from core.agent_orchestrator import AgentOrchestrator
from agents.os_agent import OSAgent
from agents.vision_agent import VisionAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.call_agent import CallAgent
from agents.wake_word_agent import WakeWordAgent
from agents.web_search_agent import WebSearchAgent
from tools.business_scraper import BusinessScraper
import re

# ═══════════════════════════════════════════
# ELITE DARK THEME  —  Neural Omni V3
# ═══════════════════════════════════════════
COLOR_BG         = "#050508"   # Void black
COLOR_SIDEBAR    = "#0a0a12"   # Deep midnight
COLOR_PANEL      = "#0e0e1a"   # Dark navy card
COLOR_PANEL2     = "#131325"   # Slightly lighter card
COLOR_ACCENT     = "#00f0ff"   # Electric cyan
COLOR_ACCENT_HOVER = "#00c8d4" # Cyan hover
COLOR_GOLD       = "#ffc857"   # Gold metallic
COLOR_GOLD2      = "#e0a030"   # Deep gold
COLOR_BORDER     = "#1e1e38"   # Subtle border
COLOR_TEXT       = "#e8eaf6"   # Soft white
COLOR_TEXT_DIM   = "#5c6082"   # Dimmed text
COLOR_LOG        = "#070710"   # Terminal black
COLOR_ERROR      = "#ff4466"   # Hot pink error
COLOR_SUCCESS    = "#00ff99"   # Matrix green
COLOR_WARN       = "#ffaa00"   # Amber warning

# ═══════════════════════════════════════════
# NOTIFICATION SYSTEM
# ═══════════════════════════════════════════
import json as _json
import os as _os

NOTIF_FILE = "notifications.json"

def _load_notif_config():
    try:
        if _os.path.exists(NOTIF_FILE):
            with open(NOTIF_FILE, 'r') as f:
                return _json.load(f)
    except:
        pass
    return None

def _save_notif_config(cfg):
    try:
        with open(NOTIF_FILE, 'w') as f:
            _json.dump(cfg, f, indent=4)
    except:
        pass


class NotificationBanner(ctk.CTkToplevel):
    """Animated sliding-in notification popup shown on startup."""
    STYLE_MAP = {
        "info":    {"accent": "#00f0ff", "icon": "ℹ️"},
        "update":  {"accent": "#ffc857", "icon": "⬆️"},
        "warning": {"accent": "#ff9900", "icon": "⚠️"},
        "success": {"accent": "#00ff99", "icon": "✅"},
    }

    def __init__(self, parent, title, message, style="info", duration=8):
        super().__init__(parent)
        self.parent_win = parent
        self.duration = duration
        s = self.STYLE_MAP.get(style, self.STYLE_MAP["info"])
        accent = s["accent"]
        icon   = s["icon"]

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0e0e1a")
        self.attributes("-alpha", 0.0)

        # Size & position — bottom-right corner of parent
        w, h = 380, 120
        self.geometry(f"{w}x{h}")
        self._target_x = parent.winfo_x() + parent.winfo_width() - w - 20
        self._target_y = parent.winfo_y() + parent.winfo_height() - h - 20
        self._start_y  = self._target_y + 60
        self.geometry(f"{w}x{h}+{self._target_x}+{int(self._start_y)}")

        # Left accent bar
        bar = ctk.CTkFrame(self, width=5, fg_color=accent, corner_radius=0)
        bar.pack(side="left", fill="y")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Title row
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=f"{icon}  {title}",
                     font=("Consolas", 13, "bold"), text_color=accent).pack(side="left")

        # Close ×
        ctk.CTkButton(title_row, text="×", width=24, height=24, corner_radius=4,
                      fg_color="transparent", hover_color="#1e1e38",
                      text_color="#5c6082", font=("Consolas", 14, "bold"),
                      command=self._dismiss).pack(side="right")

        # Message
        ctk.CTkLabel(content, text=message, font=("Consolas", 11),
                     text_color="#e8eaf6", wraplength=310,
                     justify="left").pack(anchor="w", pady=(4, 0))

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, height=3, fg_color="#1e1e38",
                                            progress_color=accent, corner_radius=0)
        self.progress.pack(side="bottom", fill="x")
        self.progress.set(1.0)

        self._animate_in()

    def _animate_in(self, step=0):
        total = 10
        if step <= total:
            alpha = step / total
            progress_y = self._start_y + (self._target_y - self._start_y) * (step / total)
            self.attributes("-alpha", min(alpha, 0.96))
            self.geometry(f"+{self._target_x}+{int(progress_y)}")
            self.after(20, lambda: self._animate_in(step + 1))
        else:
            self._tick_progress(self.duration * 1000)

    def _tick_progress(self, remaining_ms):
        if remaining_ms <= 0:
            self._dismiss()
            return
        total_ms = self.duration * 1000
        self.progress.set(remaining_ms / total_ms)
        self.after(100, lambda: self._tick_progress(remaining_ms - 100))

    def _dismiss(self):
        try:
            self.destroy()
        except:
            pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OMNI  //  AGI EDITION  v3.0")
        self.geometry("1100x800")
        self.minsize(900, 650)
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
        self.content_gen = ContentGenerator(self.llm)
        self.social_manager = SocialMediaManager(self.agent, self.content_gen, self.llm)
        self.os_agent = OSAgent()
        self.orchestrator = AgentOrchestrator(self.llm, self.agent, self.social_manager, self.cfg, self.os_agent)
        self.vision_agent = VisionAgent(self.llm, gui_callback=self.show_vision_toast)
        # V3: Personal Assistant Modules
        self.email_agent_v3 = EmailAgent()
        self.calendar_agent_v3 = CalendarAgent()
        self.call_agent_v3 = CallAgent()
        self.web_search_v3 = WebSearchAgent()
        self.wake_word_agent = WakeWordAgent(on_activated_callback=self._on_wake_word)
        self.tts = TTSEngine()
        self.tts.speak("System Initialized")
        self.biz_scraper = BusinessScraper(
            self.agent, self.llm,
            log_callback=lambda msg: self.after(0, lambda m=msg: self._biz_log(m))
        )
        self._biz_results = []  # Cache for last scrape results
        
        # Scheduler Thread
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
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
        elif saved_provider == "openrouter":
            or_key = self.cfg.get("openrouter_key")
            or_model = self.cfg.get("openrouter_model") or "google/gemini-2.0-flash-001"
            if or_key:
                self.llm.configure_openrouter(or_key, or_model)
                self.use_ai = True

        self.is_listening = False
        self.autopilot_active = False
        self.autopilot_stop_requested = False
        self.autopilot_max_iterations = 20

        # --- LAYOUT Grid Configuration ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(
            self, width=230, corner_radius=0,
            fg_color=COLOR_SIDEBAR,
            border_color=COLOR_BORDER, border_width=1
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(15, weight=1)
        self.sidebar_frame.grid_propagate(False)

        # ── Logo Block ──────────────────────────────────────
        logo_block = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_block.pack(pady=(28, 0), padx=15, fill="x")

        ctk.CTkLabel(
            logo_block,
            text="P R O J E C T",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLOR_TEXT_DIM
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_block,
            text="O M N I",
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color=COLOR_ACCENT
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_block,
            text="AGI  EDITION",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLOR_GOLD
        ).pack(anchor="w")

        # Gold separator line
        sep = ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLOR_GOLD2)
        sep.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            self.sidebar_frame,
            text="  NAVIGATION",
            font=("Consolas", 9),
            text_color=COLOR_TEXT_DIM
        ).pack(anchor="w", padx=10, pady=(2, 4))

        # --- MAIN CONTENT FLUID ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Pre-process a 20% opacity watermark image for tab backgrounds
        self.watermark_img = None
        try:
            import os
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_internal_assets", "omni_logo.png")
            pil_img = Image.open(logo_path).convert("RGBA")
            alpha = pil_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.20))  # 20% opacity
            pil_img.putalpha(alpha)
            # Make it beautifully large in the center
            self.watermark_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(350, 350))
        except Exception as e:
            pass

        # Tab Router
        self.tabs = {}
        
        # Tab Icons mapping
        TAB_ICONS = {
            "COMMAND CENTER":   "⚡",
            "NEURAL CHAT":      "🧠",
            "SCHEDULER":        "🕐",
            "ACCOUNTS":         "🔑",
            "SOCIAL MEDIA PRO": "🐦",
            "WHATSAPP PRO":     "💬",
            "COMMUNICATIONS":   "📡",
            "DATA LAB":         "📊",
            "CRYPTO TRADER":    "₿",
            "AGENT LAB":        "🤖",
            "BIZ SCRAPER":      "🗂️",
            "SYSTEM SETTINGS":  "⚙️",
        }

        def add_tab(name):
            icon = TAB_ICONS.get(name, "›")
            btn = ctk.CTkButton(
                self.sidebar_frame,
                corner_radius=6,
                height=36,
                border_spacing=10,
                text=f"  {icon}  {name}",
                fg_color="transparent",
                text_color=COLOR_TEXT_DIM,
                hover_color=COLOR_PANEL2,
                anchor="w",
                font=("Consolas", 12, "bold"),
                command=lambda n=name: self.select_tab(n)
            )
            btn.pack(fill="x", padx=8, pady=1)
            frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
            
            # Inject centered watermark behind everything
            if self.watermark_img:
                wm_lbl = ctk.CTkLabel(frame, image=self.watermark_img, text="")
                wm_lbl.place(relx=0.5, rely=0.5, anchor="center")
                
            self.tabs[name] = {"button": btn, "frame": frame}
            return frame

        self.tab_cmd = add_tab("COMMAND CENTER")
        self.tab_chat = add_tab("NEURAL CHAT")
        self.tab_scheduler = add_tab("SCHEDULER")
        self.tab_accounts = add_tab("ACCOUNTS")
        self.tab_social = add_tab("SOCIAL MEDIA PRO")
        self.tab_whatsapp = add_tab("WHATSAPP PRO")
        self.tab_comms = add_tab("COMMUNICATIONS")
        self.tab_data = add_tab("DATA LAB")
        self.tab_crypto = add_tab("CRYPTO TRADER")
        self.tab_agent = add_tab("AGENT LAB")
        self.tab_biz = add_tab("BIZ SCRAPER")
        self.tab_settings = add_tab("SYSTEM SETTINGS")

        # ── Sidebar Footer (Credits & Logo) ──────────────────────────
        footer_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=(10, 15))

        ctk.CTkFrame(footer_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=15, pady=(0, 15))

        # Try to load and display the OMNI logo (Made Bigger)
        try:
            import os
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_internal_assets", "omni_logo.png")
            logo_img = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(85, 85))
            logo_lbl = ctk.CTkLabel(footer_frame, image=logo_img, text="")
            logo_lbl.pack(pady=(0, 10))
        except Exception as e:
            pass # Skip if image not generated yet

        ctk.CTkLabel(
            footer_frame,
            text="PROJECT BY ORCA",
            font=("Consolas", 10, "bold"),
            text_color=COLOR_ACCENT
        ).pack()

        ctk.CTkLabel(
            footer_frame,
            text="Author: Naqash Afzal",
            font=("Consolas", 9),
            text_color=COLOR_TEXT
        ).pack()

        # Clickable GitHub link
        github_lbl = ctk.CTkLabel(
            footer_frame,
            text="github.com/naqashafzal",
            font=("Consolas", 9, "underline"),
            text_color=COLOR_TEXT_DIM,
            cursor="hand2"
        )
        github_lbl.pack(pady=(2, 8))
        github_lbl.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://github.com/naqashafzal"))

        ctk.CTkLabel(
            footer_frame,
            text="● OMNI SYSTEM v3.0 ONLINE",
            font=("Consolas", 9),
            text_color=COLOR_SUCCESS
        ).pack()


        # Initialize trading system
        self.trading_engine = TradingEngine()
        self.portfolio = Portfolio(initial_balance=10000)
        self.risk_manager = RiskManager(self.portfolio)
        self.exchange_client = ExchangeClient(mode="paper", initial_balance=10000)
        self.trading_active = False
        self.current_symbol = "BTCUSDT"

        self._setup_command_tab()
        self._setup_chat_tab()
        self._setup_scheduler_tab()
        self._setup_accounts_tab()
        self._setup_social_tab()
        self._setup_whatsapp_tab()
        self._setup_communications_tab()
        self._setup_data_tab()
        self._setup_crypto_tab()
        self._setup_agent_tab()
        self._setup_biz_scraper_tab()
        self._setup_settings_tab()

        self.log(">> SYSTEM INITIALIZED...")
        if self.use_ai:
            self.log(">> NEURAL LINK ESTABLISHED (API KEY LOADED).")
        else:
            self.log(">> WARNING: NO API KEY LINKED. AI MODULE OFFLINE.")
            
        # Initial Selection
        self.select_tab("COMMAND CENTER")
        
        # Show startup notification after a short delay
        self.after(1500, self._show_startup_notification)

    def _show_startup_notification(self):
        """Show notification popup on startup if enabled in notifications.json."""
        cfg = _load_notif_config()
        if not cfg or not cfg.get("enabled", False):
            return
        ntype = cfg.get("type", "custom")
        if ntype == "update":
            title   = f"Update Available  v{cfg.get('update_version', '?')}"
            message = cfg.get("update_message", "A new version is available!")
            style   = "update"
        else:
            title   = cfg.get("custom_title", "Notification")
            message = cfg.get("custom_message", "")
            style   = cfg.get("style", "info")
        duration = int(cfg.get("show_duration", 8))
        if message:
            NotificationBanner(self, title, message, style=style, duration=duration)

    def select_tab(self, name):
        """Route sidebar click to show the corresponding frame with elite highlight"""
        for tab_name, data in self.tabs.items():
            if tab_name == name:
                data["frame"].pack(fill="both", expand=True)
                data["button"].configure(
                    fg_color=COLOR_PANEL2,
                    text_color=COLOR_ACCENT,
                    border_color=COLOR_ACCENT,
                    border_width=1
                )
            else:
                data["frame"].pack_forget()
                data["button"].configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_DIM,
                    border_color=COLOR_SIDEBAR,
                    border_width=0
                )

    def _setup_command_tab(self):
        parent = self.tab_cmd
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # 1. Elite Header
        header = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10, border_color=COLOR_BORDER, border_width=1)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="⚡ PROJECT OMNI",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color=COLOR_ACCENT
        ).grid(row=0, column=0, sticky="w", padx=20, pady=12)

        status_block = ctk.CTkFrame(header, fg_color="transparent")
        status_block.grid(row=0, column=1, sticky="e", padx=20)
        ctk.CTkLabel(status_block, text="●  AGI EDITION  v3.0", font=("Consolas", 11), text_color=COLOR_GOLD).pack(side="right", padx=5)
        self.label_title = ctk.CTkLabel(status_block, text="●  ONLINE", font=("Consolas", 11), text_color=COLOR_SUCCESS)
        self.label_title.pack(side="right", padx=5)

        # 2. Controls Dashboard
        self.dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.dashboard_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.dashboard_frame.grid_columnconfigure((0, 1), weight=1)

        # Left Panel: Core
        self.panel_core = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_PANEL, corner_radius=10, border_color=COLOR_BORDER, border_width=1)
        self.panel_core.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.panel_core, text="SYSTEM CONTROLS", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_DIM).pack(pady=5)
        
        self.btn_start = ctk.CTkButton(self.panel_core, corner_radius=8, text="▶  INITIALIZE BROWSER", command=self.start_browser, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#000000", font=("Consolas", 12, "bold"))
        self.btn_start.pack(fill="x", padx=10, pady=5)
        self.btn_close = ctk.CTkButton(self.panel_core, corner_radius=8, text="■  TERMINATE SESSION", command=self.close_browser, fg_color=COLOR_PANEL, border_color=COLOR_ERROR, border_width=1, hover_color="#1a0010", text_color=COLOR_ERROR, font=("Consolas", 12, "bold"))
        self.btn_close.pack(fill="x", padx=10, pady=5)

        # Right Panel: Memory (Teach By Doing)
        self.panel_rec = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_PANEL, corner_radius=10, border_color=COLOR_BORDER, border_width=1)
        self.panel_rec.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(self.panel_rec, text="MEMORY MODULE", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_DIM).pack(pady=5)
        
        row_macro_name = ctk.CTkFrame(self.panel_rec, fg_color="transparent")
        row_macro_name.pack(fill="x", padx=5, pady=(0, 0))
        self.combo_macro = ctk.CTkComboBox(
            row_macro_name, 
            values=self._get_macro_list(), 
            font=("Consolas", 11),
            fg_color=COLOR_PANEL2,
            border_color=COLOR_BORDER
        )
        self.combo_macro.pack(fill="x", padx=2)
        if not self.combo_macro.get() or self.combo_macro.get() == "":
            self.combo_macro.set("my_macro.json")
        
        row_mem = ctk.CTkFrame(self.panel_rec, fg_color="transparent")
        row_mem.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.btn_rec_start = ctk.CTkButton(row_mem, corner_radius=8, text="🔴 TRAIN", command=self.start_recording, fg_color="#7a0000", hover_color="#cc0000", text_color="white", font=("Consolas", 11, "bold"))
        self.btn_rec_start.pack(side="left", fill="x", expand=True, padx=2)
        
        self.btn_rec_save = ctk.CTkButton(row_mem, corner_radius=8, text="⤓ SAVE", command=self.save_recording, fg_color=COLOR_PANEL, border_color=COLOR_ACCENT, border_width=1, text_color=COLOR_ACCENT, hover_color=COLOR_PANEL2)
        self.btn_rec_save.pack(side="left", fill="x", expand=True, padx=2)
        
        self.btn_replay = ctk.CTkButton(row_mem, corner_radius=8, text="▶ REPLAY", command=self.replay_recording, fg_color=COLOR_PANEL, border_color=COLOR_SUCCESS, border_width=1, text_color=COLOR_SUCCESS, hover_color=COLOR_PANEL2)
        self.btn_replay.pack(side="left", fill="x", expand=True, padx=2)

        # 3. Log Console
        self.log_textbox = ctk.CTkTextbox(
            parent,
            fg_color=COLOR_LOG,
            text_color="#00ff99",
            font=("Consolas", 12),
            corner_radius=10,
            border_color=COLOR_BORDER,
            border_width=1,
            scrollbar_button_color=COLOR_PANEL2,
            scrollbar_button_hover_color=COLOR_ACCENT
        )
        self.log_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # 4. Mode Selection
        self.frame_mode = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_mode.grid(row=3, column=0, sticky="ew", padx=10)
        
        ctk.CTkLabel(self.frame_mode, text="ACTIVE PERSONA:", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_DIM).pack(side="left", padx=5)
        self.option_mode = ctk.CTkOptionMenu(
            self.frame_mode,
            values=["GENERAL", "SOCIAL_MEDIA", "CRYPTO_TRADER"],
            fg_color=COLOR_PANEL, button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT,
            dropdown_fg_color=COLOR_PANEL2, dropdown_text_color=COLOR_TEXT
        )
        self.option_mode.pack(side="left", padx=5)
        self.option_mode.set("GENERAL")

        # 5. Command Bar (Premium)
        self.cmd_frame = ctk.CTkFrame(
            parent, fg_color=COLOR_PANEL, height=72, corner_radius=10,
            border_color=COLOR_ACCENT, border_width=1
        )
        self.cmd_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.btn_voice = ctk.CTkButton(
            self.cmd_frame, corner_radius=8,
            text="🎤 VOX: OFF", command=self.toggle_listening,
            width=105, fg_color=COLOR_PANEL2, border_color=COLOR_BORDER, border_width=1,
            font=("Consolas", 11, "bold"), hover_color=COLOR_PANEL
        )
        self.btn_voice.pack(side="left", padx=15, pady=18)
        if not self.voice_available: self.btn_voice.configure(state="disabled", text="VOX N/A")

        self.autopilot_checkbox = ctk.CTkCheckBox(
            self.cmd_frame, text="🤖 AUTO-PILOT",
            font=("Consolas", 11, "bold"), text_color=COLOR_ACCENT,
            checkmark_color=COLOR_ACCENT, fg_color=COLOR_ACCENT, hover_color=COLOR_PANEL2
        )
        self.autopilot_checkbox.pack(side="left", padx=10, pady=18)
        
        self.godmode_checkbox = ctk.CTkCheckBox(
            self.cmd_frame, text="⚡ GOD MODE",
            font=("Consolas", 11, "bold"), text_color=COLOR_GOLD,
            checkmark_color=COLOR_GOLD, fg_color=COLOR_GOLD, hover_color=COLOR_PANEL2
        )
        self.godmode_checkbox.pack(side="left", padx=10, pady=18)
        
        self.vision_checkbox = ctk.CTkCheckBox(
            self.cmd_frame, text="👁️ VISION AI", command=self.toggle_vision,
            font=("Consolas", 11, "bold"), text_color="#00ffcc",
            checkmark_color="#00ffcc", fg_color="#00ffcc", hover_color=COLOR_PANEL2
        )
        self.vision_checkbox.pack(side="left", padx=10, pady=18)

        self.btn_stop_autopilot = ctk.CTkButton(self.cmd_frame, corner_radius=8, text="⏹ STOP", command=self.stop_autopilot,
            width=80, fg_color=COLOR_ERROR, hover_color="#770022",
            text_color="white", font=("Consolas", 11, "bold")
        )
        self.btn_stop_autopilot.pack(side="left", padx=5, pady=18)
        self.btn_stop_autopilot.pack_forget()

        self.entry_cmd = ctk.CTkEntry(
            self.cmd_frame,
            placeholder_text="❯  ENTER COMMAND SEQUENCE...",
            font=("Consolas", 13),
            fg_color=COLOR_LOG,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
            placeholder_text_color=COLOR_TEXT_DIM
        )
        self.entry_cmd.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=18)
        self.entry_cmd.bind("<Return>", lambda event: self.submit_text_command())

        self.btn_submit = ctk.CTkButton(self.cmd_frame, corner_radius=8, text="EXECUTE →", command=self.submit_text_command,
            width=110, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color="#000000", font=("Consolas", 12, "bold")
        )
        self.btn_submit.pack(side="right", padx=15, pady=18)

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

        self.btn_test_api = ctk.CTkButton(self.frame_api, corner_radius=8, text="TEST CONNECTION & SAVE", command=self.test_and_save_api, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
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

        self.radio_openrouter = ctk.CTkRadioButton(provider_frame, text="OpenRouter (Cloud)", variable=self.provider_var, value="openrouter", command=self.on_provider_change)
        self.radio_openrouter.pack(side="left", padx=10)
        
        # Ollama configuration
        self.frame_ollama = ctk.CTkFrame(self.frame_model, fg_color="transparent")
        self.frame_ollama.pack(anchor="w", padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(self.frame_ollama, text="Ollama Model:", font=("Consolas", 10)).pack(side="left", padx=5)
        self.ollama_model_entry = ctk.CTkEntry(self.frame_ollama, width=200, placeholder_text="llava:latest")
        self.ollama_model_entry.pack(side="left", padx=5)
        if self.cfg.get("ollama_model"):
            self.ollama_model_entry.insert(0, self.cfg.get("ollama_model"))
        
        self.btn_save_ollama = ctk.CTkButton(self.frame_ollama, corner_radius=8, text="SAVE & CONNECT", command=self.save_ollama_config, width=120, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
        self.btn_save_ollama.pack(side="left", padx=5)

        # OpenRouter configuration
        self.frame_openrouter = ctk.CTkFrame(self.frame_model, fg_color="transparent")
        self.frame_openrouter.pack(anchor="w", padx=20, pady=10, fill="x")

        ctk.CTkLabel(self.frame_openrouter, text="API Key:", font=("Consolas", 10)).pack(side="left", padx=5)
        self.openrouter_key_entry = ctk.CTkEntry(self.frame_openrouter, width=260, placeholder_text="sk-or-...", show="*")
        self.openrouter_key_entry.pack(side="left", padx=5)
        if self.cfg.get("openrouter_key"):
            self.openrouter_key_entry.insert(0, self.cfg.get("openrouter_key"))

        ctk.CTkLabel(self.frame_openrouter, text="Model:", font=("Consolas", 10)).pack(side="left", padx=(10, 5))
        self.openrouter_model_entry = ctk.CTkEntry(self.frame_openrouter, width=220, placeholder_text="google/gemini-2.0-flash-001")
        self.openrouter_model_entry.pack(side="left", padx=5)
        if self.cfg.get("openrouter_model"):
            self.openrouter_model_entry.insert(0, self.cfg.get("openrouter_model"))

        self.btn_save_openrouter = ctk.CTkButton(self.frame_openrouter, corner_radius=8, text="SAVE & CONNECT",
            command=self.save_openrouter_config, width=130,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black"
        )
        self.btn_save_openrouter.pack(side="left", padx=5)
        
        # Show/hide based on selection
        self.on_provider_change()
        
        # Current status
        self.lbl_model = ctk.CTkLabel(self.frame_model, text=f"CURRENT: {self.llm.get_provider_name().upper()}", font=("Consolas", 12))
        self.lbl_model.pack(anchor="w", padx=20, pady=(10, 20))

        # ─── Notifications Section ───────────────────────────────────
        frame_notif = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
        frame_notif.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_notif, text="📢  NOTIFICATIONS",
                     font=("Consolas", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(frame_notif,
                     text="Configure the startup popup shown to users when they launch the app.",
                     font=("Consolas", 10), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=20)

        # Load current config
        _nc = _load_notif_config() or {}

        # Enable / Disable toggle
        notif_row1 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row1.pack(anchor="w", padx=20, pady=(12, 4), fill="x")
        ctk.CTkLabel(notif_row1, text="Enable Startup Notification:",
                     font=("Consolas", 11)).pack(side="left")
        self.notif_enabled_var = ctk.BooleanVar(value=_nc.get("enabled", True))
        ctk.CTkSwitch(notif_row1, text="", variable=self.notif_enabled_var,
                      onvalue=True, offvalue=False,
                      progress_color=COLOR_ACCENT).pack(side="left", padx=12)

        # Notification type
        notif_row2 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row2.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row2, text="Type:", font=("Consolas", 11)).pack(side="left")
        self.notif_type_var = ctk.StringVar(value=_nc.get("type", "custom"))
        ctk.CTkSegmentedButton(notif_row2,
            values=["custom", "update"], variable=self.notif_type_var,
            font=("Consolas", 11), selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=12)

        # Style dropdown
        notif_row3 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row3.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row3, text="Style:", font=("Consolas", 11)).pack(side="left")
        self.notif_style_var = ctk.StringVar(value=_nc.get("style", "info"))
        ctk.CTkOptionMenu(notif_row3, values=["info", "update", "warning", "success"],
                          variable=self.notif_style_var,
                          font=("Consolas", 11), fg_color=COLOR_PANEL2,
                          button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=12)

        # Duration slider
        notif_row4 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row4.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row4, text="Show Duration (seconds):",
                     font=("Consolas", 11)).pack(side="left")
        self.notif_dur_var = ctk.IntVar(value=int(_nc.get("show_duration", 8)))
        self.notif_dur_lbl = ctk.CTkLabel(notif_row4,
            text=str(self.notif_dur_var.get()), font=("Consolas", 11), text_color=COLOR_ACCENT)
        self.notif_dur_lbl.pack(side="right", padx=8)
        ctk.CTkSlider(notif_row4, from_=3, to=30, number_of_steps=27,
                      variable=self.notif_dur_var,
                      button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER,
                      command=lambda v: self.notif_dur_lbl.configure(text=str(int(v)))).pack(side="left", padx=12, fill="x", expand=True)

        # Title field
        notif_row5 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row5.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row5, text="Title:", font=("Consolas", 11), width=80).pack(side="left")
        self.notif_title_entry = ctk.CTkEntry(notif_row5, placeholder_text="e.g. Welcome!",
                                              font=("Consolas", 11), width=320)
        self.notif_title_entry.pack(side="left", padx=10)
        if _nc.get("custom_title"):
            self.notif_title_entry.insert(0, _nc["custom_title"])

        # Message field
        notif_row6 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row6.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row6, text="Message:", font=("Consolas", 11), width=80).pack(side="left")
        self.notif_msg_entry = ctk.CTkEntry(notif_row6,
                                             placeholder_text="Your message to the user...",
                                             font=("Consolas", 11), width=320)
        self.notif_msg_entry.pack(side="left", padx=10)
        if _nc.get("custom_message"):
            self.notif_msg_entry.insert(0, _nc["custom_message"])

        # Update version & message (for update type)
        notif_row7 = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_row7.pack(anchor="w", padx=20, pady=4, fill="x")
        ctk.CTkLabel(notif_row7, text="Update Ver:", font=("Consolas", 11), width=80).pack(side="left")
        self.notif_ver_entry = ctk.CTkEntry(notif_row7, placeholder_text="3.1",
                                             font=("Consolas", 11), width=80)
        self.notif_ver_entry.pack(side="left", padx=10)
        if _nc.get("update_version"):
            self.notif_ver_entry.insert(0, _nc["update_version"])

        ctk.CTkLabel(notif_row7, text="Update Msg:", font=("Consolas", 11)).pack(side="left", padx=(16,0))
        self.notif_update_msg_entry = ctk.CTkEntry(notif_row7, placeholder_text="New version available!",
                                                    font=("Consolas", 11), width=220)
        self.notif_update_msg_entry.pack(side="left", padx=10)
        if _nc.get("update_message"):
            self.notif_update_msg_entry.insert(0, _nc["update_message"])

        # Save & preview buttons
        notif_btn_row = ctk.CTkFrame(frame_notif, fg_color="transparent")
        notif_btn_row.pack(anchor="w", padx=20, pady=(12, 20))

        ctk.CTkButton(notif_btn_row, text="💾  SAVE NOTIFICATION",
                      font=("Consolas", 11, "bold"), corner_radius=8,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black",
                      command=self._save_notification_config).pack(side="left", padx=(0, 10))

        ctk.CTkButton(notif_btn_row, text="▶  PREVIEW",
                      font=("Consolas", 11, "bold"), corner_radius=8,
                      fg_color=COLOR_PANEL2, hover_color="#2a2a50",
                      command=self._preview_notification).pack(side="left")

        self.lbl_notif_status = ctk.CTkLabel(frame_notif, text="",
                                              font=("Consolas", 11), text_color=COLOR_SUCCESS)
        self.lbl_notif_status.pack(anchor="w", padx=20, pady=(0, 10))


    def _setup_chat_tab(self):
        parent = self.tab_chat
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="N E U R A L   C H A T", font=("Consolas", 18, "bold"), text_color=COLOR_ACCENT).grid(row=0, column=0, pady=20)

        self.chat_history_textbox = ctk.CTkTextbox(parent, font=("Consolas", 13), fg_color=COLOR_LOG, text_color="white", corner_radius=10)
        self.chat_history_textbox.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.chat_history_textbox.insert("end", ">> NEURAL CHAT INITIALIZED...\n\n")
        self.chat_history_textbox.configure(state="disabled")

        frame_input = ctk.CTkFrame(parent, fg_color="transparent")
        frame_input.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        frame_input.grid_columnconfigure(0, weight=1)

        self.entry_chat = ctk.CTkEntry(frame_input, placeholder_text="Ask me anything without executing commands...", font=("Consolas", 14), height=40)
        self.entry_chat.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_chat.bind("<Return>", lambda e: self.submit_chat())

        self.btn_chat_send = ctk.CTkButton(frame_input, corner_radius=8, text="SEND", command=self.submit_chat, width=80, height=40, font=("Consolas", 12, "bold"), fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black")
        self.btn_chat_send.grid(row=0, column=1)

    def submit_chat(self):
        text = self.entry_chat.get().strip()
        if not text: return
        self.entry_chat.delete(0, 'end')
        
        self.append_chat(f"USER: {text}\n")
        self.append_chat(f"SYSTEM: Typing...\n")
        
        self.btn_chat_send.configure(state="disabled")
        threading.Thread(target=self._chat_worker, args=(text,), daemon=True).start()

    def append_chat(self, text):
        self.chat_history_textbox.configure(state="normal")
        content = self.chat_history_textbox.get("1.0", "end-1c")
        if content.endswith("SYSTEM: Typing..."):
            self.chat_history_textbox.delete("end-18c", "end")
            
        self.chat_history_textbox.insert("end", text)
        self.chat_history_textbox.see("end")
        self.chat_history_textbox.configure(state="disabled")

    def _chat_worker(self, text):
        if not self.use_ai:
            response = "ERROR: AI Model not configured. Please set up API key in SYSTEM SETTINGS."
        else:
            try:
                # pass the last 4000 characters to provide context implicitly
                context = self.chat_history_textbox.get("1.0", "end-1c")
                context = context[-4000:] if len(context) > 4000 else context
                
                full_prompt = (
                    "You are Neural Omni, an advanced desktop AI Assistant.\n"
                    f"Conversation so far:\n{context}\n"
                    "Reply naturally to the USER. Do not use JSON. Just chat."
                )
                response = self.llm.generate_text(full_prompt)
            except Exception as e:
                response = f"ERROR: {e}"
                
        self.after(0, lambda: self.append_chat(f"AI: {response}\n\n"))
        self.after(0, lambda: self.btn_chat_send.configure(state="normal"))


    def _setup_scheduler_tab(self):
        parent = self.tab_scheduler
        parent.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(parent, text="TASK SCHEDULER", font=("Consolas", 18, "bold"), text_color="gray").pack(pady=20)
        
        # Add Task Frame
        frame_add = ctk.CTkFrame(parent, fg_color=COLOR_PANEL)
        frame_add.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame_add, text="NEW TASK", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.entry_sched_time = ctk.CTkEntry(frame_add, placeholder_text="HH:MM (24h)", width=100)
        self.entry_sched_time.pack(side="left", padx=10, pady=10)
        
        self.option_sched_type = ctk.CTkOptionMenu(frame_add, values=["REPLAY", "AUTO-PILOT"], width=120)
        self.option_sched_type.pack(side="left", padx=10, pady=10)
        
        self.entry_sched_target = ctk.CTkEntry(frame_add, placeholder_text="Filename or Goal", width=200)
        self.entry_sched_target.pack(side="left", padx=10, pady=10)
        
        btn_add = ctk.CTkButton(frame_add, corner_radius=8, text="SCHEDULE", command=self.add_scheduled_task, fg_color=COLOR_ACCENT, text_color="black")
        btn_add.pack(side="left", padx=10, pady=10)
        
        # Task List
        self.sched_list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent", label_text="ACTIVE SCHEDULES")
        self.sched_list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def _setup_accounts_tab(self):
        parent = self.tab_accounts
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Left: List
        self.frame_acc_list = ctk.CTkScrollableFrame(parent, width=250, label_text="SAVED ACCOUNTS")
        self.frame_acc_list.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Right: Editor
        self.frame_acc_edit = ctk.CTkFrame(parent, fg_color=COLOR_PANEL)
        self.frame_acc_edit.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_acc_edit, text="ADD / EDIT ACCOUNT", font=("Consolas", 16, "bold")).pack(pady=20)
        
        self.option_platform = ctk.CTkOptionMenu(self.frame_acc_edit, values=list(PLATFORM_MAP.keys()))
        self.option_platform.pack(pady=10)
        
        self.entry_acc_user = ctk.CTkEntry(self.frame_acc_edit, placeholder_text="Username / Email", width=250)
        self.entry_acc_user.pack(pady=10)
        
        self.entry_acc_pass = ctk.CTkEntry(self.frame_acc_edit, placeholder_text="Password", show="*", width=250)
        self.entry_acc_pass.pack(pady=10)
        
        btn_save_acc = ctk.CTkButton(self.frame_acc_edit, corner_radius=8, text="SAVE ENCRYPTED", command=self.save_account, fg_color=COLOR_SUCCESS, text_color="black")
        btn_save_acc.pack(pady=20)
        
        self.refresh_account_list()

    def refresh_account_list(self):
        # Clear existing
        for widget in self.frame_acc_list.winfo_children():
            widget.destroy()
            
        accounts = self.cfg.get_all_accounts()
        for platform in accounts:
            f = ctk.CTkFrame(self.frame_acc_list, fg_color=COLOR_BG)
            f.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(f, text=platform, font=("Consolas", 12, "bold")).pack(side="left", padx=10)
            
            btn_login = ctk.CTkButton(f, corner_radius=8, text="INSTANT SIGN IN", width=100, 
                                      command=lambda p=platform: self.instant_login(p),
                                      fg_color=COLOR_ACCENT, text_color="black")
            btn_login.pack(side="right", padx=5, pady=5)

    def save_account(self):
        platform = self.option_platform.get()
        user = self.entry_acc_user.get()
        pwd = self.entry_acc_pass.get()
        
        if not user or not pwd:
            return
            
        self.cfg.save_account(platform, user, pwd)
        self.entry_acc_user.delete(0, "end")
        self.entry_acc_pass.delete(0, "end")
        self.refresh_account_list()
        self.tts.speak(f"{platform} account saved")

    def instant_login(self, platform):
        self.log(f"INITIATING INSTANT LOGIN: {platform}")
        self.tts.speak(f"Signing in to {platform}")
        
        creds = self.cfg.get_account(platform)
        if not creds: return
        
        self.run_async(self._login_task(platform, creds["username"], creds["password"]))

    async def _login_task(self, platform, user, pwd):
        try:
            await perform_login(self.agent, platform, user, pwd)
            self.update_log_from_thread(f"LOGIN SUBMITTED FOR {platform}")
            self.tts.speak("Login submitted")
        except Exception as e:
            self.update_log_from_thread(f"LOGIN ERROR: {e}")
            self.tts.speak("Login failed")



    def _setup_social_tab(self):
        parent = self.tab_social
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Left Panel: Research & Config
        frame_left = ctk.CTkFrame(parent, width=350, fg_color=COLOR_PANEL)
        frame_left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame_left.grid_propagate(False)

        ctk.CTkLabel(frame_left, text="SOCIAL MEDIA PRO", font=("Consolas", 16, "bold"), text_color=COLOR_ACCENT).pack(pady=20)

        # Topic Input
        ctk.CTkLabel(frame_left, text="TOPIC / TREND", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_social_topic = ctk.CTkEntry(frame_left, placeholder_text="e.g. AI Agents")
        self.entry_social_topic.pack(fill="x", padx=10, pady=5)

        # Research Button
        self.btn_research = ctk.CTkButton(frame_left, corner_radius=8, text="🔍 RESEARCH TRENDS", command=self.research_trends, fg_color=COLOR_ACCENT, text_color="black")
        self.btn_research.pack(fill="x", padx=10, pady=10)

        # Trends Display
        ctk.CTkLabel(frame_left, text="TREND INSIGHTS", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.txt_trends = ctk.CTkTextbox(frame_left, height=150, font=("Consolas", 11))
        self.txt_trends.pack(fill="x", padx=10, pady=5)

        # Vibe Selector
        ctk.CTkLabel(frame_left, text="CONTENT VIBE", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.option_vibe = ctk.CTkOptionMenu(frame_left, values=["Professional", "Shitposting", "Storyteller", "Sales"])
        self.option_vibe.pack(fill="x", padx=10, pady=5)

        # Generate Button
        self.btn_gen_social = ctk.CTkButton(frame_left, corner_radius=8, text="✨ GENERATE POST", command=self.generate_social_post, fg_color=COLOR_SUCCESS, text_color="black")
        self.btn_gen_social.pack(fill="x", padx=10, pady=20)

        # Right Panel: Preview & Post
        frame_right = ctk.CTkFrame(parent, fg_color="transparent")
        frame_right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Preview
        ctk.CTkLabel(frame_right, text="CONTENT PREVIEW", font=("Consolas", 14, "bold")).pack(anchor="w", pady=(10, 5))
        self.txt_social_preview = ctk.CTkTextbox(frame_right, height=150, font=("Consolas", 12))
        self.txt_social_preview.pack(fill="x", pady=5)
        
        self.lbl_social_image = ctk.CTkLabel(frame_right, text="[IMAGE PREVIEW]", height=250, fg_color="#222")
        self.lbl_social_image.pack(fill="both", expand=True, pady=10)
        
        # Posting Controls
        frame_post = ctk.CTkFrame(frame_right, fg_color=COLOR_PANEL)
        frame_post.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame_post, text="PUBLISH TO", font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        
        self.btn_post_twitter = ctk.CTkButton(frame_post, corner_radius=8, text="TWITTER / X", command=lambda: self.post_social("twitter"), width=120, fg_color="#1DA1F2")
        self.btn_post_twitter.pack(side="left", padx=5, pady=10)
        
        self.btn_post_linkedin = ctk.CTkButton(frame_post, corner_radius=8, text="LINKEDIN", command=lambda: self.post_social("linkedin"), width=120, fg_color="#0077b5")
        self.btn_post_linkedin.pack(side="left", padx=5, pady=10)

        self.lbl_social_status = ctk.CTkLabel(frame_right, text="", font=("Consolas", 11))
        self.lbl_social_status.pack(pady=5)

        self.current_social_content = None

        # --- AUTO COMMENT BOT SECTION ---
        # Placed at the bottom of the right panel, spanning full width
        frame_comment = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10, border_color="#1e1e38", border_width=1)
        frame_comment.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            frame_comment,
            text="⚡  AUTO COMMENT BOT",
            font=("Consolas", 14, "bold"),
            text_color=COLOR_ACCENT
        ).pack(anchor="w", padx=15, pady=(12, 4))

        # Row 1: URL + Platform
        row1 = ctk.CTkFrame(frame_comment, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=4)
        row1.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(row1, text="DIRECT URL (Single):", font=("Consolas", 11), text_color="gray").grid(row=0, column=0, sticky="w")
        self.entry_comment_url = ctk.CTkEntry(
            row1,
            placeholder_text="Paste a specific tweet/post URL for a single comment",
            font=("Consolas", 12),
            fg_color="#000",
            border_color="#1e1e38",
            text_color="white"
        )
        self.entry_comment_url.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 4))

        ctk.CTkLabel(row1, text="PLATFORM:", font=("Consolas", 11), text_color="gray").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.option_comment_platform = ctk.CTkOptionMenu(
            row1,
            values=["Twitter / X", "Facebook"],
            width=130,
            fg_color=COLOR_PANEL,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
            text_color="white"
        )
        self.option_comment_platform.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 4))

        # Row 2: Advanced Bot Config
        row2 = ctk.CTkFrame(frame_comment, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(row2, text="OR AUTO-BOT KEYWORDS (Comma separated):", font=("Consolas", 11), text_color="cyan").pack(anchor="w")
        self.entry_bot_keywords = ctk.CTkEntry(
            row2,
            placeholder_text="AI, Crypto, Python, Tech News",
            font=("Consolas", 12),
            fg_color="#111",
            border_color="#1e1e38",
            text_color="white"
        )
        self.entry_bot_keywords.pack(fill="x", pady=(0, 8))

        # Row 2b: Limits and Delays
        row2b = ctk.CTkFrame(row2, fg_color="transparent")
        row2b.pack(fill="x")
        
        ctk.CTkLabel(row2b, text="MAX REPLIES:", font=("Consolas", 10)).pack(side="left", padx=(0, 5))
        self.entry_bot_max = ctk.CTkEntry(row2b, width=50, placeholder_text="5")
        self.entry_bot_max.insert(0, "5")
        self.entry_bot_max.pack(side="left", padx=5)

        ctk.CTkLabel(row2b, text="DELAY BETWEEN REPLIES (sec):", font=("Consolas", 10), text_color="#aaa").pack(side="left", padx=(15, 5))
        self.entry_bot_delay_min = ctk.CTkEntry(row2b, width=50, placeholder_text="8")
        self.entry_bot_delay_min.insert(0, "8")
        self.entry_bot_delay_min.pack(side="left", padx=5)
        ctk.CTkLabel(row2b, text="–", text_color="gray").pack(side="left")
        self.entry_bot_delay_max = ctk.CTkEntry(row2b, width=50, placeholder_text="20")
        self.entry_bot_delay_max.insert(0, "20")
        self.entry_bot_delay_max.pack(side="left", padx=5)
        ctk.CTkLabel(row2b, text="(↑ increase to avoid rate limits)", font=("Consolas", 9), text_color="gray").pack(side="left", padx=(5, 0))

        # Row 3: Prompt
        row3 = ctk.CTkFrame(frame_comment, fg_color="transparent")
        row3.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(row3, text="REPLY STYLE / CONTEXT (AI Intent):", font=("Consolas", 11), text_color="gray").pack(anchor="w")
        self.entry_comment_prompt = ctk.CTkEntry(
            row3,
            placeholder_text="e.g. Be funny and edgy",
            font=("Consolas", 12),
            fg_color="#000",
            border_color="#1e1e38",
            text_color="white"
        )
        self.entry_comment_prompt.pack(fill="x", pady=4)

        # Row 2c: Daily Limit
        row2c = ctk.CTkFrame(row2, fg_color="transparent")
        row2c.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(row2c, text="DAILY LIMIT:", font=("Consolas", 10)).pack(side="left", padx=(0, 5))
        self.entry_bot_daily_limit = ctk.CTkEntry(row2c, width=55, placeholder_text="20")
        self.entry_bot_daily_limit.insert(0, "20")
        self.entry_bot_daily_limit.pack(side="left", padx=5)
        self.lbl_bot_replies = ctk.CTkLabel(row2c, text="Replies today: 0", font=("Consolas", 11), text_color="gray")
        self.lbl_bot_replies.pack(side="left", padx=(20, 0))

        # Row 4: Execute / Stop buttons + status
        row4 = ctk.CTkFrame(frame_comment, fg_color="transparent")
        row4.pack(fill="x", padx=15, pady=(4, 6))

        self.btn_auto_comment = ctk.CTkButton(row4, corner_radius=8,
            text="🚀 START AUTO-COMMENT BOT",
            command=self.execute_auto_comment,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="black",
            font=("Consolas", 12, "bold")
        )
        self.btn_auto_comment.pack(side="left", padx=(0, 10))

        self.btn_stop_bot = ctk.CTkButton(row4, corner_radius=8,
            text="⛔ STOP",
            command=self._stop_bot_action,
            fg_color="#7a0000",
            hover_color="#cc0000",
            text_color="white",
            font=("Consolas", 11, "bold"),
            width=80,
            state="disabled"
        )
        self.btn_stop_bot.pack(side="left", padx=(0, 15))

        self.lbl_comment_status = ctk.CTkLabel(row4, text="READY", font=("Consolas", 11), text_color="gray")
        self.lbl_comment_status.pack(side="left")

        # Row 5: Activity Log
        ctk.CTkLabel(frame_comment, text="BOT ACTIVITY LOG", font=("Consolas", 10), text_color="gray").pack(anchor="w", padx=15)
        self.txt_bot_log = ctk.CTkTextbox(
            frame_comment,
            height=100,
            font=("Consolas", 10),
            fg_color="#050505",
            text_color="#00ff99",
            state="disabled"
        )
        self.txt_bot_log.pack(fill="x", padx=15, pady=(0, 12))

    def research_trends(self):
        topic = self.entry_social_topic.get()
        if not topic: return
        
        self.lbl_social_status.configure(text="RESEARCHING TRENDS...", text_color="yellow")
        self.tts.speak("Researching trends")
        
        threading.Thread(target=self._social_research_thread, args=(topic,)).start()

    def _social_research_thread(self, topic):
        trends = asyncio.run_coroutine_threadsafe(self.social_manager.research_trends(topic), self.loop).result()
        
        self.after(0, lambda: self.txt_trends.delete("0.0", "end"))
        self.after(0, lambda: self.txt_trends.insert("0.0", trends))
        self.after(0, lambda: self.lbl_social_status.configure(text="RESEARCH COMPLETE", text_color=COLOR_SUCCESS))
        self.tts.speak("Research complete")

    def generate_social_post(self):
        topic = self.entry_social_topic.get()
        trends = self.txt_trends.get("0.0", "end").strip()
        vibe = self.option_vibe.get()
        
        if not topic: return
        
        self.lbl_social_status.configure(text="GENERATING CONTENT...", text_color="yellow")
        self.tts.speak("Generating post")
        
        threading.Thread(target=self._gen_social_thread, args=(topic, trends, vibe)).start()

    def _gen_social_thread(self, topic, trends, vibe):
        content = asyncio.run_coroutine_threadsafe(self.social_manager.generate_content_plan(topic, trends, vibe), self.loop).result()
        self.current_social_content = content
        
        # Update UI
        self.after(0, lambda: self.txt_social_preview.delete("0.0", "end"))
        self.after(0, lambda: self.txt_social_preview.insert("0.0", content["text"]))
        
        if content["image"]:
            preview_img = ctk.CTkImage(light_image=content["image"], dark_image=content["image"], size=(400, 250))
            self.after(0, lambda: self.lbl_social_image.configure(image=preview_img, text=""))
            
        self.after(0, lambda: self.lbl_social_status.configure(text="GENERATION COMPLETE", text_color=COLOR_SUCCESS))
        self.tts.speak("Post generated")

    def post_social(self, platform):
        if not self.current_social_content:
            self.lbl_social_status.configure(text="ERROR: NO CONTENT GENERATED", text_color=COLOR_ERROR)
            return
            
        self.lbl_social_status.configure(text=f"POSTING TO {platform.upper()}...", text_color="yellow")
        self.tts.speak(f"Posting to {platform}")
        
        threading.Thread(target=self._post_social_thread, args=(platform,)).start()

    def _post_social_thread(self, platform):
        if platform == "twitter":
            result = asyncio.run_coroutine_threadsafe(self.social_manager.post_to_twitter(self.current_social_content), self.loop).result()
        elif platform == "linkedin":
            result = asyncio.run_coroutine_threadsafe(self.social_manager.post_to_linkedin(self.current_social_content), self.loop).result()
        else:
            result = "Unknown platform"
            
        self.after(0, lambda: self.lbl_social_status.configure(text=result, text_color=COLOR_ACCENT))
        self.tts.speak("Posting task finished")

    # --- Auto Comment Bot ---
    def _stop_bot_action(self):
        """Signal the bot loop to stop."""
        self.social_manager.stop_bot()
        self.lbl_comment_status.configure(text="STOP REQUESTED...", text_color="orange")
        self.btn_stop_bot.configure(state="disabled")

    def _bot_log(self, message: str):
        """Append a message to the bot activity log textbox."""
        def _append():
            self.txt_bot_log.configure(state="normal")
            self.txt_bot_log.insert("end", f"{message}\n")
            self.txt_bot_log.see("end")
            self.txt_bot_log.configure(state="disabled")
        self.after(0, _append)

    def execute_auto_comment(self):
        post_url = self.entry_comment_url.get().strip()
        bot_keywords = self.entry_bot_keywords.get().strip()
        prompt = self.entry_comment_prompt.get().strip()
        platform = self.option_comment_platform.get()
        vibe = self.option_vibe.get()

        if bot_keywords:
            if "Twitter" not in platform:
                self.lbl_comment_status.configure(text="ERROR: BOT ONLY FOR TWITTER", text_color=COLOR_ERROR)
                return
            
            try:
                keywords = [k.strip() for k in bot_keywords.split(",") if k.strip()]
                max_replies = int(self.entry_bot_max.get() or 5)
                delay_range = (int(self.entry_bot_delay_min.get() or 8), int(self.entry_bot_delay_max.get() or 20))
            except ValueError:
                self.lbl_comment_status.configure(text="ERROR: INVALID NUMBERS", text_color=COLOR_ERROR)
                return
            
            self.lbl_comment_status.configure(text="STARTING ADVANCED BOT...", text_color="yellow")
            self.btn_auto_comment.configure(state="disabled")
            self.tts.speak("Starting advanced auto comment bot")
            
            threading.Thread(
                target=self._advanced_bot_thread,
                args=(keywords, max_replies, delay_range, prompt),
                daemon=True
            ).start()
            
        elif post_url:
            self.lbl_comment_status.configure(text="GENERATING COMMENT...", text_color="yellow")
            self.btn_auto_comment.configure(state="disabled")
            self.tts.speak("Generating and posting comment")
            threading.Thread(
                target=self._auto_comment_thread,
                args=(post_url, prompt, platform, vibe),
                daemon=True
            ).start()
        else:
            self.lbl_comment_status.configure(text="ERROR: ENTER URL OR KEYWORDS.", text_color=COLOR_ERROR)

    def _advanced_bot_thread(self, keywords, max_replies, delay_range, prompt_context, daily_limit=20):
        def update_status(msg):
            self.after(0, lambda m=msg: self.lbl_comment_status.configure(text=m[:60].upper()))
            self._bot_log(msg)
            # Update daily counter label
            count = self.social_manager.get_daily_reply_count()
            self.after(0, lambda c=count: self.lbl_bot_replies.configure(text=f"Replies today: {c}"))

        try:
            result = asyncio.run_coroutine_threadsafe(
                self.social_manager.run_advanced_twitter_bot(
                    keywords=keywords,
                    max_replies=max_replies,
                    delay_range=delay_range,
                    mode="AI",
                    prompt_context=prompt_context,
                    progress_callback=update_status,
                    daily_limit=daily_limit
                ),
                self.loop
            ).result(timeout=7200)

            self.after(0, lambda r=result: self.lbl_comment_status.configure(text=r[:60].upper(), text_color=COLOR_SUCCESS))
            self._bot_log(f"--- DONE: {result} ---")
            self.tts.speak("Advanced bot finished")
        except Exception as e:
            self.after(0, lambda err=e: self.lbl_comment_status.configure(
                text=f"BOT ERROR: {str(err)[:40]}".upper(), text_color=COLOR_ERROR
            ))
            self._bot_log(f"ERROR: {e}")
        finally:
            self.after(0, lambda: self.btn_auto_comment.configure(state="normal"))
            self.after(0, lambda: self.btn_stop_bot.configure(state="disabled"))

    def _auto_comment_thread(self, post_url, prompt, platform, vibe):
        try:
            # Step 1: Generate comment text using LLM
            full_prompt = (
                f"You are writing a social media comment. Vibe: {vibe}.\n"
                f"Task: {prompt}\n\n"
                f"Write a single natural comment (no hashtags, no quotes, no intro). "
                f"Be concise and engaging. Max 2 sentences."
            )
            comment_text = self.content_gen.generate_text(full_prompt, platform=platform, vibe=vibe)

            self.after(0, lambda: self.lbl_comment_status.configure(
                text=f"POSTING: \"{comment_text[:60]}...\"", text_color="yellow"
            ))

            # Step 2: Post the comment via browser
            if "facebook" in platform.lower():
                result = asyncio.run_coroutine_threadsafe(
                    self.social_manager.auto_comment_facebook(post_url, comment_text),
                    self.loop
                ).result(timeout=60)
            else:  # Twitter / X
                result = asyncio.run_coroutine_threadsafe(
                    self.social_manager.auto_comment_twitter(post_url, comment_text),
                    self.loop
                ).result(timeout=60)

            color = COLOR_SUCCESS if result.startswith("✅") else COLOR_ERROR
            self.after(0, lambda: self.lbl_comment_status.configure(text=result, text_color=color))
            self.tts.speak("Comment task finished")
        except Exception as e:
            self.after(0, lambda err=e: self.lbl_comment_status.configure(
                text=f"ERROR: {err}", text_color=COLOR_ERROR
            ))
            self.tts.speak("Comment failed")
        finally:
            self.after(0, lambda: self.btn_auto_comment.configure(state="normal"))

    # =====================================================================
    # COMMUNICATIONS TAB — V3: Email, Calendar, Phone, Wake Word
    # =====================================================================
    def _setup_communications_tab(self):
        parent = self.tab_comms
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(parent, text="⚡ COMMUNICATIONS HUB", font=("Consolas", 18, "bold"), text_color="#00f0ff").pack(pady=(15, 5))
        ctk.CTkLabel(parent, text="Email · Calendar · Phone · Wake Word", font=("Consolas", 11), text_color="gray").pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # ── EMAIL PANEL ────────────────────────────────────────────────
        email_frame = ctk.CTkFrame(scroll, fg_color=COLOR_PANEL, corner_radius=10, border_color="#00f0ff", border_width=1)
        email_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(email_frame, text="📧 GMAIL INTEGRATION", font=("Consolas", 13, "bold"), text_color="#00f0ff").pack(anchor="w", padx=15, pady=(12, 5))

        row_email_cfg = ctk.CTkFrame(email_frame, fg_color="transparent")
        row_email_cfg.pack(fill="x", padx=15, pady=2)
        self.entry_email_addr = ctk.CTkEntry(row_email_cfg, placeholder_text="your@gmail.com", font=("Consolas", 12), width=220)
        self.entry_email_addr.pack(side="left", padx=(0, 10))
        self.entry_email_pw = ctk.CTkEntry(row_email_cfg, placeholder_text="Gmail App Password", font=("Consolas", 12), show="*", width=200)
        self.entry_email_pw.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_email_cfg, corner_radius=8, text="CONNECT", font=("Consolas", 12, "bold"), fg_color="#00f0ff", text_color="black", hover_color="#00b8cc", width=100, command=self._email_connect).pack(side="left")

        self.lbl_email_status = ctk.CTkLabel(email_frame, text="Not connected", font=("Consolas", 11), text_color="gray")
        self.lbl_email_status.pack(anchor="w", padx=15, pady=2)

        row_email_btns = ctk.CTkFrame(email_frame, fg_color="transparent")
        row_email_btns.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(row_email_btns, corner_radius=8, text="📥 READ INBOX", font=("Consolas", 12, "bold"), fg_color=COLOR_PANEL, border_color="#00f0ff", border_width=1, text_color="#00f0ff", command=self._email_read_inbox).pack(side="left", padx=(0, 10))

        # Compose panel
        ctk.CTkLabel(email_frame, text="COMPOSE:", font=("Consolas", 11), text_color="gray").pack(anchor="w", padx=15)
        self.entry_email_to = ctk.CTkEntry(email_frame, placeholder_text="To: recipient@email.com", font=("Consolas", 12))
        self.entry_email_to.pack(fill="x", padx=15, pady=2)
        self.entry_email_subj = ctk.CTkEntry(email_frame, placeholder_text="Subject", font=("Consolas", 12))
        self.entry_email_subj.pack(fill="x", padx=15, pady=2)
        self.txt_email_body = ctk.CTkTextbox(email_frame, height=80, font=("Consolas", 12))
        self.txt_email_body.pack(fill="x", padx=15, pady=2)
        ctk.CTkButton(email_frame, corner_radius=8, text="📤 SEND EMAIL", font=("Consolas", 12, "bold"), fg_color="#00cc55", text_color="black", hover_color="#00993f", command=self._email_send).pack(anchor="w", padx=15, pady=(5, 12))

        self.txt_email_output = ctk.CTkTextbox(email_frame, height=160, font=("Consolas", 11), fg_color=COLOR_LOG)
        self.txt_email_output.pack(fill="x", padx=15, pady=(0, 12))

        # ── CALENDAR PANEL ─────────────────────────────────────────────
        cal_frame = ctk.CTkFrame(scroll, fg_color=COLOR_PANEL, corner_radius=10, border_color="#7b2fff", border_width=1)
        cal_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(cal_frame, text="📅 GOOGLE CALENDAR", font=("Consolas", 13, "bold"), text_color="#7b2fff").pack(anchor="w", padx=15, pady=(12, 5))

        row_cal = ctk.CTkFrame(cal_frame, fg_color="transparent")
        row_cal.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(row_cal, corner_radius=8, text="🔗 CONNECT GOOGLE", font=("Consolas", 12, "bold"), fg_color="#7b2fff", text_color="white", width=180, command=self._calendar_connect).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_cal, corner_radius=8, text="📋 VIEW UPCOMING", font=("Consolas", 12, "bold"), fg_color=COLOR_PANEL, border_color="#7b2fff", border_width=1, text_color="#7b2fff", command=self._calendar_view).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(cal_frame, text="CREATE EVENT:", font=("Consolas", 11), text_color="gray").pack(anchor="w", padx=15, pady=(5, 0))
        row_new_event = ctk.CTkFrame(cal_frame, fg_color="transparent")
        row_new_event.pack(fill="x", padx=15, pady=2)
        self.entry_cal_title = ctk.CTkEntry(row_new_event, placeholder_text="Event Title", font=("Consolas", 12), width=200)
        self.entry_cal_title.pack(side="left", padx=(0, 5))
        self.entry_cal_date = ctk.CTkEntry(row_new_event, placeholder_text="YYYY-MM-DD", font=("Consolas", 12), width=130)
        self.entry_cal_date.pack(side="left", padx=(0, 5))
        self.entry_cal_time = ctk.CTkEntry(row_new_event, placeholder_text="HH:MM", font=("Consolas", 12), width=80)
        self.entry_cal_time.pack(side="left", padx=(0, 5))
        ctk.CTkButton(row_new_event, corner_radius=8, text="ADD", font=("Consolas", 11, "bold"), fg_color="#7b2fff", text_color="white", width=60, command=self._calendar_create).pack(side="left")

        self.txt_cal_output = ctk.CTkTextbox(cal_frame, height=120, font=("Consolas", 11), fg_color=COLOR_LOG)
        self.txt_cal_output.pack(fill="x", padx=15, pady=(5, 12))

        # ── PHONE / SMS PANEL ─────────────────────────────────────────
        phone_frame = ctk.CTkFrame(scroll, fg_color=COLOR_PANEL, corner_radius=10, border_color="#ff6600", border_width=1)
        phone_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(phone_frame, text="📞 AI PHONE & SMS (TWILIO)", font=("Consolas", 13, "bold"), text_color="#ff6600").pack(anchor="w", padx=15, pady=(12, 5))
        ctk.CTkLabel(phone_frame, text="Requires a Twilio account → twilio.com (free trial gives $15 credit)", font=("Consolas", 10), text_color="gray").pack(anchor="w", padx=15)

        row_twilio_cfg = ctk.CTkFrame(phone_frame, fg_color="transparent")
        row_twilio_cfg.pack(fill="x", padx=15, pady=5)
        self.entry_twilio_sid = ctk.CTkEntry(row_twilio_cfg, placeholder_text="Account SID", font=("Consolas", 12), width=200)
        self.entry_twilio_sid.pack(side="left", padx=(0, 5))
        self.entry_twilio_token = ctk.CTkEntry(row_twilio_cfg, placeholder_text="Auth Token", font=("Consolas", 12), show="*", width=180)
        self.entry_twilio_token.pack(side="left", padx=(0, 5))
        self.entry_twilio_from = ctk.CTkEntry(row_twilio_cfg, placeholder_text="+1XXXXXXXXXX", font=("Consolas", 12), width=130)
        self.entry_twilio_from.pack(side="left", padx=(0, 5))
        ctk.CTkButton(row_twilio_cfg, corner_radius=8, text="CONNECT", font=("Consolas", 11, "bold"), fg_color="#ff6600", text_color="black", width=90, command=self._phone_connect).pack(side="left")

        self.lbl_phone_status = ctk.CTkLabel(phone_frame, text="Not connected", font=("Consolas", 11), text_color="gray")
        self.lbl_phone_status.pack(anchor="w", padx=15)

        self.entry_phone_to = ctk.CTkEntry(phone_frame, placeholder_text="To Number: +923001234567", font=("Consolas", 12))
        self.entry_phone_to.pack(fill="x", padx=15, pady=5)
        self.entry_phone_msg = ctk.CTkEntry(phone_frame, placeholder_text="Message to speak / send as SMS", font=("Consolas", 12))
        self.entry_phone_msg.pack(fill="x", padx=15, pady=2)

        row_phone_btns = ctk.CTkFrame(phone_frame, fg_color="transparent")
        row_phone_btns.pack(fill="x", padx=15, pady=(5, 12))
        ctk.CTkButton(row_phone_btns, corner_radius=8, text="📞 CALL", font=("Consolas", 12, "bold"), fg_color="#ff6600", text_color="black", width=100, command=self._phone_call).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_phone_btns, corner_radius=8, text="💬 SEND SMS", font=("Consolas", 12, "bold"), fg_color=COLOR_PANEL, border_color="#ff6600", border_width=1, text_color="#ff6600", width=110, command=self._phone_sms).pack(side="left")

        # ── WAKE WORD PANEL ───────────────────────────────────────────
        wake_frame = ctk.CTkFrame(scroll, fg_color=COLOR_PANEL, corner_radius=10, border_color="#00ffcc", border_width=1)
        wake_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wake_frame, text="👂 WAKE WORD: \"HEY OMNI\"", font=("Consolas", 13, "bold"), text_color="#00ffcc").pack(anchor="w", padx=15, pady=(12, 5))
        ctk.CTkLabel(wake_frame, text="Always-on microphone listener. Activates Neural Omni hands-free.", font=("Consolas", 10), text_color="gray").pack(anchor="w", padx=15)

        row_wake = ctk.CTkFrame(wake_frame, fg_color="transparent")
        row_wake.pack(fill="x", padx=15, pady=(10, 12))
        self.wake_toggle = ctk.CTkSwitch(row_wake, text="Enable Wake Word Listener", font=("Consolas", 12, "bold"), text_color="#00ffcc", command=self._toggle_wake_word)
        self.wake_toggle.pack(side="left")
        self.lbl_wake_status = ctk.CTkLabel(row_wake, text="● INACTIVE", font=("Consolas", 11), text_color="gray")
        self.lbl_wake_status.pack(side="left", padx=20)

    # ── Communications Action Methods ──────────────────────────────────
    def _email_connect(self):
        addr = self.entry_email_addr.get().strip()
        pw = self.entry_email_pw.get().strip()
        if not addr or not pw:
            self.lbl_email_status.configure(text="⚠ Enter email and App Password", text_color="yellow")
            return
        result = self.email_agent_v3.configure(addr, pw)
        color = "#00ff66" if "✅" in result else COLOR_ERROR
        self.lbl_email_status.configure(text=result[:80], text_color=color)

    def _email_read_inbox(self):
        def task():
            result = self.email_agent_v3.get_unread(5)
            self.after(0, lambda: self._email_output(result))
        threading.Thread(target=task, daemon=True).start()
        self.txt_email_output.delete("0.0", "end")
        self.txt_email_output.insert("0.0", "Fetching inbox...")

    def _email_send(self):
        to = self.entry_email_to.get().strip()
        subj = self.entry_email_subj.get().strip()
        body = self.txt_email_body.get("0.0", "end").strip()
        def task():
            result = self.email_agent_v3.send_email(to, subj, body)
            self.after(0, lambda: self._email_output(result))
        threading.Thread(target=task, daemon=True).start()

    def _email_output(self, text):
        self.txt_email_output.delete("0.0", "end")
        self.txt_email_output.insert("0.0", text)

    def _calendar_connect(self):
        def task():
            result = self.calendar_agent_v3.authenticate()
            self.after(0, lambda: self.txt_cal_output.insert("end", result + "\n"))
        threading.Thread(target=task, daemon=True).start()

    def _calendar_view(self):
        def task():
            result = self.calendar_agent_v3.get_upcoming_events(5)
            self.after(0, lambda: self._cal_output(result))
        threading.Thread(target=task, daemon=True).start()

    def _calendar_create(self):
        title = self.entry_cal_title.get().strip()
        date = self.entry_cal_date.get().strip()
        time_str = self.entry_cal_time.get().strip()
        def task():
            result = self.calendar_agent_v3.create_event(title, date, time_str)
            self.after(0, lambda: self._cal_output(result))
        threading.Thread(target=task, daemon=True).start()

    def _cal_output(self, text):
        self.txt_cal_output.delete("0.0", "end")
        self.txt_cal_output.insert("0.0", text)

    def _phone_connect(self):
        sid = self.entry_twilio_sid.get().strip()
        token = self.entry_twilio_token.get().strip()
        frm = self.entry_twilio_from.get().strip()
        def task():
            result = self.call_agent_v3.configure(sid, token, frm)
            color = "#00ff66" if "✅" in result else COLOR_ERROR
            self.after(0, lambda: self.lbl_phone_status.configure(text=result[:80], text_color=color))
        threading.Thread(target=task, daemon=True).start()

    def _phone_call(self):
        to = self.entry_phone_to.get().strip()
        msg = self.entry_phone_msg.get().strip()
        def task():
            result = self.call_agent_v3.make_call(to, msg)
            self.after(0, lambda: self.lbl_phone_status.configure(text=result[:100]))
        threading.Thread(target=task, daemon=True).start()

    def _phone_sms(self):
        to = self.entry_phone_to.get().strip()
        msg = self.entry_phone_msg.get().strip()
        def task():
            result = self.call_agent_v3.send_sms(to, msg)
            self.after(0, lambda: self.lbl_phone_status.configure(text=result[:100]))
        threading.Thread(target=task, daemon=True).start()

    def _toggle_wake_word(self):
        if self.wake_toggle.get():
            result = self.wake_word_agent.start()
            self.lbl_wake_status.configure(text="● ACTIVE — Say 'Hey Omni'", text_color="#00ffcc")
            self.log(f">> WAKE WORD: {result}")
        else:
            self.wake_word_agent.stop()
            self.lbl_wake_status.configure(text="● INACTIVE", text_color="gray")

    def _on_wake_word(self):
        """Called by WakeWordAgent when 'Hey Omni' is detected."""
        self.after(0, self._focus_and_listen)

    def _focus_and_listen(self):
        self.lift()
        self.focus_force()
        self.select_tab("COMMAND CENTER")
        self.log(">> 👂 WAKE WORD DETECTED! LISTENING FOR COMMAND...")
        if self.voice_available and not self.is_listening:
            self.toggle_listening()

    def _setup_whatsapp_tab(self):
        parent = self.tab_whatsapp
        parent.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(parent, text="WHATSAPP PRO AUTOMATION", font=("Consolas", 18, "bold"), text_color="#25D366").pack(pady=20)
        
        frame_main = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10, border_color="#1e1e38", border_width=1)
        frame_main.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame_main, text="DIRECT MESSAGE CONSOLE", font=("Consolas", 14, "bold"), text_color="#25D366").pack(anchor="w", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(frame_main, text="TARGET (Phone / Chat URL):", font=("Consolas", 11), text_color="gray").pack(anchor="w", padx=15)
        self.entry_wa_target = ctk.CTkEntry(frame_main, placeholder_text="e.g. +1234567890 or https://chat.whatsapp.com/...", font=("Consolas", 12))
        self.entry_wa_target.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(frame_main, text="MESSAGE / AI PROMPT CONTEXT:", font=("Consolas", 11), text_color="gray").pack(anchor="w", padx=15)
        self.txt_wa_msg = ctk.CTkTextbox(frame_main, height=80, font=("Consolas", 12))
        self.txt_wa_msg.pack(fill="x", padx=15, pady=(0, 10))
        
        frame_actions = ctk.CTkFrame(frame_main, fg_color="transparent")
        frame_actions.pack(fill="x", padx=15, pady=(5, 15))
        
        self.btn_wa_send = ctk.CTkButton(frame_actions, corner_radius=8, text="SEND CUSTOM MESSAGE", command=lambda: self.execute_whatsapp(ai=False), fg_color="#075e54", hover_color="#128c7e", text_color="white", font=("Consolas", 12, "bold"))
        self.btn_wa_send.pack(side="left", padx=(0, 10))
        
        self.btn_wa_ai = ctk.CTkButton(frame_actions, corner_radius=8, text="GENERATE & SEND AI MESSAGE", command=lambda: self.execute_whatsapp(ai=True), fg_color="#25D366", hover_color="#1DA851", text_color="black", font=("Consolas", 12, "bold"))
        self.btn_wa_ai.pack(side="left")
        
        self.lbl_wa_status = ctk.CTkLabel(frame_main, text="READY", font=("Consolas", 11), text_color="gray")
        self.lbl_wa_status.pack(pady=10)

        # --- AUTORESPONDER BOT ---
        frame_bot = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10, border_color="#1e1e38", border_width=1)
        frame_bot.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(frame_bot, text="⚡ AI AUTO-RESPONDER BOT", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(frame_bot, text="BOT PERSONA / INSTRUCTIONS:", font=("Consolas", 11), text_color="gray").pack(anchor="w", padx=15)
        
        self.entry_wa_bot_prompt = ctk.CTkEntry(frame_bot, placeholder_text="e.g. My assistant. Tell them I am away and will reply later.", font=("Consolas", 12))
        self.entry_wa_bot_prompt.pack(fill="x", padx=15, pady=(0, 10))
        
        row_bot = ctk.CTkFrame(frame_bot, fg_color="transparent")
        row_bot.pack(fill="x", padx=15, pady=(5, 15))
        
        self.btn_wa_bot_start = ctk.CTkButton(row_bot, corner_radius=8, text="🚀 START AUTO-RESPONDER", command=self.start_wa_autoresponder, fg_color="#1DA851", hover_color="#25D366", text_color="black", font=("Consolas", 12, "bold"))
        self.btn_wa_bot_start.pack(side="left", padx=(0, 10))
        
        self.btn_wa_bot_stop = ctk.CTkButton(row_bot, corner_radius=8, text="⛔ STOP", command=self.stop_wa_autoresponder, fg_color="#7a0000", hover_color="#cc0000", font=("Consolas", 11, "bold"), width=80, state="disabled")
        self.btn_wa_bot_stop.pack(side="left")
        
        self.lbl_wa_bot_status = ctk.CTkLabel(row_bot, text="READY", font=("Consolas", 11), text_color="gray")
        self.lbl_wa_bot_status.pack(side="left", padx=15)

    def start_wa_autoresponder(self):
        prompt = self.entry_wa_bot_prompt.get().strip()
        if not prompt:
            self.lbl_wa_bot_status.configure(text="ERROR: ENTER BOT INSTRUCTIONS", text_color=COLOR_ERROR)
            return
            
        self.lbl_wa_bot_status.configure(text="STARTING...", text_color="yellow")
        self.btn_wa_bot_start.configure(state="disabled")
        self.btn_wa_bot_stop.configure(state="normal")
        self.tts.speak("Starting WhatsApp auto responder")
        
        threading.Thread(target=self._wa_autoresponder_thread, args=(prompt,), daemon=True).start()

    def stop_wa_autoresponder(self):
        self.social_manager.stop_bot()
        self.lbl_wa_bot_status.configure(text="STOP REQUESTED...", text_color="orange")
        self.btn_wa_bot_stop.configure(state="disabled")

    def _wa_autoresponder_thread(self, prompt):
        def cb(msg):
            self.after(0, lambda m=msg: self.lbl_wa_bot_status.configure(text=m[:60].upper(), text_color="yellow"))
            self._bot_log(f"[WA BOT] {msg}")

        try:
            result = asyncio.run_coroutine_threadsafe(
                self.social_manager.check_unread_whatsapp_messages(prompt, cb),
                self.loop
            ).result(timeout=3600)
            
            color = COLOR_SUCCESS if "finished" in result.lower() else COLOR_ACCENT
            self.after(0, lambda: self.lbl_wa_bot_status.configure(text=result.upper(), text_color=color))
            self.tts.speak("WhatsApp auto responder finished")
        except Exception as e:
            self.after(0, lambda: self.lbl_wa_bot_status.configure(text=f"ERROR: {e}", text_color=COLOR_ERROR))
        finally:
            self.after(0, lambda: self.btn_wa_bot_start.configure(state="normal"))
            self.after(0, lambda: self.btn_wa_bot_stop.configure(state="disabled"))

    def execute_whatsapp(self, ai=False):
        target = self.entry_wa_target.get().strip()
        msg_context = self.txt_wa_msg.get("0.0", "end").strip()
        
        if not target or (not ai and not msg_context):
            self.lbl_wa_status.configure(text="ERROR: MISSING TARGET OR MESSAGE", text_color=COLOR_ERROR)
            return
            
        self.lbl_wa_status.configure(text="PROCESSING...", text_color="yellow")
        self.tts.speak("Starting WhatsApp automation")
        
        self.btn_wa_send.configure(state="disabled")
        self.btn_wa_ai.configure(state="disabled")
        
        threading.Thread(target=self._whatsapp_thread, args=(target, msg_context, ai), daemon=True).start()

    def _whatsapp_thread(self, target, context, ai):
        try:
            if ai:
                self.after(0, lambda: self.lbl_wa_status.configure(text="GENERATING AI MESSAGE..."))
                prompt = (
                    f"You are responding via WhatsApp. Context/Request: {context}\n"
                    f"Write a natural, concise text message. Max 2 sentences."
                )
                msg_text = self.content_gen.generate_text(prompt, platform="WhatsApp", vibe="Friendly")
                self.after(0, lambda: self.lbl_wa_status.configure(text=f"SENDING: {msg_text[:30]}..."))
            else:
                msg_text = context
                
            result = asyncio.run_coroutine_threadsafe(
                self.social_manager.auto_message_whatsapp(target, msg_text),
                self.loop
            ).result(timeout=60)
            
            color = COLOR_SUCCESS if result.startswith("✅") else COLOR_ERROR
            self.after(0, lambda: self.lbl_wa_status.configure(text=result, text_color=color))
            self.tts.speak("WhatsApp task finished")
        except Exception as e:
            self.after(0, lambda: self.lbl_wa_status.configure(text=f"ERROR: {e}", text_color=COLOR_ERROR))
            self.tts.speak("WhatsApp task failed")
        finally:
            self.after(0, lambda: self.btn_wa_send.configure(state="normal"))
            self.after(0, lambda: self.btn_wa_ai.configure(state="normal"))

    def _setup_data_tab(self):
        parent = self.tab_data
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # ── Header
        hdr = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10,
                           border_color=COLOR_BORDER, border_width=1)
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="\U0001f52c  DEEP RESEARCH ENGINE",
                     font=("Consolas", 18, "bold"), text_color=COLOR_ACCENT
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=12)
        ctk.CTkLabel(hdr, text="\u25cf AI-POWERED  |  MULTI-SOURCE  |  AUTO-EXPORT",
                     font=("Consolas", 9), text_color=COLOR_GOLD
                     ).grid(row=0, column=1, sticky="e", padx=20)

        # ── Config
        cfg = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10,
                           border_color=COLOR_BORDER, border_width=1)
        cfg.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        cfg.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cfg, text="RESEARCH TOPIC:", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w", padx=15, pady=(14, 4))
        self.research_topic = ctk.CTkEntry(cfg,
            placeholder_text="e.g. 'Impact of AI on healthcare 2025'",
            font=("Consolas", 12), fg_color=COLOR_LOG,
            border_color=COLOR_ACCENT, border_width=1, text_color=COLOR_TEXT)
        self.research_topic.grid(row=0, column=1, sticky="ew", padx=10, pady=(14, 4))

        ctk.CTkLabel(cfg, text="MAX SOURCES:", font=("Consolas", 11),
                     text_color=COLOR_TEXT_DIM).grid(row=1, column=0, sticky="w", padx=15, pady=4)
        src_row = ctk.CTkFrame(cfg, fg_color="transparent")
        src_row.grid(row=1, column=1, sticky="w", padx=10, pady=4)
        self.research_src_count = ctk.CTkSlider(src_row, from_=2, to=10, number_of_steps=8,
                                                 width=200, button_color=COLOR_ACCENT,
                                                 progress_color=COLOR_ACCENT)
        self.research_src_count.set(6)
        self.research_src_count.pack(side="left")
        self.research_src_lbl = ctk.CTkLabel(src_row, text="6 pages",
                                              font=("Consolas", 11), text_color=COLOR_ACCENT)
        self.research_src_lbl.pack(side="left", padx=8)
        self.research_src_count.configure(
            command=lambda v: self.research_src_lbl.configure(text=f"{int(v)} pages"))

        ctk.CTkLabel(cfg, text="EXPORT FORMAT:", font=("Consolas", 11),
                     text_color=COLOR_TEXT_DIM).grid(row=2, column=0, sticky="w", padx=15, pady=4)
        fmt_row = ctk.CTkFrame(cfg, fg_color="transparent")
        fmt_row.grid(row=2, column=1, sticky="w", padx=10, pady=4)
        self.research_format = ctk.StringVar(value="Word (.docx)")
        ctk.CTkRadioButton(fmt_row, text="Word (.docx)",  variable=self.research_format,
                           value="Word (.docx)", font=("Consolas", 11),
                           text_color=COLOR_TEXT, fg_color=COLOR_ACCENT).pack(side="left", padx=(0,15))
        ctk.CTkRadioButton(fmt_row, text="Excel (.xlsx)", variable=self.research_format,
                           value="Excel (.xlsx)", font=("Consolas", 11),
                           text_color=COLOR_TEXT, fg_color=COLOR_ACCENT).pack(side="left", padx=(0,15))
        ctk.CTkRadioButton(fmt_row, text="Both", variable=self.research_format,
                           value="Both", font=("Consolas", 11),
                           text_color=COLOR_TEXT, fg_color=COLOR_ACCENT).pack(side="left")

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 14))
        self.research_btn_start = ctk.CTkButton(btn_row, corner_radius=8,
            text="\U0001f52c  START DEEP RESEARCH", command=self._research_start,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color="#000", font=("Consolas", 13, "bold"), height=38)
        self.research_btn_start.pack(side="left", padx=(5, 10))
        ctk.CTkButton(btn_row, corner_radius=8, text="\u26d4 STOP", command=self._research_stop,
            fg_color=COLOR_PANEL, border_color=COLOR_ERROR, border_width=1,
            hover_color="#1a0010", text_color=COLOR_ERROR,
            font=("Consolas", 11, "bold"), width=80, height=38).pack(side="left")
        self.research_status = ctk.CTkLabel(btn_row, text="\u25cf IDLE",
            font=("Consolas", 11), text_color=COLOR_TEXT_DIM)
        self.research_status.pack(side="left", padx=15)
        self.research_progress = ctk.CTkProgressBar(btn_row, width=160,
            progress_color=COLOR_ACCENT, fg_color=COLOR_PANEL2)
        self.research_progress.pack(side="left")
        self.research_progress.set(0)

        # ── Live Log
        self.research_log = ctk.CTkTextbox(parent,
            fg_color=COLOR_LOG, text_color="#00ff99",
            font=("Consolas", 11), corner_radius=10,
            border_color=COLOR_BORDER, border_width=1)
        self.research_log.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self._research_report = None
        self._researcher = None

    # ─── Deep Research Logic ────────────────────────────────────────────────────

    def _research_rlog(self, msg: str):
        """Append a message to the research live-log box (thread-safe)."""
        def append():
            self.research_log.configure(state="normal")
            self.research_log.insert("end", f"{msg}\n")
            self.research_log.see("end")
            self.research_log.configure(state="disabled")
        self.after(0, append)

    def _research_start(self):
        topic = self.research_topic.get().strip()
        if not topic:
            self._research_rlog("[ERROR] Please enter a research topic.")
            return

        if not getattr(self.agent, "page", None):
            self._research_rlog("[ERROR] Initialize the Browser first (Command Center).")
            return

        self.research_btn_start.configure(state="disabled")
        self.research_status.configure(text="● RESEARCHING…", text_color=COLOR_WARN)
        self.research_progress.set(0)

        # Clear log
        self.research_log.configure(state="normal")
        self.research_log.delete("1.0", "end")
        self.research_log.configure(state="disabled")

        max_src = int(self.research_src_count.get())
        fmt = self.research_format.get()

        import threading
        threading.Thread(
            target=self._research_thread, args=(topic, max_src, fmt), daemon=True
        ).start()

    def _research_thread(self, topic: str, max_src: int, fmt: str):
        """Background thread — runs the async research pipeline."""
        import asyncio
        from tools.deep_researcher import DeepResearcher, export_to_word, export_to_excel

        llm = self.llm if self.use_ai else None

        async def run():
            researcher = DeepResearcher(
                page=self.agent.page,
                llm_provider=llm,
                log_fn=self._research_rlog
            )
            self._researcher = researcher
            return await researcher.run(topic, max_src)

        try:
            report = asyncio.run_coroutine_threadsafe(run(), self.loop).result(timeout=300)
        except Exception as e:
            self._research_rlog(f"[FATAL] Research failed: {e}")
            self.after(0, lambda: self.research_status.configure(
                text="● FAILED", text_color=COLOR_ERROR))
            self.after(0, lambda: self.research_btn_start.configure(state="normal"))
            return

        self._research_report = report
        self.after(0, lambda: self.research_progress.set(0.8))

        # Export
        from tkinter import filedialog
        from datetime import datetime
        import os

        home = os.path.expanduser("~")
        desktop = os.path.join(home, "OneDrive", "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.join(home, "Desktop")

        safe_name = re.sub(r'[^\w\s-]', '', topic)[:40].strip().replace(' ', '_')
        timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name  = f"Research_{safe_name}_{timestamp}"

        def do_export():
            ok_word = ok_excel = True

            if fmt in ("Word (.docx)", "Both"):
                fpath = filedialog.asksaveasfilename(
                    title="Save Word Research Paper",
                    initialdir=desktop,
                    initialfile=f"{base_name}.docx",
                    defaultextension=".docx",
                    filetypes=[("Word Document", "*.docx"), ("All Files", "*.*")]
                )
                if fpath:
                    ok_word = export_to_word(report, fpath)
                    self._research_rlog(f"[EXPORT] Word saved → {fpath}")

            if fmt in ("Excel (.xlsx)", "Both"):
                fpath = filedialog.asksaveasfilename(
                    title="Save Excel Research Paper",
                    initialdir=desktop,
                    initialfile=f"{base_name}.xlsx",
                    defaultextension=".xlsx",
                    filetypes=[("Excel Workbook", "*.xlsx"), ("All Files", "*.*")]
                )
                if fpath:
                    ok_excel = export_to_excel(report, fpath)
                    self._research_rlog(f"[EXPORT] Excel saved → {fpath}")

            self.research_progress.set(1.0)
            self.research_status.configure(
                text="● COMPLETE ✓" if (ok_word and ok_excel) else "● EXPORT ERROR",
                text_color=COLOR_SUCCESS if (ok_word and ok_excel) else COLOR_ERROR
            )
            self.research_btn_start.configure(state="normal")
            self._research_rlog("[OMNI RESEARCH] ✅ All done!")

        self.after(0, do_export)

    def _research_stop(self):
        if self._researcher:
            self._researcher.stop()
        self.research_status.configure(text="● STOPPED", text_color=COLOR_ERROR)
        self.research_btn_start.configure(state="normal")
        self._research_rlog("[USER] Research stopped.")

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

    def _save_notification_config(self):
        """Persist the notification settings to notifications.json."""
        cfg = {
            "enabled":        self.notif_enabled_var.get(),
            "type":           self.notif_type_var.get(),
            "style":          self.notif_style_var.get(),
            "show_duration":  self.notif_dur_var.get(),
            "custom_title":   self.notif_title_entry.get().strip(),
            "custom_message": self.notif_msg_entry.get().strip(),
            "update_version": self.notif_ver_entry.get().strip(),
            "update_message": self.notif_update_msg_entry.get().strip(),
        }
        _save_notif_config(cfg)
        self.lbl_notif_status.configure(text="✅  Notification saved! Will show on next launch.", text_color=COLOR_SUCCESS)
        self.after(4000, lambda: self.lbl_notif_status.configure(text=""))

    def _preview_notification(self):
        """Show a live preview of the current notification settings."""
        ntype    = self.notif_type_var.get()
        style    = self.notif_style_var.get()
        duration = self.notif_dur_var.get()
        if ntype == "update":
            title   = f"Update Available  v{self.notif_ver_entry.get().strip() or '?'}"
            message = self.notif_update_msg_entry.get().strip() or "A new version is available!"
            style   = "update"
        else:
            title   = self.notif_title_entry.get().strip() or "Notification"
            message = self.notif_msg_entry.get().strip() or "Your message here."
        if message:
            NotificationBanner(self, title, message, style=style, duration=duration)

    def on_provider_change(self):

        """Show/hide provider-specific settings"""
        provider = self.provider_var.get()
        # Hide all panels first
        self.frame_api.pack_forget()
        self.frame_ollama.pack_forget()
        self.frame_openrouter.pack_forget()
        # Show only the relevant one
        if provider == "ollama":
            self.frame_ollama.pack(anchor="w", padx=20, pady=10, fill="x")
        elif provider == "openrouter":
            self.frame_openrouter.pack(anchor="w", padx=20, pady=10, fill="x")
        else:  # gemini (default)
            self.frame_api.pack(fill="x", padx=20, pady=10)

    def save_ollama_config(self):
        """Save and connect to Ollama"""
        model = self.ollama_model_entry.get().strip() or "llava:latest"
        
        try:
            self.llm.configure_ollama(model)
            
            # Test connection
            self.lbl_model.configure(text=f"TESTING OLLAMA CONNECTION...", text_color="yellow")
            self.update() # Force UI update
            
            success, msg = self.llm.test_connection()
            
            if success:
                self.cfg.set("llm_provider", "ollama")
                self.cfg.set("ollama_model", model)
                self.use_ai = True
                self.lbl_model.configure(text=f"CURRENT: OLLAMA ({model}) - ONLINE", text_color=COLOR_SUCCESS)
                self.log(f"SETTINGS: OLLAMA CONNECTED ({model})")
                self.tts.speak("Ollama Connected")
            else:
                self.lbl_model.configure(text=f"ERROR: {msg}", text_color=COLOR_ERROR)
                self.log(f"SETTINGS: OLLAMA ERROR - {msg}")
                self.tts.speak("Ollama Connection Failed")
                
        except Exception as e:
            self.log(f"ERROR: Failed to configure Ollama - {str(e)}")

    def save_openrouter_config(self):
        """Save and connect to OpenRouter"""
        key = self.openrouter_key_entry.get().strip()
        model = self.openrouter_model_entry.get().strip() or "google/gemini-2.0-flash-001"

        if not key:
            self.lbl_model.configure(text="ERROR: API key is required.", text_color=COLOR_ERROR)
            return

        try:
            self.llm.configure_openrouter(key, model)
            self.lbl_model.configure(text="TESTING OPENROUTER CONNECTION...", text_color="yellow")
            self.update()

            success, msg = self.llm.test_connection()

            if success:
                self.cfg.set("llm_provider", "openrouter")
                self.cfg.set("openrouter_key", key)
                self.cfg.set("openrouter_model", model)
                self.use_ai = True
                self.lbl_model.configure(
                    text=f"CURRENT: OPENROUTER ({model}) - ONLINE", text_color=COLOR_SUCCESS
                )
                self.log(f"SETTINGS: OPENROUTER CONNECTED ({model})")
                self.tts.speak("OpenRouter Connected")
            else:
                self.lbl_model.configure(text=f"ERROR: {msg}", text_color=COLOR_ERROR)
                self.log(f"SETTINGS: OPENROUTER ERROR - {msg}")
                self.tts.speak("OpenRouter Connection Failed")
        except Exception as e:
            self.log(f"ERROR: Failed to configure OpenRouter - {str(e)}")



    # --- Utilities ---
    def log(self, message):
        self.log_textbox.insert("end", f">> {message}\n")
        self.log_textbox.see("end")
        # Speak important messages
        if "ERROR" in message:
            self.tts.speak("Error detected")
        elif "COMPLETE" in message or "SUCCESS" in message or "ACHIEVED" in message:
            self.tts.speak("Operation complete")
        elif "INITIALIZED" in message:
            pass # Already spoke
    
    def crypto_log(self, msg):
        """Log messages to crypto trader tab"""
        try:
            self.crypto_log_display.configure(state="normal")
            self.crypto_log_display.insert("end", f">> {msg}\n")
            self.crypto_log_display.see("end")
            self.crypto_log_display.configure(state="disabled")
        except:
            # Fallback to main log if crypto log not available yet
            self.log(msg)

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
        provider_name = self.llm.get_provider_name().upper()
        self.log(f"ANALYZING INTENT via {provider_name} (VISION ACTIVE)...")
        # Capture screenshot first (sync or async?)
        # Since we are in main thread callback, we need to schedule async capture, or do it in the thread?
        # Browser access should be thread-safe(ish) or done via loop.
        # Safest: run entire flow in async task, then update UI.
        self.run_async(self._ai_pipeline(text))

    async def _get_best_screenshot(self):
        if not self.vision_checkbox.get():
            return None
            
        os_bytes = self.os_agent.take_screenshot() if self.godmode_checkbox.get() else None
        browser_bytes = None
        if self.agent.page:
            try:
                await self.agent.inject_som_overlay()
                browser_bytes = await self.agent.get_screenshot_bytes()
                await self.agent.remove_som_overlay()
            except Exception:
                pass
                
        if os_bytes and browser_bytes:
            import io
            from PIL import Image
            img_os = Image.open(io.BytesIO(os_bytes))
            img_browser = Image.open(io.BytesIO(browser_bytes))
            width = max(img_os.width, img_browser.width)
            height = img_os.height + img_browser.height
            combined = Image.new('RGB', (width, height), color='black')
            combined.paste(img_os, (0, 0))
            combined.paste(img_browser, (0, img_os.height))
            out_bytes = io.BytesIO()
            combined.save(out_bytes, format='JPEG', quality=65)
            return out_bytes.getvalue()
        elif os_bytes:
            return os_bytes
        elif browser_bytes:
            return browser_bytes
        return None

    async def _ai_pipeline(self, text):
        # Reset stop flag and show stop button
        self.autopilot_stop_requested = False
        self.after(0, lambda: self.btn_stop_autopilot.pack(side="left", padx=5, pady=20))
        
        # 0. Get Mode
        mode = self.option_mode.get()
        
        # 1. Capture Screen
        self.update_log_from_thread("CAPTURING SCREENSHOT...")
        screenshot = await self._get_best_screenshot()
        if screenshot:
            self.update_log_from_thread(f"SCREENSHOT CAPTURED ({len(screenshot)} bytes).")
        else:
            self.update_log_from_thread("NO SCREENSHOT (Browser not active?). SENDING TEXT ONLY.")
        
        # 2. Call API (in thread executor to not block loop?)
        self.update_log_from_thread(f"SENDING REQUEST TO {self.llm.get_provider_name().upper()}...")
        
        # Multimodal upload might be slow.
        # We can run sync blocking call in a thread executor provided by asyncio
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, self.llm.interpret_command, text, screenshot, mode)
        
        self.update_log_from_thread(f"AI RESPONSE RECEIVED.")
        self.update_log_from_thread(f"AI PLAN ({mode}): {response}")
        
        # 3. Execute Action Sequence
        if isinstance(response, dict) and "error" in response:
             self.update_log_from_thread(f"AI ERROR: {response['error']}")
             return

        if not isinstance(response, list):
             self.update_log_from_thread("AI ERROR: INVALID RESPONSE FORMAT.")
             return

        for step in response:
            if self.autopilot_stop_requested:
                self.update_log_from_thread(">> EXECUTION HALTED BY USER.")
                break
                
            action = step.get("action")
            self.update_log_from_thread(f"EXECUTING: {action.upper()}")
            
            if action == "navigate":
                await self._navigate_task(step.get("url"))
            elif action == "click_id":
                try:
                    await self.agent.click_id(step.get("id"))
                except Exception as e:
                    self.update_log_from_thread(f">> ERROR EXECUTING CLICK_ID: {e}")
                    break
            elif action == "type_id":
                try:
                    await self.agent.type_id(step.get("id"), step.get("text"))
                except Exception as e:
                    self.update_log_from_thread(f">> ERROR EXECUTING TYPE_ID: {e}")
                    break
            elif action == "click":
                try:
                    await self.agent.click(step.get("selector"))
                except Exception as e:
                    self.update_log_from_thread(f">> ERROR EXECUTING CLICK: {e}")
                    break
            elif action == "type":
                try:
                    await self.agent.type(step.get("selector"), step.get("text"))
                except Exception as e:
                    self.update_log_from_thread(f">> ERROR EXECUTING TYPE: {e}")
                    break
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
            elif action == "auto_message_whatsapp":
                if self.godmode_checkbox.get():
                    self.update_log_from_thread("CONVERTING WEB WHATSAPP MACRO TO PHYSICAL OS DESKTOP MACRO...")
                    target = step.get("target", "")
                    text_msg = step.get("text", "")
                    
                    self.os_agent.open_application("whatsapp")
                    self.update_log_from_thread("Waiting for Desktop App to load...")
                    await asyncio.sleep(5)
                    
                    self.update_log_from_thread(f"Searching for Contact: {target}")
                    self.os_agent.keyboard_press("ctrl+f")
                    await asyncio.sleep(0.5)
                    self.os_agent.keyboard_type(target)
                    await asyncio.sleep(2)
                    
                    self.os_agent.keyboard_press("enter")
                    await asyncio.sleep(1)
                    
                    self.update_log_from_thread("Typing physical message...")
                    self.os_agent.keyboard_type(text_msg)
                    await asyncio.sleep(0.5)
                    self.os_agent.keyboard_press("enter")
                    self.update_log_from_thread("PHYSICAL O/S WHATSAPP MACRO COMPLETE.")
                else:
                    self.update_log_from_thread("STARTING DEDICATED BROWSER WHATSAPP AUTOMATION...")
                    result = await self.social_manager.auto_message_whatsapp(step.get("target"), step.get("text"))
                    self.update_log_from_thread(f"WHATSAPP RESULT: {result}")
            # --- OS CONTROL & FILE TOOLS ---
            elif action == "os_mouse_click" and self.godmode_checkbox.get():
                res = self.os_agent.mouse_click(step.get("x"), step.get("y"), step.get("button", "left"))
                self.update_log_from_thread(f"OS RESULT: {res}")
            elif action == "os_mouse_move" and self.godmode_checkbox.get():
                res = self.os_agent.mouse_move(step.get("x"), step.get("y"))
                self.update_log_from_thread(f"OS RESULT: {res}")
            elif action == "os_keyboard_type" and self.godmode_checkbox.get():
                res = self.os_agent.keyboard_type(step.get("text"))
                self.update_log_from_thread(f"OS RESULT: {res}")
            elif action == "os_keyboard_press" and self.godmode_checkbox.get():
                res = self.os_agent.keyboard_press(step.get("key_combo"))
                self.update_log_from_thread(f"OS RESULT: {res}")
            elif action == "os_open_app" and self.godmode_checkbox.get():
                res = self.os_agent.open_application(step.get("app_name_or_path"))
                self.update_log_from_thread(f"OS RESULT: {res}")
            elif action == "os_run_command" and self.godmode_checkbox.get():
                import subprocess
                cmd = step.get("command")
                if cmd:
                    try:
                        # Force powershell execution since prompts ask for it, encode to bypass quote parsing bugs
                        if "powershell" not in cmd.lower():
                            import base64
                            encoded = base64.b64encode(cmd.encode("utf-16-le")).decode("utf-8")
                            cmd = f'powershell.exe -EncodedCommand {encoded}'
                        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                        out_str = res.stdout.strip() if res.stdout else ""
                        err_str = res.stderr.strip() if res.stderr else ""
                        final_out = out_str
                        if err_str:
                            final_out += f"\n[ERROR/STDERR]: {err_str}"
                        if not final_out.strip():
                            final_out = "SUCCESS (No Output)"
                        if res.returncode != 0:
                            final_out = f"FAILED [Exit {res.returncode}]:\n{final_out}"
                        self.update_log_from_thread(f"SHELL RESULT:\n{final_out[:500]}")
                    except Exception as e:
                        self.update_log_from_thread(f"SHELL ERROR: {e}")
            elif action == "os_list_dir" and self.godmode_checkbox.get():
                import os
                try:
                    items = os.listdir(step.get("path", "."))
                    items_str = ", ".join(items) if items else "Empty"
                    self.update_log_from_thread(f"DIR CONTENTS: {items_str}")
                except Exception as e:
                    self.update_log_from_thread(f"DIR ERROR: {e}")
            elif action == "os_read_file" and self.godmode_checkbox.get():
                try:
                    with open(step.get("path"), 'r', encoding='utf-8') as f:
                        content = f.read(500)
                    self.update_log_from_thread(f"FILE PREVIEW:\n{str(content)}")
                except Exception as e:
                    self.update_log_from_thread(f"FILE ERROR: {e}")
            else:
                self.update_log_from_thread(f"UNKNOWN AI ACTION: {action} (or God Mode disabled)")
            
            # Small delay between steps
            await asyncio.sleep(0.5)
            
        # Hide stop button when done
        self.after(0, lambda: self.btn_stop_autopilot.pack_forget())

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
            if not getattr(self.agent, "page", None):
                self.update_log_from_thread("BOOTING INTERNAL BROWSER ENGINE...")
                await self.agent.start()
            await self.agent.navigate(url)
            self.update_log_from_thread(f"ARRIVAL CONFIRMED.")
        except Exception as e:
            self.update_log_from_thread(f"NAV ERROR: {e}")

    def _get_macro_list(self):
        import os
        if not os.path.exists("recordings"):
            return []
        macros = [f for f in os.listdir("recordings") if f.endswith(".json")]
        return macros

    # --- Recorder ---
    def start_recording(self):
        if not self.agent.page:
            self.log("ERROR: INITIALIZE BROWSER FIRST BEFORE TRAINING.")
            return
        self.agent.start_recording("User Trained Sequence")
        self.log("🔴 TRAINING MODE ACTIVE. DO THE TASK IN THE BROWSER. OMNI IS WATCHING...")
        self.btn_rec_start.configure(text="RECORDING...", fg_color="#cc0000")

    def save_recording(self):
        macro_name = self.combo_macro.get() or "recording.json"
        if not macro_name.endswith(".json"): macro_name += ".json"
        
        self.agent.save_recording(macro_name)
        self.log(f"✅ TRAINING SAVED AS: {macro_name}")
        self.btn_rec_start.configure(text="🔴 TRAIN", fg_color="#7a0000")
        
        # Refresh combo box list
        self.combo_macro.configure(values=self._get_macro_list())
        self.combo_macro.set(macro_name)

    def replay_recording(self):
        macro_name = self.combo_macro.get() or "recording.json"
        if not macro_name.endswith(".json"): macro_name += ".json"
        
        self.log(f"EXECUTING STORED SEQUENCE: {macro_name}...")
        self.run_async(self._replay_task(macro_name))

    async def _replay_task(self, filename):
        # Automatically spin up the browser if it crashed or was closed
        try:
            if not self.agent.page or self.agent.page.is_closed():
                if self.godmode_checkbox.get():
                    attached = await self.agent.attach_to_existing_browser()
                    if not attached:
                        await self.agent.start()
                else:
                    await self.agent.start()
        except Exception:
            pass  # Fallback gracefully
            
        await self.agent.replay_recording(filename)
        self.update_log_from_thread("EXECUTION COMPLETE.")

    # --- Voice ---
    def toggle_listening(self):
        if not self.voice_available: return
        if self.is_listening:
            self.is_listening = False
            self.btn_voice.configure(text="🎤 VOX: OFF", fg_color=COLOR_PANEL, border_color="#1e1e38", text_color="white")
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
                     self.after(0, lambda: self.btn_voice.configure(text="🎤 VOX: OFF", fg_color=COLOR_PANEL, border_color="#1e1e38", text_color="white"))
                     self.update_log_from_thread("VOX TERMINATED BY USER.")
                     break
                
                if self.use_ai:
                    self.process_ai_command(command)
                else:
                    self.process_command(command)

    # --- Vision Auto-Monitor ---
    def toggle_vision(self):
        if self.vision_checkbox.get():
            self.log(">> VISION AI DEPLOYED. MONITORING SCREEN...")
            self.vision_agent.start()
        else:
            self.log(">> VISION AI STANDBY.")
            self.vision_agent.stop()
            
    def show_vision_toast(self, message):
        """Displays a non-blocking toast popup in the corner of the screen"""
        self.after(0, lambda: self._create_toast(message))
        
    def _create_toast(self, message):
        toast = ctk.CTkToplevel(self)
        toast.title("Vision Alert")
        toast.geometry("400x120-20-60") # Bottom right corner
        toast.overrideredirect(True) # No window border
        toast.attributes("-alpha", 0.95)
        toast.attributes("-topmost", True)
        toast.configure(fg_color="#0A192F") # Deep blue backing
        
        frame = ctk.CTkFrame(toast, border_width=2, border_color="#00ffcc", corner_radius=10, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        lbl_head = ctk.CTkLabel(frame, text="👁️ PROACTIVE AI SUGGESTION", font=("Consolas", 12, "bold"), text_color="#00ffcc")
        lbl_head.pack(pady=(5, 0))
        
        lbl_msg = ctk.CTkLabel(frame, text=message, font=("Arial", 11), text_color="white", wraplength=380, justify="left")
        lbl_msg.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Auto-destroy after 10 seconds
        self.after(10000, toast.destroy)

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
                
                # Capture best screenshot available
                screenshot = await self._get_best_screenshot()
                
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
                        elif action == "click_id":
                            await self.agent.click_id(step.get("id"))
                        elif action == "type_id":
                            await self.agent.type_id(step.get("id"), step.get("text"))
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
                            self.update_log_from_thread(f"  Extracted: {text}")
                        # --- OS CONTROL ACTIONS ---
                        elif action == "os_mouse_click" and self.godmode_checkbox.get():
                            self.os_agent.mouse_click(step.get("x"), step.get("y"), step.get("button", "left"))
                        elif action == "os_mouse_move" and self.godmode_checkbox.get():
                            self.os_agent.mouse_move(step.get("x"), step.get("y"))
                        elif action == "os_keyboard_type" and self.godmode_checkbox.get():
                            self.os_agent.keyboard_type(step.get("text"))
                        elif action == "os_keyboard_press" and self.godmode_checkbox.get():
                            self.os_agent.keyboard_press(step.get("key_combo"))
                        elif action == "os_open_app" and self.godmode_checkbox.get():
                            self.os_agent.open_application(step.get("app_name_or_path"))
                        elif action == "copy_to_clipboard":
                            await self.agent.copy_to_clipboard(step.get("text"))
                        elif action == "paste_from_clipboard":
                            await self.agent.paste_from_clipboard(step.get("selector"))
                        elif action == "os_run_command" and self.godmode_checkbox.get():
                            import subprocess
                            cmd = step.get("command")
                            if cmd:
                                try:
                                    # Encode to prevent quote parsing bugs
                                    if "powershell" not in cmd.lower():
                                        import base64
                                        encoded = base64.b64encode(cmd.encode("utf-16-le")).decode("utf-8")
                                        cmd = f'powershell.exe -EncodedCommand {encoded}'
                                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                                    out_str = res.stdout.strip() if res.stdout else ""
                                    err_str = res.stderr.strip() if res.stderr else ""
                                    final_out = out_str
                                    if err_str:
                                        final_out += f"\n[ERROR/STDERR]: {err_str}"
                                    if not final_out.strip():
                                        final_out = "SUCCESS (No Output)"
                                    if res.returncode != 0:
                                        final_out = f"FAILED [Exit {res.returncode}]:\n{final_out}"
                                    self.update_log_from_thread(f"SHELL RESULT:\n{final_out[:500]}")
                                except Exception as e:
                                    self.update_log_from_thread(f"SHELL ERROR: {e}")
                        elif action == "os_list_dir" and self.godmode_checkbox.get():
                            import os
                            try:
                                items = os.listdir(step.get("path", "."))
                                items_str = ", ".join(items) if items else "Empty"
                                self.update_log_from_thread(f"DIR CONTENTS: {items_str}")
                            except Exception as e:
                                self.update_log_from_thread(f"DIR ERROR: {e}")
                        elif action == "os_read_file" and self.godmode_checkbox.get():
                            try:
                                with open(step.get("path"), 'r', encoding='utf-8') as f:
                                    content = f.read(500)
                                self.update_log_from_thread(f"FILE PREVIEW:\n{str(content)}")
                            except Exception as e:
                                self.update_log_from_thread(f"FILE ERROR: {e}")
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

    # --- Scheduler Logic ---
    def _scheduler_loop(self):
        while self.scheduler_running:
            try:
                schedule.run_pending()
            except Exception as e:
                self.update_log_from_thread(f"SCHEDULER THREAD ERROR: {e}")
            time.sleep(1)

    def add_scheduled_task(self):
        t_time = self.entry_sched_time.get()
        t_type = self.option_sched_type.get()
        t_target = self.entry_sched_target.get()
        
        if not t_time or not t_target:
            return
            
        schedule.every().day.at(t_time).do(self._execute_scheduled, t_type, t_target)
        
        # Add to UI
        lbl = ctk.CTkLabel(self.sched_list_frame, text=f"[{t_time}] {t_type}: {t_target}", anchor="w")
        lbl.pack(fill="x", padx=5, pady=2)
        
        self.log(f"SCHEDULED: {t_type} at {t_time}")
        self.tts.speak("Task scheduled")

    def _execute_scheduled(self, t_type, t_target):
        self.update_log_from_thread(f"EXECUTING SCHEDULED TASK: {t_type} - {t_target}")
        self.tts.speak("Executing scheduled task")
        if t_type == "REPLAY":
            self.run_async(self._replay_task(t_target))
        elif t_type == "AUTO-PILOT":
            self.run_async(self._autopilot_loop(t_target))

    # --- Scraper Logic ---
    def start_scraping(self):
        url = self.entry_scrape_url.get()
        container = self.entry_scrape_container.get()
        fields_raw = self.entry_scrape_fields.get("0.0", "end").strip()
        
        if not url or not container or not fields_raw:
            self.lbl_scrape_status.configure(text="ERROR: MISSING FIELDS", text_color=COLOR_ERROR)
            return
            
        # Parse fields
        fields = {}
        for line in fields_raw.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                fields[k.strip()] = v.strip()
        
        self.lbl_scrape_status.configure(text="SCRAPING...", text_color="white")
        self.run_async(self._scrape_task(url, container, fields))

    async def _scrape_task(self, url, container, fields):
        try:
            await self.agent.navigate(url)
            data = await self.agent.scrape_data(container, fields)
            
            # Save to CSV
            if data:
                df = pd.DataFrame(data)
                filename = f"scraped_data_{int(time.time())}.csv"
                df.to_csv(filename, index=False)
                self.update_log_from_thread(f"SCRAPE SUCCESS: Saved {len(data)} items to {filename}")
                self.tts.speak(f"Scraping complete. {len(data)} items saved.")
            else:
                self.update_log_from_thread("SCRAPE: NO DATA FOUND")
                self.tts.speak("No data found")
                
        except Exception as e:
            self.update_log_from_thread(f"SCRAPE ERROR: {e}")

    def on_closing(self):
        self.scheduler_running = False
        self.tts.stop()
        self.run_async(self.agent.close())
        self.destroy()
        sys.exit()

    # --- Crypto Trading Methods ---
    def _setup_crypto_tab(self):
        parent = self.tab_crypto
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Left Panel: Controls
        frame_controls = ctk.CTkFrame(parent, width=350, fg_color=COLOR_PANEL)
        frame_controls.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame_controls.grid_propagate(False)
        
        ctk.CTkLabel(frame_controls, text="CRYPTO TRADING SYSTEM", font=("Consolas", 16, "bold")).pack(pady=20)
        
        # Strategy Selection
        ctk.CTkLabel(frame_controls, text="TRADING STRATEGY", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.strategy_var = ctk.StringVar(value="RSI")
        self.option_strategy = ctk.CTkOptionMenu(frame_controls, values=list(STRATEGIES.keys()), variable=self.strategy_var, command=self.on_strategy_change)
        self.option_strategy.pack(fill="x", padx=10, pady=5)
        
        # Symbol Input
        ctk.CTkLabel(frame_controls, text="TRADING PAIR", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.entry_symbol = ctk.CTkEntry(frame_controls, placeholder_text="BTCUSDT")
        self.entry_symbol.pack(fill="x", padx=10, pady=5)
        self.entry_symbol.insert(0, "BTCUSDT")
        
        # Trading Mode Selection
        ctk.CTkLabel(frame_controls, text="TRADING MODE", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.trading_mode_var = ctk.StringVar(value="Paper")
        self.option_trading_mode = ctk.CTkOptionMenu(
            frame_controls, 
            values=["Paper", "API (Binance)", "Browser"], 
            variable=self.trading_mode_var,
            command=self.on_trading_mode_change
        )
        self.option_trading_mode.pack(fill="x", padx=10, pady=5)
        
        # Exchange Selection (for browser mode)
        ctk.CTkLabel(frame_controls, text="EXCHANGE (Browser Mode)", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.exchange_var = ctk.StringVar(value="Binance")
        self.option_exchange = ctk.CTkOptionMenu(
            frame_controls,
            values=["Binance", "Coinbase", "Kraken"],
            variable=self.exchange_var
        )
        self.option_exchange.pack(fill="x", padx=10, pady=5)
        
        # Start/Stop Buttons
        btn_frame = ctk.CTkFrame(frame_controls, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start_trading = ctk.CTkButton(btn_frame, corner_radius=8, text="▶ START TRADING", command=self.start_trading, fg_color=COLOR_SUCCESS, hover_color="#00cc00", text_color="black", font=("Consolas", 12, "bold"))
        self.btn_start_trading.pack(fill="x", pady=5)
        
        self.btn_stop_trading = ctk.CTkButton(btn_frame, corner_radius=8, text="⏹ STOP TRADING", command=self.stop_trading, fg_color=COLOR_ERROR, hover_color="#cc0000", text_color="white", font=("Consolas", 12, "bold"))
        self.btn_stop_trading.pack(fill="x", pady=5)
        self.btn_stop_trading.configure(state="disabled")
        
        # Emergency Stop
        self.btn_emergency_stop = ctk.CTkButton(frame_controls, corner_radius=8, text="🚨 EMERGENCY STOP", command=self.emergency_stop, fg_color="#ff0000", hover_color="#770022", text_color="white", font=("Consolas", 14, "bold"), height=50)
        self.btn_emergency_stop.pack(fill="x", padx=10, pady=20)
        
        # Right Panel: Dashboard
        frame_dashboard = ctk.CTkScrollableFrame(parent, fg_color="transparent", label_text="LIVE DASHBOARD")
        frame_dashboard.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Portfolio Stats
        stats_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(stats_frame, text="PORTFOLIO", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        
        self.lbl_balance = ctk.CTkLabel(stats_frame, text="Balance: $10,000.00", font=("Consolas", 12))
        self.lbl_balance.pack(anchor="w", padx=20, pady=2)
        
        self.lbl_equity = ctk.CTkLabel(stats_frame, text="Equity: $10,000.00", font=("Consolas", 12))
        self.lbl_equity.pack(anchor="w", padx=20, pady=2)
        
        self.lbl_pnl = ctk.CTkLabel(stats_frame, text="Total P&L: $0.00 (0.00%)", font=("Consolas", 12))
        self.lbl_pnl.pack(anchor="w", padx=20, pady=2)
        
        self.lbl_daily_pnl = ctk.CTkLabel(stats_frame, text="Daily P&L: $0.00", font=("Consolas", 12))
        self.lbl_daily_pnl.pack(anchor="w", padx=20, pady=2)
        
        self.lbl_positions = ctk.CTkLabel(stats_frame, text="Open Positions: 0", font=("Consolas", 12))
        self.lbl_positions.pack(anchor="w", padx=20, pady=(2,10))
        
        # Open Positions
        positions_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
        positions_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(positions_frame, text="OPEN POSITIONS", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        
        self.positions_display = ctk.CTkTextbox(positions_frame, height=150, font=("Consolas", 11))
        self.positions_display.pack(fill="x", padx=10, pady=(0,10))
        self.positions_display.insert("0.0", "No open positions")
        self.positions_display.configure(state="disabled")
        
        # Trade History
        history_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(history_frame, text="TRADE HISTORY", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        
        self.trade_history_display = ctk.CTkTextbox(history_frame, font=("Consolas", 10))
        self.trade_history_display.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.trade_history_display.insert("0.0", "No trades yet")
        self.trade_history_display.configure(state="disabled")
        
        # Trading Log (NEW)
        log_frame = ctk.CTkFrame(frame_dashboard, fg_color=COLOR_PANEL)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(log_frame, text="TRADING LOG", font=("Consolas", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=10)
        
        self.crypto_log_display = ctk.CTkTextbox(log_frame, font=("Consolas", 9), height=200)
        self.crypto_log_display.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.crypto_log_display.insert("0.0", "Trading log will appear here...")
        self.crypto_log_display.configure(state="disabled")
        
        # Initialize strategy
        self.on_strategy_change("RSI")

    def on_strategy_change(self, strategy_name):
        """Handle strategy selection change"""
        strategy_class = STRATEGIES.get(strategy_name)
        if strategy_class:
            strategy = strategy_class()
            self.trading_engine.set_strategy(strategy)
            self.log(f"CRYPTO TRADER: Strategy changed to {strategy_name}")

    def on_trading_mode_change(self, mode):
        """Handle trading mode change"""
        self.log(f"Trading mode changed to: {mode}")
        
        # Show/hide exchange selector based on mode
        if mode == "Browser":
            self.option_exchange.configure(state="normal")
        else:
            self.option_exchange.configure(state="disabled")

    def start_trading(self):
        """Start automated trading"""
        symbol = self.entry_symbol.get().strip()
        if not symbol:
            self.log("ERROR: Please enter a trading pair")
            return
        
        self.current_symbol = symbol
        trading_mode = self.trading_mode_var.get()
        
        # Initialize appropriate trading client based on mode
        try:
            if trading_mode == "Paper":
                self.exchange_client = ExchangeClient(mode="paper", initial_balance=10000)
                self.log("📄 Initialized PAPER TRADING mode")
                
            elif trading_mode == "API (Binance)":
                # TODO: Get API keys from config
                self.log("⚠️ API mode requires Binance API keys in settings")
                self.log("Falling back to PAPER TRADING for now...")
                self.exchange_client = ExchangeClient(mode="paper", initial_balance=10000)
                
            elif trading_mode == "Browser":
                exchange = self.exchange_var.get().lower()
                self.log(f"🌐 Initializing BROWSER TRADING on {exchange.upper()}...")
                
                # Create browser trading client
                browser_client = BrowserTradingClient(self.agent, exchange)
                
                # Navigate to trading page
                async def setup_browser():
                    success = await browser_client.navigate_to_trading(symbol)
                    if success:
                        self.log(f"✅ Browser navigated to {symbol} trading page")
                    else:
                        self.log("❌ Failed to navigate to trading page")
                        return False
                    return True
                
                # Run async setup
                success = self.run_async(setup_browser())
                if not success:
                    self.log("Falling back to PAPER TRADING...")
                    self.exchange_client = ExchangeClient(mode="paper", initial_balance=10000)
                else:
                    self.exchange_client = browser_client
                    
        except Exception as e:
            self.log(f"❌ Error initializing trading client: {e}")
            self.log("Falling back to PAPER TRADING...")
            self.exchange_client = ExchangeClient(mode="paper", initial_balance=10000)
        
        self.trading_active = True
        
        # Update UI
        self.btn_start_trading.configure(state="disabled")
        self.btn_stop_trading.configure(state="normal")
        self.option_trading_mode.configure(state="disabled")
        self.option_exchange.configure(state="disabled")
        
        self.log(f"🚀 CRYPTO TRADER: Starting {trading_mode} trading on {symbol}")
        self.tts.speak(f"Starting {trading_mode} trading")
        
        # Start trading loop in thread
        threading.Thread(target=self._trading_loop, daemon=True).start()

    def stop_trading(self):
        """Stop automated trading"""
        self.trading_active = False
        self.btn_start_trading.configure(state="normal")
        self.btn_stop_trading.configure(state="disabled")
        self.option_trading_mode.configure(state="normal")
        
        # Re-enable exchange selector if in browser mode
        if self.trading_mode_var.get() == "Browser":
            self.option_exchange.configure(state="normal")
        
        self.crypto_log("CRYPTO TRADER: Trading stopped")
        self.tts.speak("Trading stopped")

    def emergency_stop(self):
        """Emergency stop - close all positions and halt trading"""
        self.trading_active = False
        
        # Close all positions
        current_prices = {self.current_symbol: self.exchange_client.get_price(self.current_symbol) or 0}
        for symbol in list(self.portfolio.positions.keys()):
            price = current_prices.get(symbol, 0)
            if price > 0:
                self.portfolio.close_position(symbol, price, "Emergency stop")
                self.log(f"EMERGENCY: Closed position in {symbol}")
        
        self.btn_start_trading.configure(state="normal")
        self.btn_stop_trading.configure(state="disabled")
        self.option_trading_mode.configure(state="normal")
        
        if self.trading_mode_var.get() == "Browser":
            self.option_exchange.configure(state="normal")
        
        self.crypto_log("🚨 EMERGENCY STOP ACTIVATED - ALL POSITIONS CLOSED")
        self.tts.speak("Emergency stop activated")
        self.update_trading_dashboard()

    def _trading_loop(self):
        """Main trading loop"""
        import time
        from datetime import datetime
        import random
        
        self.after(0, lambda: self.log(f"🚀 TRADING LOOP STARTED for {self.current_symbol}"))
        
        # Pre-populate price history for indicators to work
        base_price = 50000 if "BTC" in self.current_symbol else 3000
        self.after(0, lambda: self.log(f"📊 Initializing price history (base: ${base_price:,.0f})..."))
        
        # Add 50 historical prices with realistic movement
        for i in range(50):
            price = base_price * (1 + random.uniform(-0.01, 0.01))
            self.trading_engine.market_data.update_price(self.current_symbol, price)
            self.exchange_client.update_price(self.current_symbol, price)
            base_price = price  # Use last price as base for next
        
        self.after(0, lambda: self.log(f"✅ Price history initialized with 50 data points"))
        self.after(0, lambda: self.log(f"🔄 Starting live trading loop..."))
        
        iteration = 0
        while self.trading_active:
            try:
                iteration += 1
                
                # Generate new price with realistic movement
                current_price = self.trading_engine.market_data.current_prices.get(self.current_symbol, base_price)
                price = current_price * (1 + random.uniform(-0.02, 0.02))
                
                # Update market data
                self.trading_engine.market_data.update_price(self.current_symbol, price)
                self.exchange_client.update_price(self.current_symbol, price)
                
                # Log every 3rd iteration to avoid spam
                if iteration % 3 == 0:
                    self.after(0, lambda p=price, i=iteration: self.log(f"💹 Iteration {i}: Price ${p:,.2f}"))
                
                # Generate trading signal
                signal = self.trading_engine.analyze(self.current_symbol)
                
                if signal:
                    if signal.action in ["BUY", "SELL"]:
                        self.after(0, lambda s=signal: self.crypto_log(f"🎯 SIGNAL: {s.action} {s.symbol} @ ${s.price:,.2f} - {s.reason}"))
                        
                        # Check if we should execute
                        if signal.action == "BUY" and self.current_symbol not in self.portfolio.positions:
                            self._execute_buy(signal)
                        elif signal.action == "SELL" and self.current_symbol in self.portfolio.positions:
                            self._execute_sell(signal)
                    elif iteration % 5 == 0:  # Log HOLD signals occasionally
                        self.after(0, lambda s=signal: self.crypto_log(f"⏸️ {s.reason}"))
                else:
                    if iteration == 1:
                        self.after(0, lambda: self.log(f"⚠️ No signal generated - strategy may need more data"))
                
                # Check stop loss / take profit
                current_prices = {self.current_symbol: price}
                triggers = self.risk_manager.check_stop_loss_take_profit(current_prices)
                
                for symbol, trigger_type in triggers:
                    self._close_position(symbol, price, trigger_type)
                
                # Update dashboard
                self.after(0, self.update_trading_dashboard)
                
                # Wait before next iteration
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.after(0, lambda err=str(e), details=error_details: self.log(f"❌ TRADING ERROR: {err}\n{details}"))
                time.sleep(5)

    def _execute_buy(self, signal):
        """Execute buy order"""
        from datetime import datetime
        
        # Calculate position size
        quantity = self.risk_manager.calculate_position_size(signal.symbol, signal.price)
        
        # Validate trade
        current_prices = {signal.symbol: signal.price}
        valid, reason = self.risk_manager.validate_trade(signal.symbol, "BUY", quantity, signal.price, current_prices)
        
        if not valid:
            self.after(0, lambda r=reason: self.crypto_log(f"TRADE REJECTED: {r}"))
            return
        
        # Execute order
        success, msg, order = self.exchange_client.create_market_order(signal.symbol, "BUY", quantity)
        
        if success:
            # Create position
            stop_loss = self.risk_manager.calculate_stop_loss(signal.price, "LONG")
            take_profit = self.risk_manager.calculate_take_profit(signal.price, "LONG")
            
            position = Position(
                symbol=signal.symbol,
                side="LONG",
                entry_price=signal.price,
                quantity=quantity,
                entry_time=datetime.now(),
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            self.portfolio.add_position(position)
            self.after(0, lambda: self.log(f"BUY EXECUTED: {quantity:.4f} {signal.symbol} @ ${signal.price:.2f}"))
            self.after(0, lambda: self.tts.speak("Buy order executed"))
        else:
            self.after(0, lambda m=msg: self.crypto_log(f"BUY FAILED: {m}"))

    def _execute_sell(self, signal):
        """Execute sell order"""
        position = self.portfolio.positions.get(signal.symbol)
        if not position:
            return
        
        # Execute order
        success, msg, order = self.exchange_client.create_market_order(signal.symbol, "SELL", position.quantity)
        
        if success:
            trade = self.portfolio.close_position(signal.symbol, signal.price, signal.reason)
            if trade:
                pnl_msg = f"Profit {trade.pnl:.0f} dollars" if trade.pnl > 0 else f"Loss {abs(trade.pnl):.0f} dollars"
                self.after(0, lambda: self.log(f"SELL EXECUTED: {trade.quantity:.4f} {signal.symbol} @ ${signal.price:.2f} | P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)"))
                self.after(0, lambda: self.tts.speak(f"Sell order executed. {pnl_msg}"))
        else:
            self.after(0, lambda m=msg: self.crypto_log(f"SELL FAILED: {m}"))

    def _close_position(self, symbol, price, reason):
        """Close position (stop loss or take profit)"""
        trade = self.portfolio.close_position(symbol, price, reason)
        if trade:
            self.after(0, lambda: self.log(f"{reason.upper()}: Closed {symbol} @ ${price:.2f} | P&L: ${trade.pnl:.2f}"))
            self.after(0, lambda: self.tts.speak(f"{reason} triggered"))

    def update_trading_dashboard(self):
        """Update trading dashboard with current stats"""
        # Get current prices
        current_price = self.exchange_client.get_price(self.current_symbol) or 0
        current_prices = {self.current_symbol: current_price}
        
        # Update portfolio stats
        equity = self.portfolio.get_equity(current_prices)
        unrealized_pnl = self.portfolio.get_unrealized_pnl(current_prices)
        total_pnl = self.portfolio.total_pnl + unrealized_pnl
        return_pct = (total_pnl / self.portfolio.initial_balance) * 100
        
        self.lbl_balance.configure(text=f"Balance: ${self.portfolio.balance:,.2f}")
        self.lbl_equity.configure(text=f"Equity: ${equity:,.2f}")
        
        pnl_color = COLOR_SUCCESS if total_pnl >= 0 else COLOR_ERROR
        self.lbl_pnl.configure(text=f"Total P&L: ${total_pnl:,.2f} ({return_pct:.2f}%)", text_color=pnl_color)
        
        daily_color = COLOR_SUCCESS if self.portfolio.daily_pnl >= 0 else COLOR_ERROR
        self.lbl_daily_pnl.configure(text=f"Daily P&L: ${self.portfolio.daily_pnl:,.2f}", text_color=daily_color)
        
        self.lbl_positions.configure(text=f"Open Positions: {len(self.portfolio.positions)}")
        
        # Update positions display
        self.positions_display.configure(state="normal")
        self.positions_display.delete("0.0", "end")
        
        if self.portfolio.positions:
            for symbol, pos in self.portfolio.positions.items():
                pnl = pos.pnl(current_prices.get(symbol, pos.entry_price))
                pnl_pct = pos.pnl_percent(current_prices.get(symbol, pos.entry_price))
                pnl_sign = "+" if pnl >= 0 else ""
                self.positions_display.insert("end", f"{symbol} | {pos.side}\n")
                self.positions_display.insert("end", f"  Entry: ${pos.entry_price:.2f} | Qty: {pos.quantity:.4f}\n")
                self.positions_display.insert("end", f"  P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)\n")
                self.positions_display.insert("end", f"  SL: ${pos.stop_loss:.2f} | TP: ${pos.take_profit:.2f}\n\n")
        else:
            self.positions_display.insert("0.0", "No open positions")
        
        self.positions_display.configure(state="disabled")
        
        # Update trade history
        self.trade_history_display.configure(state="normal")
        self.trade_history_display.delete("0.0", "end")
        
        if self.portfolio.trade_history:
            for trade in reversed(self.portfolio.trade_history[-10:]):  # Last 10 trades
                pnl_sign = "+" if trade.pnl >= 0 else ""
                self.trade_history_display.insert("end", f"{trade.exit_time.strftime('%H:%M:%S')} | {trade.symbol} {trade.side}\n")
                self.trade_history_display.insert("end", f"  Entry: ${trade.entry_price:.2f} → Exit: ${trade.exit_price:.2f}\n")
                self.trade_history_display.insert("end", f"  P&L: {pnl_sign}${trade.pnl:.2f} ({pnl_sign}{trade.pnl_percent:.2f}%) | {trade.reason}\n\n")
        else:
            self.trade_history_display.insert("0.0", "No trades yet")
        
        self.trade_history_display.configure(state="disabled")


    def _setup_agent_tab(self):
        parent = self.tab_agent
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(parent, text="AGENTIC ORCHESTRATOR", font=("Consolas", 18, "bold"), text_color=COLOR_ACCENT).grid(row=0, column=0, pady=10)
        
        # Goal Entry Frame
        frame_goal = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
        frame_goal.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(frame_goal, text="COMPLEX GOAL / OBJECTIVE:", font=("Consolas", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_agent_goal = ctk.CTkTextbox(frame_goal, height=60, font=("Consolas", 12))
        self.entry_agent_goal.pack(fill="x", padx=10, pady=(0, 10))
        self.entry_agent_goal.insert("0.0", "Research latest AI agent news, save a summary to memory, and post a tweet about it.")
        
        # Controls
        frame_ctrl = ctk.CTkFrame(frame_goal, fg_color="transparent")
        frame_ctrl.pack(fill="x", padx=10, pady=(0, 10))
        
        self.btn_start_agent = ctk.CTkButton(frame_ctrl, corner_radius=8, text="🚀 INITIALIZE AGENT", command=self.start_agent_orchestrator, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="black", font=("Consolas", 12, "bold"))
        self.btn_start_agent.pack(side="left", padx=5)
        
        self.btn_stop_agent = ctk.CTkButton(frame_ctrl, corner_radius=8, text="⛔ STOP AGENT", command=self.stop_agent_orchestrator, fg_color=COLOR_ERROR, hover_color="#770022", text_color="white", state="disabled", font=("Consolas", 12, "bold"))
        self.btn_stop_agent.pack(side="left", padx=5)
        
        # Live Thoughts Console
        self.agent_console = ctk.CTkTextbox(parent, fg_color=COLOR_LOG, font=("Consolas", 12), corner_radius=10)
        self.agent_console.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Wire up callback
        def agent_ui_cb(msg, role):
            self.after(0, lambda: self._update_agent_console(msg, role))
        
        self.orchestrator.set_ui_callback(agent_ui_cb)

    def start_agent_orchestrator(self):
        if not self.use_ai:
            self._update_agent_console("ERROR: AI Provider not configured. Set API Key in Settings.", "error")
            return
            
        goal = self.entry_agent_goal.get("0.0", "end").strip()
        if not goal: return
        
        self.btn_start_agent.configure(state="disabled")
        self.btn_stop_agent.configure(state="normal")
        self.agent_console.delete("0.0", "end")
        
        self.run_async(self._agent_loop_task(goal))

    async def _agent_loop_task(self, goal):
        try:
            await self.orchestrator.execute_goal(goal)
        except Exception as e:
            self._update_agent_console(f"FATAL ORCHESTRATOR ERROR: {e}", "error")
            
        self.after(0, lambda: self.btn_start_agent.configure(state="normal"))
        self.after(0, lambda: self.btn_stop_agent.configure(state="disabled"))

    def stop_agent_orchestrator(self):
        self.orchestrator.stop()
        self.btn_stop_agent.configure(state="disabled")

    def _update_agent_console(self, msg, role):
        self.agent_console.configure(state="normal")
        color = "white"
        if role == "agent": color = COLOR_ACCENT
        elif role == "action": color = "yellow"
        elif role == "success": color = COLOR_SUCCESS
        elif role == "error": color = COLOR_ERROR
        elif role == "warning": color = "orange"
        
        self.agent_console.insert("end", f"[{role.upper()}] {msg}\n", role)
        self.agent_console.tag_config(role, foreground=color)
        self.agent_console.see("end")
        self.agent_console.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    #  BIZ SCRAPER TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_biz_scraper_tab(self):
        parent = self.tab_biz
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10,
                           border_color=COLOR_BORDER, border_width=1)
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr,
            text="🗂️  INTELLIGENT BUSINESS SCRAPER",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=COLOR_ACCENT
        ).grid(row=0, column=0, sticky="w", padx=20, pady=12)

        ctk.CTkLabel(
            hdr,
            text="Google Maps  ·  LinkedIn  ·  Instagram  →  Excel / CSV",
            font=("Consolas", 11),
            text_color=COLOR_GOLD
        ).grid(row=0, column=1, sticky="e", padx=20)

        # ── Control Panel ───────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10,
                            border_color=COLOR_BORDER, border_width=1)
        ctrl.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ctrl.grid_columnconfigure(1, weight=1)

        # Source selector (row 0)
        src_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        src_row.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=(12, 4))

        ctk.CTkLabel(src_row, text="DATA SOURCE:", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).pack(side="left", padx=(0, 12))

        self.biz_src_maps = ctk.CTkCheckBox(
            src_row, text="🗺  Google Maps",
            font=("Consolas", 11, "bold"), text_color=COLOR_ACCENT,
            checkmark_color=COLOR_ACCENT, fg_color=COLOR_ACCENT, hover_color=COLOR_PANEL2
        )
        self.biz_src_maps.pack(side="left", padx=10)
        self.biz_src_maps.select()

        self.biz_src_linkedin = ctk.CTkCheckBox(
            src_row, text="💼  LinkedIn",
            font=("Consolas", 11, "bold"), text_color="gray",
            checkmark_color="gray", fg_color="gray", hover_color=COLOR_PANEL2,
            state="disabled"
        )
        self.biz_src_linkedin.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(src_row, text="🔬 UNDER TESTING",
                     font=("Consolas", 8, "bold"), text_color="#ff9900",
                     fg_color="#1a1000", corner_radius=4).pack(side="left", padx=(2, 10))

        self.biz_src_instagram = ctk.CTkCheckBox(
            src_row, text="📸  Instagram",
            font=("Consolas", 11, "bold"), text_color="gray",
            checkmark_color="gray", fg_color="gray", hover_color=COLOR_PANEL2,
            state="disabled"
        )
        self.biz_src_instagram.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(src_row, text="🔬 UNDER TESTING",
                     font=("Consolas", 8, "bold"), text_color="#ff9900",
                     fg_color="#1a1000", corner_radius=4).pack(side="left", padx=(2, 10))

        self.biz_ai_enrich = ctk.CTkCheckBox(
            src_row, text="🧠  AI Enrich",
            font=("Consolas", 11, "bold"), text_color=COLOR_GOLD,
            checkmark_color=COLOR_GOLD, fg_color=COLOR_GOLD, hover_color=COLOR_PANEL2
        )
        self.biz_ai_enrich.pack(side="left", padx=20)

        # Query + max results (row 1)
        query_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        query_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=4)
        query_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(query_row, text="SEARCH QUERY:", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.biz_entry_query = ctk.CTkEntry(
            query_row,
            placeholder_text='e.g.  "restaurants in Lahore"  or  "#fashion"  or  "AI startup"',
            font=("Consolas", 12),
            fg_color=COLOR_LOG, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT, placeholder_text_color=COLOR_TEXT_DIM,
            height=36
        )
        self.biz_entry_query.grid(row=0, column=1, sticky="ew", padx=(0, 15))

        ctk.CTkLabel(query_row, text="MAX:", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).grid(row=0, column=2, sticky="e", padx=(0, 5))

        self.biz_max_results = ctk.CTkEntry(
            query_row, width=60, font=("Consolas", 12),
            fg_color=COLOR_LOG, border_color=COLOR_BORDER, text_color=COLOR_TEXT
        )
        self.biz_max_results.insert(0, "30")
        self.biz_max_results.grid(row=0, column=3, padx=(0, 5))

        # Action buttons (row 2)
        btn_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=3, sticky="ew", padx=15, pady=(4, 12))

        self.biz_btn_scrape = ctk.CTkButton(
            btn_row, text="▶  SCRAPE NOW", command=self._biz_start_scrape,
            corner_radius=8, height=38,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color="#000000", font=("Consolas", 13, "bold"), width=160
        )
        self.biz_btn_scrape.pack(side="left", padx=(0, 10))

        self.biz_btn_stop = ctk.CTkButton(
            btn_row, text="⏹  STOP", command=self._biz_stop_scrape,
            corner_radius=8, height=38,
            fg_color=COLOR_PANEL2, border_color=COLOR_ERROR, border_width=1,
            hover_color="#1a0010", text_color=COLOR_ERROR, font=("Consolas", 13, "bold"), width=100
        )
        self.biz_btn_stop.pack(side="left", padx=5)

        self.biz_status_lbl = ctk.CTkLabel(
            btn_row, text="● READY", font=("Consolas", 11, "bold"),
            text_color=COLOR_SUCCESS
        )
        self.biz_status_lbl.pack(side="left", padx=20)

        self.biz_count_lbl = ctk.CTkLabel(
            btn_row, text="0 records", font=("Consolas", 11),
            text_color=COLOR_TEXT_DIM
        )
        self.biz_count_lbl.pack(side="left", padx=5)

        # ── Main Body: Log + Results side by side ────────────────────────────
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Live scrape log
        log_frame = ctk.CTkFrame(body, fg_color=COLOR_PANEL,
                                  corner_radius=10, border_color=COLOR_BORDER, border_width=1)
        log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_frame, text="LIVE LOG", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w", padx=10, pady=6)

        self.biz_log_box = ctk.CTkTextbox(
            log_frame, font=("Consolas", 10),
            fg_color=COLOR_LOG, text_color=COLOR_SUCCESS,
            corner_radius=6, scrollbar_button_color=COLOR_PANEL2
        )
        self.biz_log_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.biz_log_box.insert("end", ">> SCRAPER READY.\n")
        self.biz_log_box.configure(state="disabled")

        # Results table
        results_frame = ctk.CTkFrame(body, fg_color=COLOR_PANEL,
                                      corner_radius=10, border_color=COLOR_BORDER, border_width=1)
        results_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        res_hdr = ctk.CTkFrame(results_frame, fg_color="transparent")
        res_hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(res_hdr, text="RESULTS TABLE", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).pack(side="left")

        self.biz_results_table = ctk.CTkScrollableFrame(
            results_frame, fg_color=COLOR_LOG,
            corner_radius=6, scrollbar_button_color=COLOR_PANEL2
        )
        self.biz_results_table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.biz_results_table.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._biz_draw_table_header()

        # ── Export Panel ─────────────────────────────────────────────────────
        export_frame = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10,
                                     border_color=COLOR_BORDER, border_width=1)
        export_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        export_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(export_frame, text="EXPORT:", font=("Consolas", 11, "bold"),
                     text_color=COLOR_TEXT_DIM).grid(row=0, column=0, sticky="w", padx=15, pady=10)
























                                                                                            
                                                                                    
                                                                                    
        self.biz_export_path = ctk.CTkEntry(
            export_frame,
            placeholder_text="Save path (e.g. C:\\Users\\Me\\Desktop\\businesses.xlsx)",
            font=("Consolas", 11), fg_color=COLOR_LOG, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT, placeholder_text_color=COLOR_TEXT_DIM
        )
        self.biz_export_path.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(
            export_frame, text="📊 EXCEL (.xlsx)",
            command=self._biz_export_excel,
            corner_radius=8, height=34,
            fg_color=COLOR_SUCCESS, hover_color="#007744",
            text_color="#000", font=("Consolas", 11, "bold"), width=140
        ).grid(row=0, column=2, padx=5, pady=10)

        ctk.CTkButton(
            export_frame, text="📄 CSV",
            command=self._biz_export_csv,
            corner_radius=8, height=34,
            fg_color=COLOR_PANEL2, border_color=COLOR_ACCENT, border_width=1,
            hover_color=COLOR_PANEL, text_color=COLOR_ACCENT,
            font=("Consolas", 11, "bold"), width=80
        ).grid(row=0, column=3, padx=(0, 15), pady=10)

    # ── BIZ SCRAPER: Internal helpers ──────────────────────────────────────────

    def _biz_log(self, msg: str):
        """Append a message to the live log textbox."""
        try:
            self.biz_log_box.configure(state="normal")
            self.biz_log_box.insert("end", f"{msg}\n")
            self.biz_log_box.see("end")
            self.biz_log_box.configure(state="disabled")
        except Exception:
            pass

    def _biz_draw_table_header(self):
        """Draw the results table column headers."""
        headers = ["#", "Name", "Category", "Address / Platform", "Rating / Followers", "Phone", "Website / URL"]
        widths   = [30,  140,   110,         160,                  90,                   100,     180]
        for col, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(
                self.biz_results_table,
                text=h,
                font=("Consolas", 10, "bold"),
                text_color=COLOR_ACCENT,
                fg_color=COLOR_PANEL2,
                corner_radius=4,
                width=w
            )
            lbl.grid(row=0, column=col, padx=2, pady=2, sticky="ew")

    def _biz_populate_table(self, records: list):
        """Refresh the results table with scraped records."""
        # Clear existing rows (keep header row=0)
        for widget in self.biz_results_table.winfo_children():
            info = widget.grid_info()
            if info and int(info.get("row", 0)) > 0:
                widget.destroy()

        # Columns to display in the table
        DISPLAY = ["Name", "Category", "Address", "Rating", "Phone", "Website"]
        widths   = [140,   110,        160,        90,       100,     180]

        for row_idx, rec in enumerate(records, start=1):
            row_bg = COLOR_PANEL2 if row_idx % 2 == 0 else COLOR_LOG

            # Row number
            ctk.CTkLabel(
                self.biz_results_table, text=str(row_idx),
                font=("Consolas", 9), text_color=COLOR_TEXT_DIM,
                fg_color=row_bg, width=30
            ).grid(row=row_idx, column=0, padx=2, pady=1, sticky="ew")

            for col_idx, (field, w) in enumerate(zip(DISPLAY, widths), start=1):
                val = rec.get(field, "") or rec.get("Followers", "") or ""
                # For review/followers column, prefer rating then followers
                if field == "Rating" and not val:
                    val = rec.get("Followers", "")
                # For website, prefer website then LinkedIn then Instagram
                if field == "Website" and not val:
                    val = rec.get("LinkedIn", "") or rec.get("Instagram", "")

                display_val = str(val)[:40] if val else "—"
                ctk.CTkLabel(
                    self.biz_results_table, text=display_val,
                    font=("Consolas", 9), text_color=COLOR_TEXT,
                    fg_color=row_bg, width=w, anchor="w"
                ).grid(row=row_idx, column=col_idx, padx=2, pady=1, sticky="ew")

        # Update count label
        src_tags = list(set(r.get("Source", "?") for r in records))
        self.biz_count_lbl.configure(text=f"{len(records)} records  [{', '.join(src_tags)}]")

    def _biz_start_scrape(self):
        """Launch the scrape in a background thread."""
        query = self.biz_entry_query.get().strip()
        if not query:
            self._biz_log("[ERROR] Please enter a search query.")
            return

        try:
            max_r = int(self.biz_max_results.get().strip())
        except ValueError:
            max_r = 30

        sources = []
        if self.biz_src_maps.get():     sources.append("maps")
        if self.biz_src_linkedin.get(): sources.append("linkedin")
        if self.biz_src_instagram.get(): sources.append("instagram")

        if not sources:
            self._biz_log("[ERROR] Select at least one data source.")
            return

        # Check browser
        if not getattr(self.agent, "page", None):
            self._biz_log("[ERROR] Browser not started. Click 'INITIALIZE BROWSER' first (Command Center).")
            return

        self.biz_btn_scrape.configure(state="disabled")
        self.biz_status_lbl.configure(text="● SCRAPING…", text_color=COLOR_WARN)
        self.biz_scraper._stop_requested = False
        self._biz_results = []

        do_enrich = bool(self.biz_ai_enrich.get()) and self.use_ai

        threading.Thread(
            target=self._biz_scrape_thread,
            args=(query, max_r, sources, do_enrich),
            daemon=True
        ).start()

    def _biz_scrape_thread(self, query, max_r, sources, do_enrich):
        """Background thread that runs the async scrape coroutines."""
        import asyncio

        async def run():
            records = []
            if "maps" in sources:
                maps_records = await self.biz_scraper.scrape_google_maps(query, max_r)
                records.extend(maps_records)
            if "linkedin" in sources:
                linkedin_records = await self.biz_scraper.scrape_linkedin_companies(query, max_r)
                records.extend(linkedin_records)
            if "instagram" in sources:
                insta_records = await self.biz_scraper.scrape_instagram_profiles(query, max_r)
                records.extend(insta_records)
            return records

        try:
            records = asyncio.run_coroutine_threadsafe(run(), self.loop).result(timeout=300)
        except Exception as e:
            self.after(0, lambda: self._biz_log(f"[FATAL] {e}"))
            records = []

        if do_enrich and records:
            self._biz_log("[AI] Starting AI enrichment pass...")
            records = self.biz_scraper.enrich_with_ai(records)

        self._biz_results = records
        self.after(0, lambda: self._biz_populate_table(records))
        self.after(0, lambda: self.biz_status_lbl.configure(
            text=f"● DONE  ({len(records)} results)", text_color=COLOR_SUCCESS
        ))
        self.after(0, lambda: self.biz_btn_scrape.configure(state="normal"))

    def _biz_stop_scrape(self):
        self.biz_scraper.stop()
        self.biz_status_lbl.configure(text="● STOPPING…", text_color=COLOR_ERROR)
        self._biz_log("[USER] Stop requested.")

    def _biz_export_excel(self):
        import os
        from tkinter import filedialog
        from datetime import datetime
        
        if not self._biz_results:
            self._biz_log("[EXPORT] No data to export. Run a scrape first.")
            return

        # Smart desktop path resolution (OneDrive support)
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "OneDrive", "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.join(home, "Desktop")
            
        fname = f"businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Interactive file dialog
        path = filedialog.asksaveasfilename(
            title="Save Excel Data",
            initialdir=desktop,
            initialfile=fname,
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("All Files", "*.*")]
        )
        
        if not path:
            return  # User cancelled

        # Update input box with chosen path for transparency
        self.biz_export_path.delete(0, 'end')
        self.biz_export_path.insert(0, path)

        ok = self.biz_scraper.export_to_excel(self._biz_results, path)
        if ok:
            self.biz_status_lbl.configure(text="● EXPORTED ✓", text_color=COLOR_SUCCESS)
        else:
            self.biz_status_lbl.configure(text="● EXPORT FAILED", text_color=COLOR_ERROR)

    def _biz_export_csv(self):
        import os
        from tkinter import filedialog
        from datetime import datetime
        
        if not self._biz_results:
            self._biz_log("[EXPORT] No data to export. Run a scrape first.")
            return

        home = os.path.expanduser("~")
        desktop = os.path.join(home, "OneDrive", "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.join(home, "Desktop")
            
        fname = f"businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Interactive file dialog
        path = filedialog.asksaveasfilename(
            title="Save CSV Data",
            initialdir=desktop,
            initialfile=fname,
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")]
        )
        
        if not path:
            return  # User cancelled

        # Update input box with chosen path for transparency
        self.biz_export_path.delete(0, 'end')
        self.biz_export_path.insert(0, path)

        ok = self.biz_scraper.export_to_csv(self._biz_results, path)
        if ok:
            self.biz_status_lbl.configure(text="● CSV EXPORTED ✓", text_color=COLOR_SUCCESS)
        else:
            self.biz_status_lbl.configure(text="● EXPORT FAILED", text_color=COLOR_ERROR)

if __name__ == "__main__":

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
