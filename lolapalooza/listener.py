import collections, logging, wave, webrtcvad
import numpy as np
import sounddevice as sd

from config import (
    SAMPLE_RATE, CHANNELS, VAD_AGGRESSIVENESS, VAD_FRAME_MS, SILENCE_TIMEOUT, MAX_RECORD_SECONDS
)

logger = logging.getLogger("thursday.listener")

FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)
SILENCE_FRAMES = int(SILENCE_TIMEOUT * 1000 / VAD_FRAME_MS)

def record_until_silence(output_file: str = "input.wav") -> bool:
    """
    Record audio using Voice Activity Detection.
    Starts capturing immediately, stops automatically after SILENCE_TIMEOUT
    seconds of continuous silence, or MAX_RECORD_SECONDS as a hard cap.
    
    Returns True on success, False if nothing was captured.
    """

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    frames: list[bytes] = []
    silence_count = 0
    speech_detected = False
    max_frames = int(MAX_RECORD_SECONDS * 1000 / VAD_FRAME_MS)

    ring = collections.deque(maxlen = 10)

    logger.info("Listening for speech...")

    try:
        with sd.RawInputStream(
            samplerate = SAMPLE_RATE,
            channels = CHANNELS,
            dtype = "int16",
            blocksize = FRAME_SIZE,
        ) as stream:
            while len(frames) < max_frames:
                raw, _ = stream.read(FRAME_SIZE)
                frame = bytes(raw)

                is_speech = _safe_vad(vad, frame)

                if is_speech:
                    if not speech_detected:
                        frames.extend(ring)  # Prepend buffered frames to avoid cutting off start
                        speech_detected = True
                        logger.debug("Speech detected, starting recording...")
                    frames.append(frame)
                    silence_count = 0

                else:
                    ring.append(frame)
                    if speech_detected:
                        silence_count += 1
                        frames.append(frame)  # Keep adding silence frames until timeout
                        if silence_count >= SILENCE_FRAMES:
                            logger.debug("Silence timeout reached, stopping recording.")
                            break
    except Exception as e:
        logger.error(f"Error during recording: {e}")
        return False
    if not speech_detected:
        logger.info("No speech detected.")
        return False
    
    _save_wav(frames, output_file)
    duration = len(frames) * VAD_FRAME_MS / 1000
    logger.info(f"Recording saved: {output_file} ({duration:.2f} seconds)")
    return True

def _safe_vad(vad: webrtcvad.Vad, frame: bytes) -> bool:
    try:
        return vad.is_speech(frame, SAMPLE_RATE)
    except Exception as e:
        logger.warning(f"VAD error: {e}")
        return False
    
def _save_wav(frames: list[bytes], path: str):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))