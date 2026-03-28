# 🧠 Neural Automater // God Mode Edition

Neural Automater is a powerful, autonomous, AI-driven desktop application built in Python. It seamlessly fuses Local and Cloud Large Language Models (LLMs) with deep OS-level environment control ("God Mode") and advanced browser automation (Playwright).

From securely navigating your file system, to automating WhatsApp messages, generating viral social media posts, and running self-correcting agentic loops—Neural Automater acts as a true digital employee.

---

## 🚀 Key Features

### ⚡ God Mode (Total OS Control)
- **Physical Integration**: Replaces standard web-only automation with total PC control using PyAutoGUI and Subprocess.
- **Filesystem & Shell**: Tell the AI to `create a folder on my desktop`, `check my C: drive`, or `launch calculator`, and it executes native OS directory scans and shell commands dynamically.
- **Physical Automation**: Physically controls your mouse cursor and keyboard when traditional DOM selectors fail or when interacting with non-web desktop applications.

### 🤖 Intelligent Execution Modes
- **Single-Shot Manual**: Type a command (e.g., `go to youtube and search for python tutorials`). The AI generates an instant sequence plan and executes it flawlessly.
- **Auto-Pilot Loop**: The AI takes over. It looks at a screenshot of your screen, decides the next logical step, executes the action, verifies the outcome via another screenshot, and repeats until the goal is achieved.
- **Voice (VOX) Command**: Speak naturally to your AI via your microphone (`🎤 VOX: LIVE`) using integrated Speech Recognition. It natively replies using TTS (Text-to-Speech) vocal synthesis.

### 📡 Multi-LLM Provider Support
Freedom to choose the AI brain that powers your workflows:
- **Google Gemini (Cloud)**: Blazing fast, top-tier multimodal vision capabilities.
- **Ollama (True Local)**: 100% private, offline AI. We recommend `llama3.2-vision` for optimal Auto-Pilot capabilities on an 8GB GPU, or `qwen2.5-coder:7b` for God Mode scripting.
- **OpenRouter (Cloud Hub)**: Seamless connection to 100+ models (Claude, Llama 3, OpenAI) with a robust automatic fallback mechanism for text-only models.

### 💼 Dedicated Professional Tools
1. **WhatsApp Pro**: Built-in, ultra-reliable auto-messaging engine. Automatically formats phone numbers, handles slow WhatsApp Web load times, and includes an AI responder to generate perfect messages from short contexts.
2. **Social Media Pro**: Fully automated Twitter/X and LinkedIn bot. Provide a topic, and the engine researches live Google/Reddit trends, generates viral content (matching your selected "Vibe"), and automatically navigates and posts to your feed. It includes an **Advanced Comment Bot** capable of finding Tweets by keywords and replying empathetically to up to 20 daily targets.
3. **Data Extraction Lab**: Scrape elements off web pages instantly. Provide a URL and your target CSS fields (like `Name=h2`, `Price=.price`), and export to CSV/JSON rapidly.
4. **Task Scheduler**: Automate completely! Schedule specific Auto-Pilot goals or pre-recorded macros to trigger automatically at a specific time (e.g., `14:30`).
5. **Memory Module (Macros)**: Record a sequence of successful AI actions and save them to disk. Replay them anytime with one click.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9, 3.10, or 3.11.
- Ensure your terminal (or Command Prompt) is running with Administrator privileges for deep OS ("God Mode") capability.

### 1. Clone & Install
```bash
git clone https://github.com/your-repo/neural-automater.git
cd neural-automater

# It's highly recommended to use a virtual environment:
python -m venv venv
venv\Scripts\activate

# Install Core Requirements
pip install -r requirements.txt

# Install Playwright Browsers (Required for web automation!)
playwright install
```

### 2. Configure Your AI Brain
Before you can run Auto-Pilot, you need an LLM. 
- **Option A (Google Gemini API - Easiest):** Get a free API key from Google AI Studio. 
- **Option B (Ollama - Local & Private):** Download [Ollama](https://ollama.com/), open a terminal, and type `ollama run llama3.2-vision`.

### 3. Launch
```bash
python gui_app.py
```
*(On first load, head immediately to the **SYSTEM SETTINGS** tab to select your Provider and paste your API key).*

---

## 🕹️ How to Use Neural Automater

### Basic Web Navigation
1. Go to **Command Center**.
2. Make sure the ⚡ **God Mode** box is **UNCHECKED**. (By default, it will use the internal, invisible Playwright browser engine).
3. Type: `open youtube and search for coding tutorials`.
4. Hit **EXECUTE**. The browser will pop up and run your workflow automatically.

### Enabling God Mode (System Automation)
1. Check the ⚡ **God Mode** box in the Command Center.
2. Type an OS prompt: `check what is inside my C:\ drive` or `create a folder called Projects on my desktop`.
3. Hit **EXECUTE**. The LLM will now interpret your command and execute physical `os_list_dir` or `os_run_command` tools in the terminal window, printing the results directly to the GUI log! 
*(Note: Be careful in God Mode! The AI has direct access to run shell scripts. Use a Local LLM if working with highly sensitive folders).*

### Advanced Auto-Pilot
1. Check the 🤖 **AUTO-PILOT** box.
2. Type a highly complex objective: `find a cheap flight to Tokyo on Expedia`.
3. Hit **EXECUTE**. 
4. The system will enter a loop: it takes a screenshot of the browser, sends it to the AI, analyzes the DOM elements, clicks the correct buttons, waits for the page to load, and repeats this cycle up to 20 times until it mathematically proves the user goal states "completed: true".
5. Click the red ⏹ **STOP** button anytime to interrupt the AI.

### WhatsApp Automation
1. Log into your WhatsApp once using the **Accounts** tab or by running the browser manually. Once logged in, your session is saved locally!
2. Go to the **WhatsApp Pro** tab.
3. Enter a target (e.g., `+1234567890`).
4. Enter context (e.g., `Remind them about the meeting at 4 PM`).
5. Click **GENERATE & SEND AI MESSAGE**. The app will compose the text, navigate the hurdles of WhatsApp Web, and safely dispatch your message.

---

## ⚠️ Known Limitations & Safety
- **Failsafe**: When God Mode is manually controlling your physical mouse, you can violently drag your mouse to any of the 4 absolute corners of your physical monitor to trigger a `PyAutoGUI FailSafeException` and instantly abort the script.
- **OpenRouter Vision**: If you use OpenRouter with a model that *does not* support images (like `nemotron:free`), the app's advanced fallback system will automatically detect the failure, strip the screenshot, and process your request via pure text. However, Auto-Pilot *requires* vision, so use an appropriate model (like `google/gemini-2.0-flash` or `llava`) for Auto-Pilot.

---
*Built with Python, CustomTkinter, Playwright, and pure Agentic reasoning.*
