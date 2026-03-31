"""
config.py – Global constants and persistent config (COM port assignments).
"""
import json
from pathlib import Path

APP_TITLE   = "Ski Load Cell System"
APP_VERSION = "1.0.0"

NUM_ARDUINOS     = 15
CELLS_PER_ARDUINO = 8
TOTAL_CELLS      = NUM_ARDUINOS * CELLS_PER_ARDUINO   # 120

BAUD_RATE       = 115200
SERIAL_TIMEOUT  = 1.0          # seconds
READ_INTERVAL_MS = 300         # GUI refresh rate for live view

KNOWN_MASS_G = 163.0           # default calibration mass (grams)

# ── Filesystem ────────────────────────────────────────────────────────────────
DOCUMENTS_DIR = Path.home() / "Documents" / "SkiLoadcell"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DOCUMENTS_DIR / "config.json"

# ── Default COM ports (only 2 Arduinos wired right now) ───────────────────────
DEFAULT_PORTS: dict[int, str] = {
    0: "COM3",
    1: "COM4",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_port_config() -> dict[int, str]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            return {int(k): v for k, v in data.get("ports", {}).items()}
        except Exception:
            pass
    return DEFAULT_PORTS.copy()


def save_port_config(ports: dict[int, str]) -> None:
    try:
        existing: dict = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                existing = json.load(f)
        existing["ports"] = {str(k): v for k, v in ports.items()}
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[config] Failed to save: {e}")


def load_full_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_full_config(data: dict) -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[config] Failed to save: {e}")
