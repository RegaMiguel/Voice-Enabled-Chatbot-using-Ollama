import logging
import sys
import threading
import time

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s  %(levelname)-8s %(name)s - %(message)s",
    datefmt = "%H:%M:%S",
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("thursday.log", encoding = "utf-8")
    ],
)

logger = logging.getLogger("thursday.main")

from speaker import speak
from listener import record_until_silence
from transcriber import transcribe
from brain import process, Intent
from wakeword import WakeWordDetector
from skills import check_due_now, check_warnings

AUDIO_FILE = "input.wav"

_shutdown_flag  = threading.Event()
_in_session     = threading.Event()   # True while Thursday is actively conversing


# ── Conversation session ──────────────────────────────────────────────────────

def session_start():
    """
    Activated by the wake word.
    Keeps listening and responding until:
      - The user goes silent (no speech detected)
      - The user says a shutdown phrase
      - An unrecoverable error occurs
    """
    if _in_session.is_set():
        logger.info("Already in session — ignoring wake word.")
        return

    _in_session.set()
    logger.info("Session started.")

    try:
        speak("Yes, sir?")

        consecutive_misses = 0
        MAX_MISSES = 2  # How many silent/empty turns before Thursday goes back to standby

        while not _shutdown_flag.is_set():

            # ── Listen ────────────────────────────────────────────────────────
            success = record_until_silence(AUDIO_FILE)

            if not success:
                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    speak("I'll be on standby, sir. Just call me when you need me.")
                    logger.info("No speech detected — returning to standby.")
                    break
                speak("I didn't catch that, sir.")
                continue

            # ── Transcribe ────────────────────────────────────────────────────
            text = transcribe(AUDIO_FILE)

            if not text or not text.strip():
                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    speak("Returning to standby, sir.")
                    break
                speak("Sorry, I didn't quite catch that.")
                continue

            consecutive_misses = 0  # Reset on successful transcription
            print(f"\n[You] {text}")

            # ── Process & respond ─────────────────────────────────────────────
            try:
                intent, response = process(text)
            except Exception as e:
                logger.error(f"Brain error: {e}", exc_info=True)
                speak("Sorry, something went wrong processing that, sir.")
                continue

            print(f"[Thursday] {response}\n")
            speak(response)

            # ── Check for shutdown ────────────────────────────────────────────
            if intent == Intent.SHUTDOWN:
                _shutdown_flag.set()
                break

            # ── Stay in conversation ──────────────────────────────────────────
            # Small pause so Thursday doesn't immediately record her own voice
            time.sleep(0.4)

    except Exception as e:
        logger.exception("Unexpected session error:")
        speak("Sorry, something went wrong, sir. Please check the logs.")
    finally:
        _in_session.clear()
        logger.info("Session ended — returning to wake word standby.")


# ── Background loops ──────────────────────────────────────────────────────────

def _reminder_loop():
    """Check for due reminders every 30 seconds."""
    while not _shutdown_flag.is_set():
        try:
            due = check_due_now()
            for title in due:
                msg = f"Reminder, sir: {title}."
                print(f"[Thursday - Reminder] {msg}")
                speak(msg)
        except Exception as e:
            logger.warning(f"Reminder check error: {e}")
        time.sleep(30)


def _sysmon_loop():
    """Proactively warn about resource spikes every 60 seconds."""
    while not _shutdown_flag.is_set():
        try:
            warnings = check_warnings()
            for w in warnings:
                print(f"[Thursday - Warning] {w}")
                speak(w)
        except Exception as e:
            logger.warning(f"System monitoring error: {e}")
        time.sleep(60)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║            THURSDAY  —  Online and Standing By           ║
║                Intelligent System  v2.0                  ║
╚══════════════════════════════════════════════════════════╝
Say "THURSDAY" to begin a conversation.
Keep talking — Thursday stays with you until you go quiet.
Say "Goodbye THURSDAY" to shut down.
Press Ctrl+C to force quit.
""")

    speak("THURSDAY online. All systems operational. How may I assist you today, sir?")

    threading.Thread(target=_reminder_loop, daemon=True, name="reminders").start()
    threading.Thread(target=_sysmon_loop,   daemon=True, name="sysmon").start()

    detector = WakeWordDetector(on_wake=lambda: threading.Thread(
        target=session_start, daemon=True
    ).start())

    detector.start()

    try:
        while not _shutdown_flag.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Ctrl+C] Shutting down...")
    finally:
        detector.stop()
        speak("THURSDAY shutting down. Goodbye, sir.")
        logger.info("THURSDAY has been shut down.")


if __name__ == "__main__":
    main()