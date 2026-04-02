# Neural Automater V2 — Complete Installation & User Guide

> **The world's most advanced personal AI agent for Windows.**  
> It controls your browser, your PC, reads your files, monitors your screen, and never forgets you — all locally and in real time.

---

## Table of Contents
1. [System Requirements](#1-system-requirements)
2. [Installation — Step by Step](#2-installation--step-by-step)
3. [First Launch & Configuration](#3-first-launch--configuration)
4. [Tab-by-Tab Feature Guide](#4-tab-by-tab-feature-guide)
   - [COMMAND CENTER](#command-center)
   - [NEURAL CHAT](#neural-chat)
   - [SCHEDULER](#scheduler)
   - [ACCOUNTS](#accounts)
   - [SOCIAL MEDIA PRO](#social-media-pro)
   - [WHATSAPP PRO](#whatsapp-pro)
   - [DATA LAB](#data-lab)
   - [CRYPTO TRADER](#crypto-trader)
   - [AGENT LAB](#agent-lab)
   - [SYSTEM SETTINGS](#system-settings)
5. [V2 Features Deep Dive](#5-v2-features-deep-dive)
6. [Troubleshooting](#6-troubleshooting)
7. [Safety & Best Practices](#7-safety--best-practices)

---

## 1. System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.10 | 3.11 |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 2 GB free | 5 GB free |
| **Internet** | Required for AI APIs | Broadband |
| **Microphone** | Optional (Voice Mode) | Any USB mic |

---

## 2. Installation — Step by Step

### Step 1: Install Python 3.11
1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.11.x** (NOT 3.13+)
3. Run the installer. **CRITICAL**: ✅ Check **"Add Python to PATH"** before clicking Install

Verify in **PowerShell**:
```powershell
python --version
# Expected: Python 3.11.x
```

---

### Step 2: Open the Project Folder
Open **PowerShell** and navigate to the project:
```powershell
cd C:\Users\naqas\OneDrive\Desktop\Prog\neural-automater
```

---

### Step 3: Create a Virtual Environment
```powershell
python -m venv venv
```
Activate it:
```powershell
.\venv\Scripts\Activate.ps1
```
> If you get an "execution policy" error, run: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

### Step 4: Install All Dependencies
```powershell
pip install -r requirements.txt
pip install chromadb PyPDF2 python-docx pyautogui mss
```

Install the Playwright browser engine (Chromium):
```powershell
playwright install chromium
```

---

### Step 5: (Optional) Install PyAudio for Voice Commands
PyAudio requires a special build for Windows. Run:
```powershell
pip install pipwin
pipwin install pyaudio
```

---

### Step 6: Launch the Application
```powershell
python gui_app.py
```

---

## 3. First Launch & Configuration

When the app opens, go to the **SYSTEM SETTINGS** tab first.

### Setting Up Your AI Provider (Choose ONE)

#### Option A: Google Gemini (Recommended — Free Tier Available)
1. Visit [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create a free API key
3. In **SYSTEM SETTINGS**, paste your key in the **"Gemini API Key"** field
4. Select **"gemini"** as the LLM Provider
5. Click **SAVE CONFIGURATION**

#### Option B: Ollama (100% Local, Free, No Internet Needed)
1. Download Ollama from [https://ollama.com/download](https://ollama.com/download)
2. Install and run it. In PowerShell:
   ```powershell
   ollama pull llava:latest    # Vision model (required for screenshots)
   ollama pull llama3.1:latest # Optional text model
   ```
3. In **SYSTEM SETTINGS**, select **"ollama"** as provider
4. Enter model name: `llava:latest`
5. Click **SAVE CONFIGURATION**

#### Option C: OpenRouter (Access GPT-4, Claude, Gemini with one key)
1. Get a key at [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. In **SYSTEM SETTINGS**, paste key in **"OpenRouter API Key"**
3. Set provider to **"openrouter"**
4. Set model (e.g., `google/gemini-2.0-flash-001`)

---

## 4. Tab-by-Tab Feature Guide

---

### COMMAND CENTER
The main control hub and intelligence console.

**Controls explained:**
| Control | What It Does |
|---|---|
| **INITIALIZE BROWSER** | Launches a background Chromium browser the AI can control |
| **TERMINATE SESSION** | Safely closes the AI browser session |
| **SAVE SEQUENCE** | Records the last set of browser actions to replay later |
| **EXECUTE REPLAY** | Replays the last saved browser sequence |
| **🤖 AUTO-PILOT** | When checked, the AI will plan multi-step goal loops autonomously |
| **⚡ GOD MODE** | Enables physical mouse/keyboard control of your whole PC |
| **👁️ VISION AI** | Activates proactive screen monitoring (AI watches and suggests) |

**How to type a command:**
1. Type your goal in the bottom input box
2. Press **ENTER** or click **EXECUTE**
3. Watch the console log show the AI's real-time thoughts

**Example commands:**
```
Go to google.com and search for Python tutorials
Open notepad and type Hello World then save it
Find my documents folder and list all PDF files
```

---

### NEURAL CHAT
A direct LLM chat interface — like ChatGPT, but private and running your API.

- Type a question and press **Send** or **Enter**
- The AI responds in the chat window
- No memory persistence (clears on restart) — see AGENT LAB for persistent sessions

---

### SCHEDULER
Automate tasks to run at specific times or intervals.

**How to add a task:**
1. Enter a task description (e.g., `Post a tweet about AI`)
2. Set the time or interval
3. Click **ADD TO SCHEDULE**
4. The scheduler runs in the background automatically

---

### ACCOUNTS
Manage login credentials for automated tasks.

- Add social media accounts for auto-posting
- Credentials are stored encrypted locally using the `cryptography` library
- Never stored in plain text

---

### SOCIAL MEDIA PRO
Automates Twitter/X engagement.

**Twitter Auto-Comment Bot:**
1. Enter your **Keywords** (e.g., `Iran war, AI news, Bitcoin`)
2. Set the **System Prompt** (e.g., `You are a geopolitical expert. Add insightful commentary`)
3. Set **Max Replies per Run** (e.g., `5`)
4. Set **Daily Limit** (e.g., `20`)
5. Click **▶ START BOT**

The bot will:
- Log into Twitter via Playwright automatically
- Search for live tweets matching your keywords
- Read each tweet and craft a unique reply using the AI
- Post the reply and log the tweet ID so it is never replied to twice

**Tips for best results:**
- Keep your keywords specific
- Use a detailed system prompt for your desired persona
- Start with a low Daily Limit (5-10) to test before scaling

---

### WHATSAPP PRO
AI-powered WhatsApp Web automation.

#### Sending a Manual Message
1. Enter the contact name in **Target Contact**
2. Type the message
3. Click **SEND MESSAGE**

#### AI Auto-Responder Bot ⚡
The bot will automatically reply to **unread WhatsApp messages** using AI.

**Setup:**
1. Enter your **bot persona** in the System Prompt box  
   *Example:* `You are a helpful sales assistant for Zakria Sons. Always be polite and professional.`
2. Click **▶ START AUTO-RESPONDER**

**What happens:**
- WhatsApp Web opens in a background browser
- Scan the QR code once with your phone (this is a one-time step per session)
- The bot scans the chat list every 30 seconds for unread messages
- When it finds a new unread message, it:
  1. Opens the conversation
  2. Reads the last 5 messages for full context
  3. Generates an appropriate, context-aware reply
  4. Sends the reply automatically

---

### DATA LAB
Data extraction and analysis.

- Scrape data from websites using natural language commands
- Load CSV/Excel files and ask the AI to analyze them
- Export results as CSV

---

### CRYPTO TRADER
Paper trading and live market monitoring.

- Connect Binance API keys for live data
- Set trading strategy (SMA, EMA, RSI, etc.)
- Run paper trading simulations before going live
- Monitor portfolio P&L in real time

> ⚠️ **WARNING**: Never use real funds without thorough testing. Start with Paper Mode only.

---

### AGENT LAB
The most advanced interface — runs the full **Multi-Agent Swarm**.

**How to use:**
1. Type a complex, multi-step goal in the input box
2. Press **EXECUTE GOAL**
3. Watch as the Supervisor AI breaks it down and dispatches specialist agents

**Example powerful goals:**
```
Search Google for the latest price of gold, then write a Python script
that calculates my profit if I bought 10 grams at $1800, and save it to my Desktop.
```

```
Go to my GitHub profile, find the latest commit message on my neural-automater repo,
then post a tweet announcing the update.
```

**Agent roles:**
| Agent | Specialization |
|---|---|
| **Supervisor** | Plans goals, routes tasks to specialists |
| **CoderAgent** | Reads/writes files, executes terminal commands |
| **BrowserAgent** | Navigates websites, scrapes data |
| **OSAgent** | Controls mouse, keyboard, opens apps physically |

---

### SYSTEM SETTINGS
Configure API keys, LLM providers, and visual preferences.

- **API Key / Provider**: Set your Gemini, Ollama, or OpenRouter key
- **Save Configuration**: Persists settings to `config.json` for next launch

---

## 5. V2 Features Deep Dive

### 🧠 Long-Term Memory
The AI learns about you permanently. There is no "clear history" between sessions.

**How to teach it facts:**
In the Command Center, just say:
```
Remember that my name is Naqash and I run a business called Zakria Sons.
```
The AI calls `ltm_memorize` automatically. On the next session, you do NOT need to repeat this — the AI will recall it from the vector database before answering any question.

**How memory is stored:**  
Facts are stored in the `memory_vault/` subdirectory as a local ChromaDB SQLite vector database. You can delete this folder to fully reset the AI's memory.

---

### 📚 Universal File RAG (Document Search)
You can ask the AI to find and read ANY document on your PC — without opening it.

**First, index a folder:**
```
Please index my Documents folder: C:/Users/naqas/Documents
```
(The AI does this automatically if you tell it to)

**Then search it:**
```
Search my documents for anything about the Q3 2024 financial report
```

**Supported formats:** `.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json`, `.py`, `.html`

---

### 👁️ Real-Time Vision AI
Every 10 seconds, the AI silently takes a screenshot and analyzes what you are doing.

**Activate by checking**: `👁️ VISION AI` checkbox in Command Center

**What it does:**
- If you have a **code error** visible on screen → the popup suggests the fix
- If you are paused on a **confusing UI** → it explains what to click
- If everything looks normal → it stays silent (shows `IDLE` internally)

**The toast popup** appears bottom-right of your screen and vanishes after 10 seconds.

---

### 🐝 Multi-Agent Swarm
For complex tasks requiring multiple skills, the Supervisor AI delegates to specialists.

**Delegation flow:**
```
User Goal → Supervisor analyzes → Breaks into sub-tasks → Dispatches agents → Collects results → Reports back
```

This means a task like *"Research a topic and write a Python tool about it"* won't get confused — the Browser searches, then hands the research to the Coder to write the script.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: customtkinter` | Run `pip install customtkinter` |
| `ModuleNotFoundError: chromadb` | Run `pip install chromadb` |
| `Playwright browser not found` | Run `playwright install chromium` |
| `pyaudio` install fails | Run `pipwin install pyaudio` |
| `WhatsApp bot stuck at QR code` | Scan the QR code in the opened Chromium window using your phone's WhatsApp |
| `Twitter bot finds 0 tweets` | Ensure you are logged into Twitter in the Playwright window that opens |
| `Vision AI shows nothing` | Ensure Pillow is installed: `pip install Pillow` |
| `Memory not working` | Check that `memory_vault/` folder exists in the project directory |
| App crashes on startup | Run `pip install -r requirements.txt` again and check Python version is 3.11 |

---

## 7. Safety & Best Practices

> ⚠️ **GOD MODE is a powerful and potentially dangerous feature.**

- **Fail-safe**: Slam your mouse rapidly into any corner of the screen. PyAutoGUI has a built-in safety trigger that immediately aborts all AI actions.
- **Always supervise** the AI when using GOD MODE for the first time with a new task.
- **Never** store real passwords unless you understand the local encryption implementation.
- **Start with Paper Trading** in the Crypto Trader before connecting any real exchange.
- The Twitter Auto-Comment bot can result in account limitations if used aggressively. Always start with a daily limit of **5-10 replies**.
- WhatsApp automation may violate WhatsApp's Terms of Service. Use responsibly and for personal/business productivity only.

---

*Neural Automater V2 — Built with Python, Playwright, ChromaDB, PyAutoGUI, and Google Gemini.*
