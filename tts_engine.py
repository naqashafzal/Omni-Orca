import pyttsx3
import threading
import queue

class TTSEngine:
    def __init__(self):
        self.engine = None
        self.queue = queue.Queue()
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        """
        Initialize engine in its own thread (pyttsx3 has issues if init/run 
        happens in different threads or main thread with other loops).
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)  # Default speed
        
        while self.is_running:
            try:
                text = self.queue.get(timeout=1)
                if text is None: break # Sentinel to stop
                
                self.engine.say(text)
                self.engine.runAndWait()
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS Error: {e}")

    def speak(self, text):
        """Queue text to be spoken."""
        self.queue.put(text)

    def stop(self):
        """Stop the TTS thread."""
        self.is_running = False
        self.queue.put(None)

    def set_rate(self, rate):
        """Set speech rate (approx words per minute)."""
        # We can't easily change property inside the loop while runAndWait might be active
        # For simplicity in this version, we might skip dynamic rate changing 
        # or implement a command queue for properties too.
        pass 
