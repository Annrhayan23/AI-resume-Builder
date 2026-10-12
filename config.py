import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
OUTPUT_DIR = BASE_DIR / "backend" / "output"
CONFIG_FILE = DATA_DIR / "settings.json"
APPLICATIONS_FILE = DATA_DIR / "applications.xlsx"
MASTER_RESUME_FILE = DATA_DIR / "master_resume.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
    "gemini_model": "gemini-2.5-flash",
    "fit_bar_threshold": 50,
    "evidence_match_target": 75,
    "max_iterations": 3,
}

def load_settings():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                if not config["gemini_api_key"]:
                    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_settings(new_settings: dict):
    current = load_settings()
    current.update(new_settings)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current
