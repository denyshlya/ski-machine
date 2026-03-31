"""
gui/pages/calibration_mode.py

Enters calibration mode by monitoring serial output for all connected Arduinos.
The physical button on A5 of each Arduino is what actually triggers calibration;
this page just provides a live combined serial view and instructions.
"""
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage


class CalibrationModePage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._seen: dict[int, int] = {}
        self._build()

    def _build(self):
        self._page_header(
            "🛠  Calibration Mode",
            "Monitor all Arduinos · calibration is triggered by the physical button (A5→GND)",
        )
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=28, pady=12)

        info = (
            "To enter calibration on any Arduino:\n"
            "  1. Press the button wired to A5 → GND on that board.\n"
            "  2. Follow the on-screen prompts in the serial output below.\n"
            "  3. For detailed per-board guidance, use Load Cell Calibration.\n\n"
            "All connected Arduinos are mirrored here simultaneously."
        )
        tk.Label(body, text=info, bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_BODY, justify="left", anchor="w").pack(
                     fill=tk.X, pady=(0, 12))

        ctrl = tk.Frame(body, bg=theme.BG)
        ctrl.pack(fill=tk.X, pady=(0, 6))
        tk.Label(ctrl, text="Combined serial output", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_HEADING).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="Clear",
                   command=self._clear).pack(side=tk.RIGHT)

        self._txt = tk.Text(
            body, bg=theme.BG_SECONDARY, fg=theme.TEXT,
            font=theme.F_MONO, wrap="word", state="disabled")
        vsb = ttk.Scrollbar(body, orient="vertical", command=self._txt.yview)
        self._txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt.pack(fill=tk.BOTH, expand=True)
        self._txt.tag_configure("cal", foreground=theme.WARNING)
        self._txt.tag_configure("ok",  foreground=theme.SUCCESS)
        self._txt.tag_configure("err", foreground=theme.DANGER)

    def on_show(self):
        self._seen = {}
        self._poll()

    def on_hide(self):
        self._cancel_after()

    def _poll(self):
        for aid in range(config.NUM_ARDUINOS):
            conn = self.manager.arduinos.get(aid)
            if not conn or not conn.connected:
                continue
            lines = conn.get_raw_lines(200)
            seen  = self._seen.get(aid, 0)
            new   = lines[seen:]
            if new:
                self._seen[aid] = seen + len(new)
                self._txt.configure(state="normal")
                for line in new:
                    tag = "ok" if "DONE" in line.upper() else (
                          "err" if "ERROR" in line.upper() else
                          "cal" if "CALIB" in line.upper() else "")
                    self._txt.insert("end", f"[A{aid+1}] {line}\n", tag)
                self._txt.configure(state="disabled")
                self._txt.see("end")
        self._after_id = self.after(400, self._poll)

    def _clear(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")
        self._seen = {}
