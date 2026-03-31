"""
gui/widgets/loadcell_chart.py

Reusable bar-chart widget showing all 120 load cells in a single left-to-right row.
Bars are colour-coded by load magnitude.
Arduino group boundaries are marked with dashed vertical lines.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker

import config
from gui import theme


class LoadcellChart(ttk.Frame):
    """
    Drop-in tkinter widget.  Call update_data(readings) with a list of 120
    Optional[float] values to refresh the chart.
    """

    # Colour thresholds (grams)
    _THRESH_LOW  = 50
    _THRESH_MID  = 200
    _THRESH_HIGH = 400

    def __init__(self, parent: tk.Widget, height_in: float = 3.8, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)

        self.fig = Figure(
            figsize=(16, height_in),
            facecolor=theme.BG_CARD,
            tight_layout={"pad": 1.4},
        )
        self.ax = self.fig.add_subplot(111)
        self._configure_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Draw empty chart on creation
        self.update_data([None] * config.TOTAL_CELLS)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_data(self, readings: list[Optional[float]]):
        """Refresh chart.  `readings` must have length TOTAL_CELLS (120)."""
        values = [v if v is not None else 0.0 for v in readings]
        colors = [self._color_for(v, r) for v, r in zip(values, readings)]

        self.ax.cla()
        self._configure_axes()

        x = list(range(1, config.TOTAL_CELLS + 1))
        self.ax.bar(x, values, color=colors, width=0.72, zorder=2)

        # Dynamic Y ceiling
        max_v = max(values) if any(v > 0 for v in values) else 0
        self.ax.set_ylim(0, max(100.0, max_v * 1.18))

        # Arduino group labels near top
        y_top = self.ax.get_ylim()[1]
        for i in range(config.NUM_ARDUINOS):
            cx = i * config.CELLS_PER_ARDUINO + config.CELLS_PER_ARDUINO / 2 + 1
            self.ax.text(
                cx, y_top * 0.96,
                f"A{i + 1}",
                color=theme.TEXT_MUTED,
                ha="center", va="top", fontsize=6.5,
            )

        self.canvas.draw_idle()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _configure_axes(self):
        ax = self.ax
        ax.set_facecolor(theme.BG_CARD)
        ax.tick_params(axis="both", colors=theme.TEXT_MUTED, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(theme.BG_TERTIARY)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlabel("Load cell  (1 → 120)", color=theme.TEXT_SEC, fontsize=9)
        ax.set_ylabel("Weight (g)", color=theme.TEXT_SEC, fontsize=9)
        ax.set_xlim(0, config.TOTAL_CELLS + 1)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(8))

        # Dashed separators between Arduinos
        for i in range(1, config.NUM_ARDUINOS):
            ax.axvline(
                x=i * config.CELLS_PER_ARDUINO + 0.5,
                color=theme.BG_TERTIARY,
                linewidth=0.9, linestyle="--", zorder=1,
            )

    @staticmethod
    def _color_for(value: float, reading: Optional[float]) -> str:
        if reading is None:
            return theme.TEXT_MUTED           # offline / timeout
        if value < LoadcellChart._THRESH_LOW:
            return theme.ACCENT               # blue  – light load
        if value < LoadcellChart._THRESH_MID:
            return theme.SUCCESS              # green – medium load
        if value < LoadcellChart._THRESH_HIGH:
            return theme.WARNING              # amber – heavy load
        return theme.DANGER                   # red   – very heavy
