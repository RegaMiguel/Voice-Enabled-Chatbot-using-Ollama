import logging
import threading
import pyttsx3
from config import TTS_RATE, TTS_VOLUME

logger = logging.getLogger("thursday.speaker")

class Speaker:
    """Thread-safe TTS engine initialized once for the lifetime of the program."""

    def __init__(self):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", TTS_RATE)
        self._engine.setProperty("volume", TTS_VOLUME)
        self._lock = threading.Lock()
        self._select_voice()
    
    def _select_voice(self):
        voices = self._engine.getProperty("voices")
        preferred = None

        for v in voices:
            name = v.name.lower()
            
            if "david" in name or ("male" in name and "en" in v.id.lower()):
                preferred = v.id
                break
        if preferred:
            self._engine.setProperty("voice", preferred)
            logger.debug(f"Voice selected: {preferred}")

    def say(self, text: str):
        if not text or not text.strip():
            return
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")

_speaker = None

def get_speaker() -> Speaker:
    global _speaker
    if _speaker is None:
        _speaker = Speaker()
    return _speaker
def speak(text: str):
    """Convenience function to speak text using the global Speaker instance."""
    get_speaker().say(text)