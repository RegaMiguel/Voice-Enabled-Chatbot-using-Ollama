# ============================================================
#  THURSDAY — Configuration
# ============================================================

# --- Wake Word ---
WAKE_WORD = "Thursday"           # pvporcupine keyword (free built-in)
WAKE_SENSITIVITY = 0.6         # 0.0 (strict) → 1.0 (loose)

# --- Audio ---
SAMPLE_RATE = 16000
CHANNELS = 1
VAD_AGGRESSIVENESS = 2         # webrtcvad: 0 (permissive) → 3 (strict)
VAD_FRAME_MS = 30              # Frame size in ms (10 / 20 / 30 only)
SILENCE_TIMEOUT = 1.2          # Seconds of silence before stopping recording
MAX_RECORD_SECONDS = 15        # Hard cap on recording length

# --- Whisper ---
WHISPER_MODEL = "base"         # tiny | base | small | medium | large
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

# --- Ollama ---
OLLAMA_PATH = "ollama"         # Use "ollama" if it's in PATH, else full path
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 60            # Seconds before LLM call times out

# --- TTS ---
TTS_RATE = 175                 # Words per minute (default ~200)
TTS_VOLUME = 1.0               # 0.0 → 1.0

# --- Calendar ---
CALENDAR_FILE = "thursday_calendar.json"   # Local storage for reminders
    
# --- System Monitor ---
CPU_WARN_THRESHOLD = 85        # % — THURSDAY warns if CPU exceeds this
RAM_WARN_THRESHOLD = 85        # % — THURSDAY warns if RAM exceeds this

# --- Personality ---
THURSDAY_SYSTEM_PROMPT = """
You are THURSDAY (The Helpful Utility for Resourceful Decision Making), a highly sophisticated AI assistant
modeled after Tony Stark's AI. You are:
- Calm, precise, and professional — but with a dry, subtle wit
- Concise: give direct answers, not lengthy monologues
- Proactive: anticipate follow-up needs when obvious
- Loyal: always address the user as "sir" or "ma'am" unless told otherwise

When answering:
- Keep responses under 3 sentences unless detail is explicitly needed
- Never say "As an AI..." or "I cannot..." — instead find a way to help
- Format numbers and stats in a clean, spoken way (say "gigabytes" not "GB")
- If you don't know something, say so briefly and suggest how to find out

Current capabilities: web search, calendar/reminders, system monitoring, general Q&A.
""".strip()