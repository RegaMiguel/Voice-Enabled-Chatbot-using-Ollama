# ============================================================
#  JARVIS — Wake Word Detection (sounddevice + faster-whisper)
# ============================================================
# No PyAudio, no Porcupine, no signup required.
# Continuously samples short audio chunks, transcribes them
# with Whisper, and fires on_wake() when the wake word is heard.
# ============================================================

import logging
import threading
import wave
import tempfile
import os
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import WAKE_WORD, SAMPLE_RATE, WHISPER_DEVICE, WHISPER_COMPUTE

logger = logging.getLogger("jarvis.wakeword")

CHUNK_SECONDS   = 2      # Record this many seconds per detection attempt
CHUNK_SAMPLES   = SAMPLE_RATE * CHUNK_SECONDS
ENERGY_THRESHOLD = 200   # Skip transcription on silent chunks (saves CPU)


class WakeWordDetector:
    """
    Listens in short bursts and uses Whisper to spot the wake word.
    Completely offline, no external API or account needed.
    """

    def __init__(self, on_wake: callable):
        self._on_wake = on_wake
        self._running = False
        self._thread  = None
        # Reuse the tiny model for speed — wake word detection doesn't need accuracy
        logger.info("Loading wake word Whisper model (tiny)…")
        self._model = WhisperModel("tiny", device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
        logger.info(f"Wake word detector ready — listening for '{WAKE_WORD}'")

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Wake word detector running…")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Wake word detector stopped.")

    def _loop(self):
        while self._running:
            try:
                # Record a short chunk
                audio = sd.rec(
                    CHUNK_SAMPLES,
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()

                # Skip silent chunks — no need to transcribe
                rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
                if rms < ENERGY_THRESHOLD:
                    continue

                # Write to a temp WAV and transcribe
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    tmp_path = f.name

                try:
                    with wave.open(tmp_path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(audio.tobytes())

                    segments, _ = self._model.transcribe(tmp_path, beam_size=1)
                    text = " ".join(s.text for s in segments).lower().strip()

                    if text:
                        logger.debug(f"Wake heard: '{text}'")

                    if WAKE_WORD.lower() in text:
                        logger.info(f"Wake word '{WAKE_WORD}' detected!")
                        try:
                            self._on_wake()
                        except Exception as e:
                            logger.error(f"on_wake callback error: {e}")

                finally:
                    os.unlink(tmp_path)

            except Exception as e:
                logger.warning(f"Wake word loop error: {e}")