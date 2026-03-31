"""
core/arduino_manager.py

Manages serial connections to up to 15 Arduino Nanos.
Each Arduino runs in its own background reader thread.
The GUI reads shared state (no blocking) from the main thread.
"""
import threading
import time
from typing import Optional, Callable

import serial
import serial.tools.list_ports

import config
from core.serial_reader import parse_line, is_data_line


class ArduinoConnection:
    """One serial connection + background reader thread for one Arduino."""

    def __init__(self, arduino_id: int, port: str):
        self.arduino_id   = arduino_id          # 0-indexed
        self.port         = port
        self.connected    = False
        self.error_msg    = ""
        self.last_update  = 0.0                 # epoch time of last valid reading

        self._serial: Optional[serial.Serial] = None
        self._lock        = threading.Lock()
        self._stop_evt    = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Shared state written by reader thread, read by GUI
        self._readings: dict[int, Optional[float]] = {}   # board 1-8 -> grams
        self._raw_lines: list[str] = []                   # ring-buffer (last 200 lines)
        self._raw_lock  = threading.Lock()

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open port and start reader thread. Returns True on success."""
        try:
            self._serial = serial.Serial(
                self.port,
                config.BAUD_RATE,
                timeout=config.SERIAL_TIMEOUT,
            )
            time.sleep(2.0)          # wait for Arduino reset after DTR
            self.connected = True
            self.error_msg = ""
            self._stop_evt.clear()
            self._thread = threading.Thread(
                target=self._read_loop, daemon=True, name=f"arduino-{self.arduino_id}"
            )
            self._thread.start()
            return True
        except serial.SerialException as exc:
            self.connected = False
            self.error_msg = str(exc)
            return False

    def disconnect(self):
        """Stop reader thread and close port."""
        self._stop_evt.set()
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self.connected = False

    # ── Data access (thread-safe) ─────────────────────────────────────────────

    def get_readings(self) -> dict[int, Optional[float]]:
        with self._lock:
            return dict(self._readings)

    def get_raw_lines(self, n: int = 100) -> list[str]:
        """Return the last n raw serial lines."""
        with self._raw_lock:
            return list(self._raw_lines[-n:])

    def send(self, text: str):
        """Send a string (+ newline) to the Arduino."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.write((text + "\n").encode("utf-8"))
                self._serial.flush()
            except serial.SerialException:
                pass

    def is_stale(self, timeout: float = 3.0) -> bool:
        """True if no valid reading received within `timeout` seconds."""
        return self.connected and (time.time() - self.last_update) > timeout

    # ── Background reader ─────────────────────────────────────────────────────

    def _read_loop(self):
        while not self._stop_evt.is_set():
            try:
                if self._serial and self._serial.is_open:
                    if self._serial.in_waiting:
                        raw  = self._serial.readline()
                        line = raw.decode("utf-8", errors="replace").strip()
                        if line:
                            # Store raw line for debug monitor
                            with self._raw_lock:
                                self._raw_lines.append(line)
                                if len(self._raw_lines) > 200:
                                    self._raw_lines.pop(0)
                            # Parse if it's a data line
                            if is_data_line(line):
                                readings = parse_line(line)
                                with self._lock:
                                    self._readings = readings
                                    self.last_update = time.time()
                    else:
                        time.sleep(0.01)
            except serial.SerialException as exc:
                with self._lock:
                    self.connected = False
                    self.error_msg  = str(exc)
                break
            except Exception:
                time.sleep(0.05)


# ─────────────────────────────────────────────────────────────────────────────

class ArduinoManager:
    """Manages all 15 Arduinos as a single logical unit."""

    def __init__(self):
        self.arduinos: dict[int, ArduinoConnection] = {}
        self._ports: dict[int, str] = {}
        self.estop_active = False

    # ── Setup ─────────────────────────────────────────────────────────────────

    def set_ports(self, ports: dict[int, str]):
        """Set COM-port mapping before connecting."""
        self._ports = ports

    def connect_all(self) -> dict[int, bool]:
        """
        Open all configured ports.
        Returns {arduino_id: success_bool}.
        Arduinos without a configured port are created as offline placeholders.
        """
        results: dict[int, bool] = {}
        for aid, port in self._ports.items():
            conn = ArduinoConnection(aid, port)
            self.arduinos[aid] = conn
            results[aid] = conn.connect()

        # Placeholders for unconfigured slots
        for i in range(config.NUM_ARDUINOS):
            if i not in self.arduinos:
                conn = ArduinoConnection(i, "")
                conn.error_msg = "No COM port configured"
                self.arduinos[i] = conn

        return results

    def disconnect_all(self):
        for conn in self.arduinos.values():
            conn.disconnect()
        self.arduinos.clear()

    def reconnect_all(self, progress_cb: Optional[Callable[[int, str], None]] = None) -> dict[int, bool]:
        """Disconnect, wait, reconnect. Calls progress_cb(step, message) if given."""
        if progress_cb:
            progress_cb(0, "Disconnecting all Arduinos…")
        self.disconnect_all()
        time.sleep(1.5)

        results: dict[int, bool] = {}
        for idx, (aid, port) in enumerate(self._ports.items()):
            if progress_cb:
                progress_cb(idx + 1, f"Connecting Arduino {aid + 1} on {port}…")
            conn = ArduinoConnection(aid, port)
            self.arduinos[aid] = conn
            results[aid] = conn.connect()

        # Re-create placeholders
        for i in range(config.NUM_ARDUINOS):
            if i not in self.arduinos:
                conn = ArduinoConnection(i, "")
                conn.error_msg = "No COM port configured"
                self.arduinos[i] = conn

        return results

    # ── Data ──────────────────────────────────────────────────────────────────

    def get_all_readings(self) -> list[Optional[float]]:
        """
        Flat list of 120 readings (left-to-right).
        Index = arduino_id * CELLS_PER_ARDUINO + (board_num - 1)
        """
        out: list[Optional[float]] = [None] * config.TOTAL_CELLS
        for aid in range(config.NUM_ARDUINOS):
            conn = self.arduinos.get(aid)
            if conn and conn.connected:
                for board_num, val in conn.get_readings().items():
                    idx = aid * config.CELLS_PER_ARDUINO + (board_num - 1)
                    if 0 <= idx < config.TOTAL_CELLS:
                        out[idx] = val
        return out

    def get_total_weight(self) -> float:
        return sum(v for v in self.get_all_readings() if v is not None)

    def get_status(self) -> dict[int, dict]:
        status: dict[int, dict] = {}
        for i in range(config.NUM_ARDUINOS):
            conn = self.arduinos.get(i)
            if conn:
                status[i] = {
                    "connected":   conn.connected,
                    "port":        conn.port,
                    "error":       conn.error_msg,
                    "last_update": conn.last_update,
                    "stale":       conn.is_stale() if conn.connected else False,
                }
            else:
                status[i] = {
                    "connected": False, "port": "", "error": "Not initialized",
                    "last_update": 0.0, "stale": False,
                }
        return status

    # ── E-Stop ────────────────────────────────────────────────────────────────

    def trigger_estop(self):
        """Software e-stop: flag active and send STOP to all connected Arduinos."""
        self.estop_active = True
        for conn in self.arduinos.values():
            if conn.connected:
                conn.send("STOP")

    def clear_estop(self):
        self.estop_active = False

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def list_available_ports() -> list[str]:
        return sorted(p.device for p in serial.tools.list_ports.comports())
