import speech_recognition as sr

class VoiceCommander:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        # Adjust for noise once at startup if possible, or separately
        with self.mic as source:
            print("Adjusting for ambient noise... ensure silence.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self):
        """Listens for a voice command and returns the text."""
        print("Listening...")
        with self.mic as source:
            # self.recognizer.adjust_for_ambient_noise(source) # Removed per-call adjustment for speed
            try:
                # timeout=None means wait forever, phrase_time_limit set to avoid hanging on noise
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                return None

        try:
            # print("Recognizing...") # Reduce spam
            command = self.recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            # print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
