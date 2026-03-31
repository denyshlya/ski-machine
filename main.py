"""
main.py – Entry point for the Ski Load Cell System.

Run directly:
    python main.py

Build to .exe:
    pyinstaller ski_loadcell.spec
    (or run build_windows.bat)
"""
import sys
import os

# ── Path fix (must be first, before any local imports) ────────────────────────
# Insert the folder that contains THIS file at the front of sys.path.
# This ensures 'core', 'gui', and 'config' are always found regardless of
# which directory Python was launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ── Quick structure check (gives a clear error instead of a cryptic one) ──────
_missing = [d for d in ("core", "gui") if not os.path.isdir(os.path.join(_HERE, d))]
if _missing:
    import tkinter as tk
    from tkinter import messagebox
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Missing folders",
        f"Cannot find these folders next to main.py:\n\n"
        + "\n".join(f"  {_HERE}\\{d}\\" for d in _missing)
        + "\n\nMake sure the full project folder is intact.\n"
          "core\\, gui\\, and config.py must sit beside main.py.",
    )
    sys.exit(1)

# ── Normal imports (only reached if structure is correct) ─────────────────────
import tkinter as tk
from tkinter import messagebox

import config
from core.arduino_manager import ArduinoManager
from gui.main_window import MainWindow


def main():
    # ── Load port config ───────────────────────────────────────────────────
    ports = config.load_port_config()

    # ── Create Arduino manager ─────────────────────────────────────────────
    manager = ArduinoManager()
    manager.set_ports(ports)

    # Connect (non-blocking) – GUI shows offline until connected
    connect_results = manager.connect_all()

    failed = [
        aid for aid, ok in connect_results.items()
        if not ok and manager._ports.get(aid)
    ]

    # ── Launch GUI ─────────────────────────────────────────────────────────
    root = tk.Tk()
    root.withdraw()     # hide while building

    app = MainWindow(root, manager)

    if failed:
        names = ", ".join(
            f"Arduino {aid + 1} ({manager._ports[aid]})" for aid in failed
        )
        messagebox.showwarning(
            "Connection warning",
            f"Could not connect to:\n  {names}\n\n"
            "Check COM port assignments in Settings → System Check.",
            parent=root,
        )

    root.deiconify()
    root.protocol("WM_DELETE_WINDOW", app._on_exit)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        manager.disconnect_all()


if __name__ == "__main__":
    main()
