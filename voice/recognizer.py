import speech_recognition as sr

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recognize(self, audio_data):
        with sr.AudioFile(audio_data) as source:
            audio = self.recognizer.record(source)
            try:
                return self.recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                return f"Service error: {e}"
