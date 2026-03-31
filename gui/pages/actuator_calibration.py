"""
gui/pages/actuator_calibration.py

DC linear actuator calibration.
Hardware not yet wired – UI is prepared for future implementation.
"""
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage


class ActuatorCalibrationPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header("⚙  Actuator Calibration",
                          "DC linear actuator travel limits and zero-position setup")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(expand=True)

        tk.Label(
            body,
            text="⚠  Hardware not yet connected",
            bg=theme.BG, fg=theme.WARNING,
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 12))

        tk.Label(
            body,
            text=(
                "DC linear actuator wiring is not yet installed.\n\n"
                "Once wired, this screen will provide:\n"
                "  • Individual actuator travel limit calibration\n"
                "  • Zero-position (home) detection\n"
                "  • Force vs. position characterisation\n"
                "  • Per-actuator fault detection\n\n"
                "Connect actuator hardware and update config.py,\n"
                "then this page will enable automatically."
            ),
            bg=theme.BG, fg=theme.TEXT_SEC,
            font=theme.F_BODY, justify="left",
        ).pack()

        # Pre-built UI elements (disabled until hardware is connected)
        frame = tk.Frame(body, bg=theme.BG)
        frame.pack(pady=24)

        for i in range(1, 9):      # placeholder for 8 actuators
            row = tk.Frame(frame, bg=theme.BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"Actuator {i}", bg=theme.BG,
                     fg=theme.TEXT_MUTED, font=theme.F_BODY, width=12,
                     anchor="w").pack(side=tk.LEFT)
            ttk.Button(row, text="Home", state="disabled").pack(side=tk.LEFT, padx=4)
            ttk.Button(row, text="Calibrate limits",
                       state="disabled").pack(side=tk.LEFT, padx=4)
            tk.Label(row, text="— not connected —", bg=theme.BG,
                     fg=theme.TEXT_MUTED, font=theme.F_SMALL).pack(side=tk.LEFT,
                                                                    padx=8)
