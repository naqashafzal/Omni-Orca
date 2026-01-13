import asyncio
import sys
from browser_agent import BrowserAgent
# Optional: only import VoiceCommander if we plan to use it immediately, 
# but it's good to have it ready.
try:
    from voice_commander import VoiceCommander
    VOICE_AVAILABLE = True
except ImportError:
    print("Voice dependencies not fully installed. Voice features disabled.")
    VOICE_AVAILABLE = False

async def main():
    agent = BrowserAgent(headless=False)
    
    if VOICE_AVAILABLE:
        commander = VoiceCommander()
    else:
        commander = None

    print("--- Automater Control ---")
    print("1. Record Actions (Voice/Manual)")
    print("2. Replay Recording")
    print("3. Exit")
    
    choice = input("Select mode (1/2/3): ")

    if choice == "1":
        await agent.start()
        print("Browser started. Type commands or say 'stop' to finish.")
        print("Supported voice commands: 'go to google', 'click search', 'type [text]', 'stop'")
        
        try:
            while True:
                # For simplicity, we'll ask user if they want to use voice or text for each step
                # In a real "autonomous" loop, this would be more fluid.
                mode = input("Command source (text/voice/stop): ").strip().lower()
                
                command = ""
                if mode == "stop":
                    break
                elif mode == "voice" and commander:
                    command = commander.listen()
                else:
                    command = input("Enter command (e.g., 'goto google.com', 'click #id'): ")

                if not command:
                    continue

                if "stop" in command:
                    break
                
                # Simple parser
                if "go to" in command or "goto" in command:
                    # Extract URL
                    url = command.replace("go to", "").replace("goto", "").strip()
                    # Add https if missing
                    if not url.startswith("http"):
                        url = "https://" + url
                    await agent.navigate(url)
                    
                elif "click" in command:
                    selector = command.replace("click", "").strip()
                    # If selector is empty (just "click"), maybe ask for it or click active element?
                    # For now assume user says "click [selector]" (a bit hard with voice for css selectors)
                    if selector:
                         await agent.click(selector)
                    else:
                        print("Please specify what to click.")

                elif "type" in command:
                    # simplistic parsing: "type hello world into #search"
                    # or just "type hello world" -> types into focused element? 
                    # Playwright needs a selector. Let's assume params are split by " into "
                    if " into " in command:
                        parts = command.replace("type", "").split(" into ")
                        text_to_type = parts[0].strip()
                        selector = parts[1].strip()
                        await agent.type(selector, text_to_type)
                    else:
                        print("Format: type [text] into [selector]")

                else:
                    print("Unknown command. Try 'go to', 'click', 'type'.")

        except KeyboardInterrupt:
            pass
        finally:
            save = input("Save recording? (y/n): ")
            if save.lower() == 'y':
                name = input("Filename (default: recording.json): ") or "recording.json"
                agent.save_recording(name)
            await agent.close()

    elif choice == "2":
        filename = input("Enter recording file (default: recording.json): ") or "recording.json"
        await agent.start()
        await agent.replay_recording(filename)
        await agent.close()

    else:
        print("Exiting.")

if __name__ == "__main__":
    asyncio.run(main())
