# 🧠 Neural Automater

**Neural Automater** is a powerful, AI-driven browser automation tool that allows you to control your web browser using natural language voice or text commands. It leverages advanced LLMs (Google Gemini or Local Ollama) to understand your intent, analyze the screen visually, and execute complex workflows automatically.

![Neural Automater](https://via.placeholder.com/800x400?text=Neural+Automater+UI)

---

## ✨ Key Features

### 🤖 AI Intelligence
- **Dual AI Support**: Use **Google Gemini** (Cloud) for speed and accuracy, or **Ollama** (Local) for privacy and offline use.
- **Vision Capabilities**: The AI "sees" the browser page to find buttons, forms, and layout elements dynamically.
- **Smart Reasoning**: Understands complex commands like "Search for X and click the first result".

### 🚀 Automation Modes
- **Voice Command**: Speak naturally to control the browser (e.g., "Open YouTube and play jazz").
- **Text Command**: Type instructions directly.
- **🤖 Auto-Pilot**: A continuous loop where the AI observes, decides, and acts until a goal is achieved (e.g., "Log into Gmail and find unread emails").

### 🛠️ Advanced Controls
- **Mouse Control**: Click at coordinates, hover, right-click, double-click, and drag-and-drop.
- **Keyboard Control**: Press specific keys (Enter, Esc, Tab, Shortcuts).
- **Text Extraction**: Read text from elements or the entire page.
- **Clipboard**: Copy and paste data automatically.
- **Auto-Reply**: Monitor chats (WhatsApp, Email) and generate context-aware replies.

### 📼 Recording & Replay
- **Record**: Save your automation sessions automatically.
- **Replay**: Execute saved workflows later.
- **Library**: Manage your automation scripts.

### 🕵️ Stealth Mode
- **Anti-Detection**: Built-in stealth features to bypass bot detection on major websites.

---

## 📥 Installation

### Prerequisites
- **Python 3.8+**
- **Google Chrome** (or Chromium)
- **Microphone** (for voice commands)

### Setup Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/neural-automater.git
    cd neural-automater
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browsers**
    ```bash
    playwright install
    ```

---

## ⚙️ Configuration

Launch the application:
```bash
python gui_app.py
```

Go to the **SYSTEM SETTINGS** tab to configure your AI provider.

### Option A: Google Gemini (Recommended for Speed)
1.  Get a free API Key from [Google AI Studio](https://makersuite.google.com/app/apikey).
2.  Select **"Google Gemini (Cloud)"**.
3.  Paste your API Key.
4.  Click **"TEST CONNECTION & SAVE"**.

### Option B: Ollama (Local & Private)
1.  Install [Ollama](https://ollama.ai).
2.  Pull a vision-capable model (required for Auto-Pilot):
    ```bash
    ollama pull llava:7b
    # OR for better reasoning (no vision):
    ollama pull deepseek-r1:7b
    # OR for best local balance:
    ollama pull qwen2-vl:7b
    ```
3.  Start Ollama: `ollama serve`.
4.  In the app, select **"Ollama (Local)"**.
5.  Enter your model name (e.g., `llava:7b`).
6.  Click **"SAVE & CONNECT"**.

---

## 🎮 Usage Guide

### Basic Commands
- **Navigation**: "Go to google.com", "Open YouTube".
- **Interaction**: "Click the search button", "Type 'Hello' in the box".
- **Scrolling**: "Scroll down", "Scroll to bottom".

### Auto-Pilot Mode
1.  Check the **"🤖 AUTO-PILOT"** box.
2.  Give a high-level goal: *"Go to Amazon, search for 'gaming mouse', and sort by price."*
3.  The AI will execute step-by-step, observing the screen after each action.

### Mouse & Keyboard
- **Click Coordinates**: "Click at 500, 300".
- **Right Click**: "Right click the image".
- **Hover**: "Hover over the menu".
- **Shortcuts**: "Press Control+T", "Press Enter".

### Text & Auto-Reply
- **Extract**: "Get text from the first paragraph", "Copy all prices".
- **Auto-Reply**: "Monitor WhatsApp and reply to new messages with 'I'll be right back'".

---

## 📂 File Structure

- `gui_app.py`: Main application GUI and logic.
- `browser_agent.py`: Handles Playwright browser automation (clicks, navigation, stealth).
- `llm_provider.py`: Abstraction layer for Gemini and Ollama.
- `prompts.py`: System prompts defining AI behavior.
- `voice_commander.py`: Speech-to-text handling.
- `recordings/`: Saved automation scripts.

---

## 🔧 Troubleshooting

**1. "Ollama Error: Connection refused"**
- Ensure Ollama is running (`ollama serve`).
- Check if the model is downloaded (`ollama list`).

**2. AI is not clicking the right button**
- Try describing the button more clearly (e.g., "Click the blue 'Submit' button").
- Use Auto-Pilot mode so the AI can "see" the page.

**3. "Browser not started"**
- The browser launches automatically with your first command. Say "Open Google" to start.

---

## 📜 License
MIT License. Feel free to modify and use for your own projects!
