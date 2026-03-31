"""
core/data_store.py – Save and load ski measurement CSVs.

File format:
  ~/Documents/SkiLoadcell/YYYYMMDD_HHMMSS_<ski_model>.csv

CSV columns:
  Timestamp, Ski Model, Total Weight (g), Cell 1 … Cell 120
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import config


# ── Write ─────────────────────────────────────────────────────────────────────

def _safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in text)


def make_save_path(ski_model: str) -> Path:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{ts}_{_safe_name(ski_model)}.csv"
    return config.DOCUMENTS_DIR / name


def save_measurement(
    ski_model: str,
    readings: list[Optional[float]],
    total_weight: float,
    path: Optional[Path] = None,
) -> Path:
    """Write one measurement row to disk. Returns the file path."""
    if path is None:
        path = make_save_path(ski_model)

    ts = datetime.now().isoformat(timespec="seconds")

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # Header
        w.writerow(
            ["Timestamp", "Ski Model", "Total Weight (g)"]
            + [f"Cell {i + 1}" for i in range(config.TOTAL_CELLS)]
        )
        # Data
        w.writerow(
            [ts, ski_model, f"{total_weight:.2f}"]
            + [f"{v:.2f}" if v is not None else "N/A" for v in readings]
        )
    return path


# ── Read ──────────────────────────────────────────────────────────────────────

def list_measurements() -> list[dict]:
    """
    Return summary dicts for all saved CSVs, newest-first.
    Each dict has keys: path, filename, timestamp, ski_model, total_weight.
    """
    results = []
    for fp in sorted(config.DOCUMENTS_DIR.glob("*.csv"), reverse=True):
        summary = _read_summary(fp)
        if summary:
            results.append(summary)
    return results


def _read_summary(path: Path) -> Optional[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)          # skip header
            row = next(reader, None)
        if row and len(row) >= 3:
            return {
                "path":         path,
                "filename":     path.name,
                "timestamp":    row[0],
                "ski_model":    row[1],
                "total_weight": row[2],
            }
    except Exception:
        pass
    return None


def load_measurement(path: Path) -> tuple[dict, list[Optional[float]]]:
    """
    Load a measurement CSV.
    Returns (metadata_dict, readings_list[120]).
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)                    # header
        row = next(reader)

    meta = {
        "timestamp":    row[0] if len(row) > 0 else "",
        "ski_model":    row[1] if len(row) > 1 else "",
        "total_weight": row[2] if len(row) > 2 else "",
    }

    readings: list[Optional[float]] = []
    for cell_str in row[3: 3 + config.TOTAL_CELLS]:
        try:
            readings.append(float(cell_str))
        except (ValueError, TypeError):
            readings.append(None)

    # Pad to TOTAL_CELLS in case file has fewer columns
    while len(readings) < config.TOTAL_CELLS:
        readings.append(None)

    return meta, readings
