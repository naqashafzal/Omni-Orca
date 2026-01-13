# Neural Automater 🤖

A futuristic, AI-powered autonomous browser agent capable of controlling a web browser via Voice, Text, or Vision commands.

## Features

-   **🤖 AI-Powered**: Uses Google Gemini Pro/Flash for natural language understanding.
-   **👁️ Vision Capable**: "See" the screen to find buttons and read text (Multimodal).
-   **🗣️ Voice Control**: Continuous voice command loop ("Start Listening" / "Stop Listening").
-   **🎭 Personas**: Switch modes between "General", "Social Media Manager", and "Crypto Trader".
-   **🖥️ Cyberpunk GUI**: Modern, dark-themed interface built with `customtkinter`.
-   **📼 Recorder**: Record and replay automation sequences.

## Installation

1.  **Clone the repo**
    ```bash
    git clone https://github.com/yourusername/automater.git
    cd automater
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  **Run the App**
    ```bash
    python gui_app.py
    ```

## Usage

1.  **Setup Keys**: Go to the **SYSTEM SETTINGS** tab and enter your [Gemini API Key](https://aistudio.google.com/).
2.  **Select Persona**: Choose your agent mode (General, Social, Crypto).
3.  **Command**: 
    -   *Text*: Type "Go to youtube and play lofi beats" -> EXECUTE.
    -   *Voice*: Toggle VOX and speak your command.

## Technologies

-   Python 3.11+
-   Playwright (Browser Automation)
-   CustomTkinter (GUI)
-   Google Gemini API (LLM & Vision)
-   SpeechRecognition & PyAudio

## License

MIT
