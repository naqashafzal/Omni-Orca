"""
wake_word_agent.py
Always-listening wake word detection for hands-free activation.
Listens for "Hey Omni" in the background — no button press needed.
"""

import threading
import time
import struct

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# Fallback keyword matching (no API key needed)
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class WakeWordAgent:
    """
    Listens for the wake phrase "Hey Omni" 24/7.
    Uses pvporcupine (Picovoice) if configured, otherwise falls back to 
    SpeechRecognition keyword detection.
    """

    def __init__(self, on_activated_callback=None, picovoice_key: str = None):
        self.callback = on_activated_callback
        self.picovoice_key = picovoice_key

        self.is_running = False
        self.thread = None
        self.wake_word_phrase = "hey omni"

    def start(self) -> str:
        if self.is_running:
            return "Wake word listener already running."

        if not PYAUDIO_AVAILABLE:
            return "Error: pyaudio not installed. Run: pipwin install pyaudio"

        self.is_running = True

        # Try Picovoice first (higher accuracy), fall back to SR
        if PORCUPINE_AVAILABLE and self.picovoice_key:
            self.thread = threading.Thread(target=self._porcupine_loop, daemon=True)
            mode = "Picovoice"
        elif SR_AVAILABLE:
            self.thread = threading.Thread(target=self._sr_fallback_loop, daemon=True)
            mode = "SpeechRecognition fallback"
        else:
            self.is_running = False
            return "Error: Neither pvporcupine nor speech_recognition are available."

        self.thread.start()
        return f"👂 Wake word listener ACTIVE ({mode}). Say 'Hey Omni' to trigger!"

    def stop(self):
        self.is_running = False
        print("[WAKE] Wake word listener stopped.")

    def _porcupine_loop(self):
        """High-accuracy Picovoice Porcupine detection loop."""
        pa = None
        porcupine = None
        try:
            porcupine = pvporcupine.create(
                access_key=self.picovoice_key,
                keywords=["hey siri"]  # fallback built-in; custom "hey omni" needs custom model
            )
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )
            print("[WAKE] Porcupine microphone stream open.")

            while self.is_running:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    print("[WAKE] Wake word detected!")
                    self._trigger()

        except Exception as e:
            print(f"[WAKE] Porcupine error: {e}. Switching to fallback...")
            if self.is_running:
                self._sr_fallback_loop()
        finally:
            if pa:
                pa.terminate()
            if porcupine:
                porcupine.delete()

    def _sr_fallback_loop(self):
        """Fallback: Uses SpeechRecognition to detect 'hey omni' phrase."""
        if not SR_AVAILABLE:
            self.is_running = False
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        print("[WAKE] Listening for 'Hey Omni'...")

        while self.is_running:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)

                try:
                    text = recognizer.recognize_google(audio).lower()
                    print(f"[WAKE] Heard: '{text}'")
                    if self.wake_word_phrase in text or "hey auto" in text or "neural" in text:
                        print("[WAKE] Wake phrase detected!")
                        self._trigger()
                except sr.UnknownValueError:
                    pass  # Silence or unintelligible — keep listening
                except sr.RequestError as e:
                    print(f"[WAKE] STT API error: {e}")
                    time.sleep(5)

            except Exception as e:
                if self.is_running:
                    print(f"[WAKE] Microphone error: {e}")
                    time.sleep(2)

    def _trigger(self):
        """Called when wake word is detected — fires the GUI callback."""
        print("🎙️ [WAKE WORD TRIGGERED] OMNI activated!")
        if self.callback:
            self.callback()


if __name__ == "__main__":
    def on_wake():
        print(">>> WAKE WORD HEARD! Starting to listen for command...")

    agent = WakeWordAgent(on_activated_callback=on_wake)
    result = agent.start()
    print(result)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
