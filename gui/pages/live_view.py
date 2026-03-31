"""
gui/pages/live_view.py – Continuous 120-cell live chart.

• Refreshes at READ_INTERVAL_MS (default 300 ms)
• Record button saves a session CSV in Documents/SkiLoadcell/
• Shows total weight in large text
• Ski model text field is mandatory before recording starts
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional
import csv
from datetime import datetime

import config
from gui import theme
from gui.pages.base_page import BasePage
from gui.widgets.loadcell_chart import LoadcellChart
from core.data_store import make_save_path


class LiveViewPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._recording      = False
        self._record_path: Optional[Path] = None
        self._record_writer  = None
        self._record_file    = None
        self._record_rows    = 0
        self._build()

    def _build(self):
        self._page_header("📏  Live View",
                          "Continuous 120-cell readout · refreshes every 300 ms")

        # ── Controls bar ──────────────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=theme.BG)
        ctrl.pack(fill=tk.X, padx=28, pady=(10, 4))

        tk.Label(ctrl, text="Ski model:", bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_BODY).pack(side=tk.LEFT)
        self._model_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self._model_var, width=30).pack(
            side=tk.LEFT, padx=(6, 20))

        self._record_btn = ttk.Button(ctrl, text="⏺  Start recording",
                                      style="Success.TButton",
                                      command=self._toggle_record)
        self._record_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._rec_label = tk.Label(ctrl, text="", bg=theme.BG,
                                   fg=theme.DANGER, font=theme.F_BODY)
        self._rec_label.pack(side=tk.LEFT)

        # ── Weight display ────────────────────────────────────────────────────
        wt_frame = tk.Frame(self, bg=theme.BG)
        wt_frame.pack(fill=tk.X, padx=28)
        tk.Label(wt_frame, text="Total weight:", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(side=tk.LEFT)
        self._weight_lbl = tk.Label(wt_frame, text="— g", bg=theme.BG,
                                    fg=theme.ACCENT, font=theme.F_HUGE)
        self._weight_lbl.pack(side=tk.LEFT, padx=12)

        # ── Chart ─────────────────────────────────────────────────────────────
        self._chart = LoadcellChart(self, height_in=4.0)
        self._chart.pack(fill=tk.BOTH, expand=True, padx=28, pady=(8, 16))

        # ── Status strip ──────────────────────────────────────────────────────
        self._status_lbl = tk.Label(self, text="Paused – navigate here to start",
                                    bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
                                    font=theme.F_SMALL, anchor="w", padx=10)
        self._status_lbl.pack(fill=tk.X, side=tk.BOTTOM)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._tick()

    def on_hide(self):
        self._cancel_after()
        if self._recording:
            self._stop_recording()

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _tick(self):
        if self.manager.estop_active:
            self._status_lbl.configure(text="⛔ E-STOP ACTIVE – live view paused",
                                       fg=theme.DANGER)
            self._after_id = self.after(500, self._tick)
            return

        readings = self.manager.get_all_readings()
        total_w  = sum(v for v in readings if v is not None)

        self._chart.update_data(readings)
        self._weight_lbl.configure(text=f"{total_w:.2f} g")

        if self._recording:
            self._append_record(readings, total_w)
            self._rec_label.configure(
                text=f"● REC  {self._record_rows} rows  →  {self._record_path.name}")
            self._status_lbl.configure(
                text=f"Recording to: {self._record_path}", fg=theme.DANGER)
        else:
            self._status_lbl.configure(text="Live  ·  not recording", fg=theme.TEXT_MUTED)

        self._after_id = self.after(config.READ_INTERVAL_MS, self._tick)

    # ── Recording ─────────────────────────────────────────────────────────────

    def _toggle_record(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        model = self._model_var.get().strip()
        if not model:
            messagebox.showwarning("Ski model required",
                                   "Please enter a ski model before recording.",
                                   parent=self)
            return
        self._record_path  = make_save_path(model)
        self._record_file  = open(self._record_path, "w", newline="", encoding="utf-8")
        self._record_writer = csv.writer(self._record_file)
        # Write header
        self._record_writer.writerow(
            ["Timestamp", "Ski Model", "Total Weight (g)"]
            + [f"Cell {i + 1}" for i in range(config.TOTAL_CELLS)]
        )
        self._record_rows  = 0
        self._recording    = True
        self._record_btn.configure(text="⏹  Stop recording", style="Danger.TButton")

    def _stop_recording(self):
        self._recording = False
        if self._record_file:
            self._record_file.close()
            self._record_file   = None
            self._record_writer = None
        self._record_btn.configure(text="⏺  Start recording", style="Success.TButton")
        self._rec_label.configure(text="")
        if self._record_path:
            messagebox.showinfo("Recording saved",
                                f"Saved {self._record_rows} rows to:\n{self._record_path}",
                                parent=self)

    def _append_record(self, readings, total_w):
        if self._record_writer is None:
            return
        ts    = datetime.now().isoformat(timespec="milliseconds")
        model = self._model_var.get().strip()
        row   = ([ts, model, f"{total_w:.2f}"]
                 + [f"{v:.2f}" if v is not None else "N/A" for v in readings])
        self._record_writer.writerow(row)
        self._record_file.flush()
        self._record_rows += 1
