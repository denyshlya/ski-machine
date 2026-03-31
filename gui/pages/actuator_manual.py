"""
gui/pages/actuator_manual.py

Manual control panel for DC linear actuators.
Hardware not yet wired – full UI skeleton ready for future use.
"""
import tkinter as tk
from tkinter import ttk

from gui import theme
from gui.pages.base_page import BasePage

_NUM_ACTUATORS = 8   # expected number per rig


class ActuatorManualPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header("🕹  Actuator Manual Control",
                          "Individual extend / retract / stop per actuator")

        # Hardware-not-connected banner
        banner = tk.Frame(self, bg="#3d2800", pady=8)
        banner.pack(fill=tk.X, padx=28, pady=(8, 12))
        tk.Label(banner,
                 text="⚠  Actuator hardware not yet wired  –  controls are disabled",
                 bg="#3d2800", fg=theme.WARNING,
                 font=("Segoe UI", 11, "bold")).pack()

        # Master stop button (top)
        master_frame = tk.Frame(self, bg=theme.BG)
        master_frame.pack(fill=tk.X, padx=28, pady=(0, 12))
        tk.Button(
            master_frame, text="⏹  STOP ALL",
            bg=theme.DANGER, fg=theme.BG,
            font=("Segoe UI", 14, "bold"),
            relief="flat", state="disabled",
            cursor="hand2", padx=24, pady=8,
        ).pack(side=tk.LEFT)

        # Per-actuator controls grid
        grid = tk.Frame(self, bg=theme.BG)
        grid.pack(fill=tk.X, padx=28)

        headers = ["Actuator", "Extend", "Retract", "Stop", "Status"]
        for col, h in enumerate(headers):
            tk.Label(grid, text=h, bg=theme.BG, fg=theme.TEXT_MUTED,
                     font=("Segoe UI", 9, "bold")).grid(
                         row=0, column=col, sticky="w",
                         padx=(0, 20), pady=(0, 6))

        for i in range(_NUM_ACTUATORS):
            row = i + 1
            tk.Label(grid, text=f"Actuator {i + 1}", bg=theme.BG,
                     fg=theme.TEXT, font=theme.F_BODY).grid(
                         row=row, column=0, sticky="w", padx=(0, 20), pady=3)

            for col, label in [(1, "▶ Extend"), (2, "◀ Retract"), (3, "■ Stop")]:
                ttk.Button(grid, text=label, state="disabled").grid(
                    row=row, column=col, padx=(0, 12), pady=3)

            tk.Label(grid, text="— not connected —",
                     bg=theme.BG, fg=theme.TEXT_MUTED,
                     font=theme.F_SMALL).grid(
                         row=row, column=4, sticky="w")

        # Speed slider (disabled)
        spd = tk.Frame(self, bg=theme.BG)
        spd.pack(fill=tk.X, padx=28, pady=(16, 0))
        tk.Label(spd, text="Speed (PWM %):", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(side=tk.LEFT)
        ttk.Scale(spd, from_=0, to=100, orient="horizontal",
                  state="disabled", length=200).pack(side=tk.LEFT, padx=8)
