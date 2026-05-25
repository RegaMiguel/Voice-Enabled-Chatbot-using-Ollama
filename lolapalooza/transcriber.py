import logging
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE

logger = logging.getLogger("thursday.transcriber")


logger.info(f"Loading Whisper model '{WHISPER_MODEL}' on {WHISPER_DEVICE} with {WHISPER_COMPUTE} compute...")
_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
logger.info("whisper model loaded successfully.")

def transcribe_audio(file_path: str = "input.wav") -> str:
    try:
        segments, info = _model.transcribe(file_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        logger.info(f"Transcribed ({info.language}, {info.duration:.1f}s): '{text}'")
        return text
    except FileNotFoundError:
        logger.error(f"Audio file not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""