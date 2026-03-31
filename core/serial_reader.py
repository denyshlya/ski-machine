"""
core/serial_reader.py – Parse lines from the Arduino HX711 reader.

Arduino output format (calibrated):
    B1:12.34g | B2:56.78g | B3:TO | B4:0.00g | ...

Arduino output format (raw, pre-calibration):
    B1:123456 | B2:234567 | B3:TO | ...

TO = timeout sentinel (no chip response within timeout window).
"""
import re
from typing import Optional

_BOARD_RE = re.compile(r'B(\d+):([^\s|]+)')


def parse_line(line: str) -> dict[int, Optional[float]]:
    """
    Parse one serial line.

    Returns a dict mapping board number (1-based) to:
      float – grams (or raw count if not yet calibrated)
      None  – timeout / parse error
    """
    result: dict[int, Optional[float]] = {}
    for m in _BOARD_RE.finditer(line):
        board = int(m.group(1))
        raw   = m.group(2).strip()
        if raw in ("TO", "ERR", "ERROR"):
            result[board] = None
        else:
            cleaned = raw.rstrip("g")
            try:
                result[board] = float(cleaned)
            except ValueError:
                result[board] = None
    return result


def is_data_line(line: str) -> bool:
    """Return True if the line contains load-cell readings."""
    return bool(_BOARD_RE.search(line))
