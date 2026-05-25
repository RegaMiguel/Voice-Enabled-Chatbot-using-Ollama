#!/usr/bin/env python3
# ============================================================
#  JARVIS — Debug Script
#  Run this to isolate exactly where the issue is.
#  python debug.py
# ============================================================

import sys
import os
import wave
import tempfile
import subprocess
import numpy as np

# ── Test 1: Microphone ────────────────────────────────────────────────────────
print("\n[TEST 1] Microphone & sounddevice...")
try:
    import sounddevice as sd
    print(f"  ✓ sounddevice imported")
    print(f"  Default input device: {sd.query_devices(kind='input')['name']}")

    print("  Recording 2 seconds of audio — speak something now...")
    audio = sd.rec(2 * 16000, samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
    print(f"  Audio RMS energy: {rms:.1f}  (needs to be > 200 to trigger wake word)")
    if rms < 200:
        print("  ⚠ Very low energy — mic may be muted, wrong device, or too quiet")
    else:
        print("  ✓ Mic is picking up audio")
except Exception as e:
    print(f"  ✗ Microphone error: {e}")
    sys.exit(1)


# ── Test 2: Wake word transcription ──────────────────────────────────────────
print("\n[TEST 2] Wake word detection (Whisper tiny)...")
try:
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("  Recording 3 seconds — say 'THURSDAY' clearly...")
    audio = sd.rec(3 * 16000, samplerate=16000, channels=1, dtype="int16")
    sd.wait()

    tmp = tempfile.mktemp(suffix=".wav")
    with wave.open(tmp, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio.tobytes())

    segments, _ = model.transcribe(tmp, beam_size=1)
    text = " ".join(s.text for s in segments).lower().strip()
    os.unlink(tmp)

    print(f"  Whisper heard: '{text}'")
    if "thursday" in text:
        print("  ✓ Wake word detected correctly!")
    else:
        print("  ⚠ Wake word NOT detected. Try speaking louder/clearer.")
        print("    If Whisper heard something else, update WAKE_WORD in config.py to match.")
except Exception as e:
    print(f"  ✗ Whisper error: {e}")


# ── Test 3: Full recording + transcription (listener.py) ─────────────────────
print("\n[TEST 3] Full speech recording (listener.py)...")
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from listener import record_until_silence
    from transcriber import transcribe

    print("  Speak a sentence after this line — it stops when you go silent...")
    success = record_until_silence("debug_input.wav")
    if not success:
        print("  ⚠ No speech detected. Check SILENCE_THRESHOLD in listener.py (currently 500)")
    else:
        text = transcribe("debug_input.wav")
        print(f"  Transcribed: '{text}'")
        if text:
            print("  ✓ Recording and transcription working!")
        else:
            print("  ⚠ Recording worked but transcription returned empty string")
except Exception as e:
    print(f"  ✗ Listener/transcriber error: {e}")


# ── Test 4: Ollama ────────────────────────────────────────────────────────────
print("\n[TEST 4] Ollama LLM...")
try:
    from config import OLLAMA_PATH, OLLAMA_MODEL
    result = subprocess.run(
        [OLLAMA_PATH, "run", OLLAMA_MODEL],
        input=b"Reply with exactly three words: I am THURSDAY.",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    response = result.stdout.decode(errors="replace").strip()
    print(f"  Ollama response: '{response}'")
    if response:
        print("  ✓ Ollama is working!")
    else:
        err = result.stderr.decode(errors="replace").strip()
        print(f"  ⚠ Empty response. stderr: {err}")
except FileNotFoundError:
    print(f"  ✗ Ollama not found at '{OLLAMA_PATH}' — update OLLAMA_PATH in config.py")
except subprocess.TimeoutExpired:
    print("  ✗ Ollama timed out — is it running? Try: ollama serve")
except Exception as e:
    print(f"  ✗ Ollama error: {e}")


# ── Test 5: TTS ───────────────────────────────────────────────────────────────
print("\n[TEST 5] Text-to-speech (pyttsx3)...")
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.say("THURSDAY diagnostic complete.")
    engine.runAndWait()
    print("  ✓ TTS working — did you hear the voice?")
except Exception as e:
    print(f"  ✗ TTS error: {e}")


print("\n" + "="*50)
print("Paste the output above so we can pinpoint the issue.")
print("="*50 + "\n")