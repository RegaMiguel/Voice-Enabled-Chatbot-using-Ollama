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
        logging.FileHandler("jarvis.log", encoding = "utf-8")
    ],
)

logger = logging.getLogger("jarvis.main")


from speaker import speak
from listener import record_until_silence
from transcriber import transcribe_audio
from brain import handle_search, process, Intent
from wakeword import WakeWordDetector
from skills import check_due_now, check_warnings

AUDIO_FILE = "input.wav"

_shutdown_flag = threading.Event()
_processing = threading.Lock()

def session_start():
    """ONE full listen -> transcribe -> respond cycle."""
    if not _processing.acquire(blocking = False):
        logger.info("Already processing - ignoring wake word.")
        return

    try:
        speak("Yes, sir?")

        success = record_until_silence(AUDIO_FILE)
        if not success:
            speak("I didn't catch that. sir.")
            return
        
        text = transcribe_audio(AUDIO_FILE)
        if not text:
            speak ("Sorry, I couldn't understand you, sir.")
            return

        print(f"\n[You] {text}")

        intent, response = process(text)

        print(f"[Thursday] {response}\n")
        speak(response)

        if intent == Intent.SHUTDOWN:
            _shutdown_flag.set()

    except Exception as e:
        logger.exception("Error during session:")
        speak("Sorry, something went wrong, sir. Please Check the logs for details.")

    finally:
        _processing.release()

def _reminder_loop():
    """Check for due reminders every 30 seconds."""
    while not _shutdown_flag.is_set():
        try:
            due = check_due_now()
            for title in due:
                msg = f"Reminder: {title} is due."
                print(f"[Thursdaay - Reminder] {msg}")
                speak(msg)

        except Exception as e:
            logger.warning(f"Reminder check error: {e}")
        time.sleep(30)


def _sysmon_loop():
    """Proactively warn about resource spikes every 60 seconds."""
    while not _shutdown_flag.is_set():
        try:
            warning = check_warnings()
            for w in warning:
                print(f"[Thursday - Warning] {w}")
                speak(w)
        except Exception as e:
            logger.warning(f"System monitoring error: {e}")
        time.sleep(60)


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║            THURSDAY  -   Online and Standing By          ║
║                Intelligent System  v2.0                  ║
╚══════════════════════════════════════════════════════════╝
Say "Hey THURSDAY" (or just "THURSDAY") to begin.
Say "Goodbye THURSDAY" to shut down.
Press Ctrl+C to force quit.
""")

    speak("THURSDAY online. All systems operational. How may I assist you today, sir?")


    threading.Thread(target=_reminder_loop, daemon = True, name="reminder").start()
    threading.Thread(target=_sysmon_loop, daemon = True, name="sysmon").start()

    detector = WakeWordDetector(on_wake=lambda: threading.Thread(
        target= handle_search, daemon=True
    ).start())

    detector.start()

    try:
        while not _shutdown_flag.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n [Ctrl+C] shutting down...")
    finally:
        detector.stop()
        speak("THURSDAY shutting down. Goodbye, sir.")
        logger.info("THURSDAY has been shut down.")

if __name__ == "__main__":
    main()
    
