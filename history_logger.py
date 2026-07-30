import json
import os
from datetime import datetime, timedelta

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "usage_history.json")

def log_usage(gemini_5h_pct, external_5h_pct):
    """
    Appends the current usage to the history file.
    """
    now = datetime.now().isoformat()
    record = {
        "timestamp": now,
        "gemini_5h": gemini_5h_pct,
        "external_5h": external_5h_pct
    }
    
    history = _load_history()
    history.append(record)
    
    # Prune history to keep only last 24 hours (approx 480 records at 3 min intervals)
    cutoff = datetime.now() - timedelta(hours=24)
    history = [r for r in history if datetime.fromisoformat(r["timestamp"]) > cutoff]
    
    _save_history(history)

def get_history(minutes=90):
    """
    Returns history from the last N minutes.
    """
    history = _load_history()
    cutoff = datetime.now() - timedelta(minutes=minutes)
    return [r for r in history if datetime.fromisoformat(r["timestamp"]) > cutoff]

def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[history_logger] Failed to load history: {e}")
        return []

def _save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        print(f"[history_logger] Failed to save history: {e}")

if __name__ == "__main__":
    # Test
    log_usage(74.5, 99.0)
    print(get_history())
