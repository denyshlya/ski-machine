"""
gui/pages/single_measurement.py

Takes a one-shot snapshot of all 120 cells.
User enters ski model, clicks "Take measurement", reviews chart, then saves.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gui import theme
from gui.pages.base_page import BasePage
from gui.widgets.loadcell_chart import LoadcellChart
from core import data_store


class SingleMeasurementPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._last_readings: list[Optional[float]] = []
        self._last_total: float = 0.0
        self._build()

    def _build(self):
        self._page_header("📸  Single Measurement",
                          "Enter ski model, take snapshot, then save to CSV")

        # ── Input row ─────────────────────────────────────────────────────────
        row = tk.Frame(self, bg=theme.BG)
        row.pack(fill=tk.X, padx=28, pady=(12, 6))

        tk.Label(row, text="Ski model:", bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_BODY).pack(side=tk.LEFT)
        self._model_var = tk.StringVar()
        ttk.Entry(row, textvariable=self._model_var, width=32).pack(
            side=tk.LEFT, padx=(6, 20))

        ttk.Button(row, text="📸  Take measurement", style="Primary.TButton",
                   command=self._take).pack(side=tk.LEFT, padx=(0, 10))
        self._save_btn = ttk.Button(row, text="💾  Save CSV", style="Success.TButton",
                                    command=self._save, state="disabled")
        self._save_btn.pack(side=tk.LEFT)

        # ── Weight + metadata ──────────────────────────────────────────────────
        info = tk.Frame(self, bg=theme.BG)
        info.pack(fill=tk.X, padx=28, pady=(0, 4))

        tk.Label(info, text="Total weight:", bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_BODY).pack(side=tk.LEFT)
        self._weight_lbl = tk.Label(info, text="— g", bg=theme.BG,
                                    fg=theme.ACCENT, font=theme.F_LARGE)
        self._weight_lbl.pack(side=tk.LEFT, padx=10)

        self._status_lbl = tk.Label(info, text="No measurement taken yet",
                                    bg=theme.BG, fg=theme.TEXT_MUTED,
                                    font=theme.F_SMALL)
        self._status_lbl.pack(side=tk.LEFT, padx=10)

        # ── Chart ─────────────────────────────────────────────────────────────
        self._chart = LoadcellChart(self, height_in=4.0)
        self._chart.pack(fill=tk.BOTH, expand=True, padx=28, pady=(4, 16))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _take(self):
        if self.manager.estop_active:
            messagebox.showerror("E-Stop active",
                                 "Cannot take measurement while E-Stop is armed.",
                                 parent=self)
            return

        readings = self.manager.get_all_readings()
        total_w  = sum(v for v in readings if v is not None)
        active   = sum(1 for v in readings if v is not None)

        self._last_readings = readings
        self._last_total    = total_w

        self._chart.update_data(readings)
        self._weight_lbl.configure(text=f"{total_w:.2f} g")
        self._status_lbl.configure(
            text=f"{active} / 120 cells active", fg=theme.TEXT_SEC)
        self._save_btn.configure(state="normal")

    def _save(self):
        model = self._model_var.get().strip()
        if not model:
            messagebox.showwarning("Ski model required",
                                   "Please enter a ski model before saving.",
                                   parent=self)
            return
        if not self._last_readings:
            messagebox.showwarning("No data",
                                   "Take a measurement first.", parent=self)
            return
        path = data_store.save_measurement(
            model, self._last_readings, self._last_total)
        self._status_lbl.configure(
            text=f"Saved → {path.name}", fg=theme.SUCCESS)
        messagebox.showinfo("Saved", f"Measurement saved to:\n{path}", parent=self)
