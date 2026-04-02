import threading
import time
import io
import traceback
try:
    from PIL import ImageGrab
    import PIL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class VisionAgent:
    def __init__(self, llm_provider, gui_callback=None):
        self.llm = llm_provider
        self.gui_callback = gui_callback
        
        self.is_running = False
        self.thread = None
        self.interval_seconds = 10 # Check every 10 seconds to save tokens/API calls
        self.last_suggestion = ""
        
        self.PROACTIVE_PROMPT = (
            "You are a proactive AI assistant living on the user's PC. Look at this screenshot of their desktop. "
            "Is the user currently struggling with an error, looking at a bug, or visibly stuck? "
            "If YES, provide a SHORT, 1-2 sentence helpful suggestion or fix. "
            "If NO (they are just browsing, watching a video, or typing normally without errors), reply EXACTLY with the word 'IDLE'."
        )

    def start(self):
        if not PIL_AVAILABLE:
            print("[VISION] Error: Pillow library not installed. Cannot capture screen.")
            return False
            
        if self.is_running:
            return True
            
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("[VISION] Proactive Screen Monitor STARTED.")
        return True

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[VISION] Proactive Screen Monitor STOPPED.")

    def _monitor_loop(self):
        while self.is_running:
            try:
                # 1. Capture screen
                screenshot = ImageGrab.grab()
                
                # 2. Compress the image to save bandwidth and API time
                # Resize to max 1280x720 while maintaining aspect ratio
                screenshot.thumbnail((1280, 720), PIL.Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='JPEG', quality=60)
                img_bytes = img_byte_arr.getvalue()
                
                # 3. Ask the vision model
                response = self.llm.generate_response(
                    self.PROACTIVE_PROMPT,
                    image_bytes=img_bytes
                )
                
                suggestion = response.strip()
                
                # 4. Trigger UI if not idle
                if suggestion and "IDLE" not in suggestion.upper():
                    # Check if it's identical to last suggestion to avoid spamming the UI
                    if suggestion != self.last_suggestion:
                        self.last_suggestion = suggestion
                        print(f"👀 [VISION PROACTIVE]: {suggestion}")
                        if self.gui_callback:
                            self.gui_callback(suggestion)
                            
            except Exception as e:
                print(f"[VISION ERROR]: {e}")
                
            # Wait for next cycle
            time.sleep(self.interval_seconds)
            
if __name__ == "__main__":
    # Mock LLM for local test
    class MockLLM:
        def generate_response(self, prompt, image_bytes=None):
            return "IDLE"
            
    v = VisionAgent(MockLLM())
    v.start()
    time.sleep(5)
    v.stop()
