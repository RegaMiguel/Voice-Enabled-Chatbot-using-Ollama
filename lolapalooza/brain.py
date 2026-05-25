import logging, subprocess, threading, time
from typing import Optional

from config import OLLAMA_PATH, OLLAMA_MODEL, OLLAMA_TIMEOUT, THURSDAY_SYSTEM_PROMPT
import skills

logger = logging.getLogger("thursday.brain")

class Intent:
    SEARCH = "search"
    CALENDAR = "calendar"
    SYSMON = "sysmon"
    GENERAL = "general"
    SHUTDOWN = "shutdown"

SHUTDOWN_PHRASES = ["shutdown thursday", "goodbye thursday", "exit", "quit", "power off", "that's all thursday"]

def detect_intent(text: str) -> str:
    lower = text.lower()

    if any(p in lower for p in SHUTDOWN_PHRASES):
        return Intent.SHUTDOWN
    
    if skills.is_sysmon_query(lower):
        return Intent.SYSMON

    if skills.is_calendar_query(lower):
        return Intent.CALENDAR
    
    if skills.is_search_query(lower):
        return Intent.SEARCH

    return Intent.GENERAL


def handle_sysmon(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["full", "all", "complete", "report", "everything"]):
        return skills.get_full_report()
    return skills.get_quick_status()

def handle_calendar(text: str) -> str:
    lower = text.lower()

    if any(w in lower for w in ["list", "show", "what are", "what", "upcoming", "do i have"]):
        return skills.list_reminders()

    if any(w in lower for w in ["done", "complete", "finished", "mark"]):
        import re
        m = re.search(r"\[?([a-f0-9]{8})\]?", lower)

        if m:
            return skills.complete_reminder(m.group(1))
        return "Please specify the reminder ID, sir"


    parsed = skills.parse_reminder_from_text(text)
    if parsed:
        return skills.add_reminder(parsed["title"], parsed["when"])

    context = skills.list_all()
    prompt = f"{context}\n\nUser request: {text}"
    return ask_llm(prompt)

def handle_search(text: str) -> str:

    import re
    query = re.sub(
        r"^(thursday,?\s*)?(search|look up|find|what is|who is|where is|"
        r"when did|how do|tell me about)\s*",
        "", text, flags = re.IGNORECASE).strip() or text

    raw_results = skills.search(query)
    summary_prompt = (
        f"Using only the following search results, give a concise spoken answer "
        f"(2-3 sentences MAX). Do not mention the source. \n\n{raw_results}"
    )

    return ask_llm(summary_prompt)


def ask_llm(user_message: str, extra_context: str = "") -> str:
    """
    Send a prompt to Ollama and return the response text.
    Injects the THURSDAY system prompt automatically.
    """

    full_prompt = (
        f"[SYSTEM]\n{THURSDAY_SYSTEM_PROMPT}\n\n"
        f"{('[CONTEXT]\n' + extra_context + chr(10) + chr(10)) if extra_context else ''}"
        f"[USER]\n{user_message}"
    )

    logger.info(f"Sending to LLM ({OLLAMA_MODEL})...")
    result: list[str] = []
    error: list[str] = []

    def _run():
        try:
            proc = subprocess.run(
                [OLLAMA_PATH, "run", OLLAMA_MODEL],
                input = full_prompt.encode(),
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                timeout = OLLAMA_TIMEOUT,
            )
            if proc.returncode == 0:
                result.append(proc.stdout.decode(errors="replace").strip())
            else:
                error.append(proc.stderr.decode(errors="replace"))
        except subprocess.TimeoutExpired:
            error.append("timeout")
        except FileNotFoundError:
            error.append("Ollama not found")
        except Exception as e:
            error.append(str(e))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout = OLLAMA_TIMEOUT + 5)


    if result:
        return result[0]
    if error:
        msg = error[0]
        if "timeout" in msg:
            logger.error("LLM timed out")
            return "I'm sorry, sir, but the language model took too long to respond. Please try again later."
        if "not found" in msg:
            logger.error("Ollama executable not found")
            return "I'm sorry, sir, but I seem to be having trouble accessing the language model. Please ensure Ollama is running."
        logger.error(f"LLM error: {msg}")
        return "I'm sorry, sir, but there was an error processing your request."
    return "I didn't receive a response from the model, sir."

def process(text: str) -> tuple[str, str]:
    """
    Route text to the appropriate skill or LLM.
    Returns (intent, response_text).
    """
    intent = detect_intent(text)
    logger.info(f"Intent: {intent} | Input: '{text}'")
 
    if intent == Intent.SHUTDOWN:
        return intent, "Of course, sir. Going offline. Have a good one."
 
    if intent == Intent.SYSMON:
        response = handle_sysmon(text)
    elif intent == Intent.CALENDAR:
        response = handle_calendar(text)
    elif intent == Intent.SEARCH:
        response = handle_search(text)
    else:
        response = ask_llm(text)
 
    return intent, response