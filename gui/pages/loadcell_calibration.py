"""
gui/pages/loadcell_calibration.py

Guides the operator through the HX711 calibration sequence.
Calibration is triggered by the physical button on each Arduino (A5 → GND).
This page shows step-by-step instructions and mirrors the serial output
so the operator can see what the Arduino is reporting.
"""
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage

_POLL_MS = 350


class LoadcellCalibrationPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._seen: dict[int, int] = {}
        self._build()

    def _build(self):
        self._page_header(
            "⚖  Load Cell Calibration",
            "Physical button (A5→GND) on the Arduino triggers each step",
        )

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=28, pady=12)
        body.columnconfigure(1, weight=1)

        # ── Left: settings + steps ────────────────────────────────────────────
        left = tk.Frame(body, bg=theme.BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        # Arduino selector
        tk.Label(left, text="Arduino to calibrate:", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(anchor="w")
        self._ard_var = tk.StringVar(value="Arduino 1")
        ttk.Combobox(
            left, textvariable=self._ard_var,
            values=[f"Arduino {i + 1}" for i in range(config.NUM_ARDUINOS)],
            state="readonly", width=18,
        ).pack(anchor="w", pady=(4, 12))

        # Known mass
        tk.Label(left, text="Known calibration mass (g):", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(anchor="w")
        self._mass_var = tk.StringVar(value=str(config.KNOWN_MASS_G))
        ttk.Entry(left, textvariable=self._mass_var, width=12).pack(
            anchor="w", pady=(4, 16))

        # Step-by-step guide
        tk.Label(left, text="Calibration steps", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_HEADING).pack(anchor="w",
                                                                pady=(0, 6))
        steps = [
            ("1", "Remove ALL weight from ALL load cells"),
            ("2", "Press button on Arduino → enters calibration mode"),
            ("3", "Serial shows 'CALIBRATION MODE' message"),
            ("4", "Press button again → tares all 8 cells"),
            ("5", "For each cell (1-8):"),
            ("",  "   • Place the known mass on that cell"),
            ("",  "   • Press button when reading is stable"),
            ("6", "Arduino prints scale factor (g/count)"),
            ("7", "After cell 8, calibration is saved to RAM"),
            ("",  "   ⚠  RAM only – resets on power-off"),
        ]
        for num, text in steps:
            row_f = tk.Frame(left, bg=theme.BG)
            row_f.pack(fill=tk.X, pady=1)
            if num:
                tk.Label(row_f, text=f"{num}.", bg=theme.BG,
                         fg=theme.ACCENT, font=("Segoe UI", 11, "bold"),
                         width=3, anchor="e").pack(side=tk.LEFT)
            else:
                tk.Label(row_f, text="   ", bg=theme.BG,
                         width=3).pack(side=tk.LEFT)
            tk.Label(row_f, text=text, bg=theme.BG,
                     fg=theme.TEXT, font=theme.F_BODY,
                     anchor="w").pack(side=tk.LEFT)

        # ── Right: serial monitor ─────────────────────────────────────────────
        right = tk.Frame(body, bg=theme.BG)
        right.grid(row=0, column=1, sticky="nsew")

        ctrl = tk.Frame(right, bg=theme.BG)
        ctrl.pack(fill=tk.X, pady=(0, 6))
        tk.Label(ctrl, text="Serial output (selected Arduino)",
                 bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_HEADING).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="Clear", command=self._clear).pack(
            side=tk.RIGHT)

        self._txt = tk.Text(
            right, bg=theme.BG_SECONDARY, fg=theme.TEXT,
            font=theme.F_MONO, wrap="word", state="disabled",
            height=20,
        )
        vsb = ttk.Scrollbar(right, orient="vertical", command=self._txt.yview)
        self._txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt.pack(fill=tk.BOTH, expand=True)

        self._txt.tag_configure("cal",  foreground=theme.WARNING)
        self._txt.tag_configure("ok",   foreground=theme.SUCCESS)
        self._txt.tag_configure("err",  foreground=theme.DANGER)
        self._txt.tag_configure("info", foreground=theme.ACCENT)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._seen = {}
        self._poll()

    def on_hide(self):
        self._cancel_after()

    # ── Serial mirror ─────────────────────────────────────────────────────────

    def _poll(self):
        sel_text = self._ard_var.get()          # "Arduino N"
        try:
            aid = int(sel_text.split()[-1]) - 1
        except (ValueError, IndexError):
            aid = 0

        conn = self.manager.arduinos.get(aid)
        if conn and conn.connected:
            lines    = conn.get_raw_lines(200)
            seen_cnt = self._seen.get(aid, 0)
            new      = lines[seen_cnt:]
            if new:
                self._seen[aid] = seen_cnt + len(new)
                self._append(new)

        self._after_id = self.after(_POLL_MS, self._poll)

    def _append(self, lines: list[str]):
        self._txt.configure(state="normal")
        for line in lines:
            upper = line.upper()
            if "CALIBRAT" in upper or "TARE" in upper:
                tag = "cal"
            elif "ERROR" in upper or "TO" in upper or "DELTA=0" in upper:
                tag = "err"
            elif "DONE" in upper or "FINISH" in upper or "SCALE=" in upper:
                tag = "ok"
            else:
                tag = "info"
            self._txt.insert("end", line + "\n", tag)
        lc = int(self._txt.index("end-1c").split(".")[0])
        if lc > 1000:
            self._txt.delete("1.0", f"{lc - 1000}.0")
        self._txt.configure(state="disabled")
        self._txt.see("end")

    def _clear(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")
        self._seen = {}
