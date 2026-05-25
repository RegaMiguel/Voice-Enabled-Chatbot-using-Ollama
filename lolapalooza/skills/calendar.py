import json, logging, os, re, uuid
from datetime import datetime, timedelta
from pathlib import Path

from config import CALENDAR_FILE

logger = logging.getLogger("thursday.skills.calendar")

def _load() -> list[dict]:
    if not Path(CALENDAR_FILE).exists():
        return []
    try:
        with open(CALENDAR_FILE) as f:
            return json.load(f)
    except Exception:
        return []
    
def _save(entries: list[dict]):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(entries, f, indent=2, default=str)

def add_reminder(title: str, when: datetime, notes: str ="") -> str:
    entries = _load()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "when": when.isoformat(),
        "notes": notes,
        "done": False
    }
    entries.append(entry)
    _save(entries)
    friendly = when.strftime("%A, %B %d at %I:%M %p")
    logger.info(f"Added reminder: '{title}' at {friendly}")
    return f"Reminder set: '{title}' on {friendly}."

def list_upcoming(hours: int = 24) -> str:
    entries = _load()
    now = datetime.now()
    soon = now + timedelta(hours=hours)

    upcoming = [e for e in entries
                if not e["done"] and now <= datetime.fromisoformat(e["when"]) <= soon
                ]
    
    if not upcoming:
        return f"No upcoming reminders in the next {hours} hours."
    
    lines = [f"Upcoming reminds ({hours}h window):"]
    for e in sorted(upcoming, key=lambda x: x["when"]):
        t = datetime.fromisoformat(e["when"]).strftime("%I:%M %p")
        lines.append(f"  • [{e['id']}] {e['title']} at {t}")
    return "\n".join(lines)

def list_all() -> str:
    entries = _load()
    pending = [e for e in entries if not e["done"]]
    if not pending:
        return "No pending reminders."
    lines = ["All pending reminders:"]
    for e in sorted(pending, key=lambda x: x["when"]):
        dt = datetime.fromisoformat(e["when"]).strftime("%b %d, %I:%M %p")
        lines.append(f"  • [{e['id']}] {e['title']} at {dt}")
    return "\n".join(lines)

def complete_reminder(reminder_id: str) -> str:
    entries = _load()
    for e in entries:
        if e["id"] == reminder_id:
            e["done"] = True
            _save(entries)
            return f"Reminder '{e['title']} marked as completed."
    return f"No reminder found with ID: {reminder_id}"

def check_due_now() -> list[str]:
    entries = _load()
    now = datetime.now()
    window = now + timedelta(minutes=1)
    triggered = []
    changed = False

    for e in entries:
        if e["done"]:
            continue
        dt = datetime.fromisoformat(e["when"])
        if now <= dt <= window:
            triggered.append(e["title"])
            e["done"] = True
            changed = True

    if changed:
        _save(entries)
    
    return triggered

def is_calendar_query(text: str) -> bool:
    triggers = [
        "remind", "reminder", "calendar", "schedule", "agenda", "event",
        "what's on my calendar", "what's on my schedule", "what's on my agenda",
        "what do i have", "what's coming up", "what's next",
    ]
    lower = text.lower()
    return any(t in lower for t in triggers)

def parse_reminder_from_text(text: str) -> dict | None:
    lower = text.lower()

    m = re.search(r"in (\d+)\s*(minute|minutes|hour|hours)", lower)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = m.group(3)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        now = datetime.now()
        when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if when < now:
            when += timedelta(days=1)

        title = re.sub(r"remind me (to |about )?", "", lower, flags=re.IGNORECASE)
        title = re.sub(r"\s*at \d{1,2}: \d{2}.*", "", title).strip()
        title = title.capitalize() or "Reminder"

        return {"title": title, "when": when}
    return None