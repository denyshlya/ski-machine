"""
gui/pages/home.py – Dashboard / welcome page.
"""
import time
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header(
            "⛷  Ski Load Cell System",
            f"v{config.APP_VERSION}  ·  {config.NUM_ARDUINOS} Arduinos  ·  "
            f"{config.TOTAL_CELLS} load cells",
        )

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=28, pady=16)

        # ── Status grid ───────────────────────────────────────────────────────
        tk.Label(body, text="Arduino status", bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_HEADING).grid(row=0, column=0, sticky="w",
                                            pady=(0, 8))

        grid_frame = tk.Frame(body, bg=theme.BG)
        grid_frame.grid(row=1, column=0, sticky="nw")

        self._status_cells: list[tk.Label] = []
        for i in range(config.NUM_ARDUINOS):
            row, col = divmod(i, 5)
            lbl = tk.Label(
                grid_frame,
                text=f"A{i + 1}\n—",
                bg=theme.BG_TERTIARY, fg=theme.TEXT_MUTED,
                font=theme.F_SMALL, width=9, height=3,
                relief="flat",
            )
            lbl.grid(row=row, column=col, padx=4, pady=4)
            self._status_cells.append(lbl)

        # ── Summary cards ──────────────────────────────────────────────────────
        cards = tk.Frame(body, bg=theme.BG)
        cards.grid(row=1, column=1, sticky="nw", padx=(32, 0))
        body.columnconfigure(1, weight=1)

        self._total_lbl = self._stat_card(
            cards, "Total weight", "0.00 g", theme.ACCENT, row=0)
        self._conn_lbl  = self._stat_card(
            cards, "Connected", "0 / 15", theme.SUCCESS, row=1)
        self._cells_lbl = self._stat_card(
            cards, "Active cells", "0 / 120", theme.INFO, row=2)

        # ── Quick-nav buttons ──────────────────────────────────────────────────
        nav_frame = tk.Frame(body, bg=theme.BG)
        nav_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(24, 0))
        tk.Label(nav_frame, text="Quick actions", bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_HEADING).pack(anchor="w", pady=(0, 8))

        btns = tk.Frame(nav_frame, bg=theme.BG)
        btns.pack(anchor="w")
        for label, page in [
            ("📏  Live View",          "live_view"),
            ("📸  Single Measurement", "single_measurement"),
            ("📁  Saved Measurements", "saved_measurements"),
            ("🔧  System Check",       "system_check"),
        ]:
            ttk.Button(btns, text=label, style="Primary.TButton",
                       command=lambda p=page: self.navigate(p)
                       ).pack(side=tk.LEFT, padx=(0, 10))

    def _stat_card(self, parent, title, initial, color, row):
        card = tk.Frame(parent, bg=theme.BG_CARD, padx=20, pady=12)
        card.grid(row=row, column=0, sticky="ew", pady=4)
        tk.Label(card, text=title, bg=theme.BG_CARD, fg=theme.TEXT_SEC,
                 font=theme.F_SMALL).pack(anchor="w")
        lbl = tk.Label(card, text=initial, bg=theme.BG_CARD, fg=color,
                       font=theme.F_LARGE)
        lbl.pack(anchor="w")
        return lbl

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._refresh()

    def on_hide(self):
        self._cancel_after()

    def _refresh(self):
        statuses = self.manager.get_status()
        connected = sum(1 for s in statuses.values() if s["connected"])

        # Update grid cells
        for i, lbl in enumerate(self._status_cells):
            s = statuses.get(i, {})
            if s.get("connected"):
                lbl.configure(text=f"A{i+1}\n{s['port']}",
                              bg=theme.BG_CARD, fg=theme.SUCCESS)
            elif s.get("port"):
                lbl.configure(text=f"A{i+1}\n✗ ERR",
                              bg=theme.BG_CARD, fg=theme.DANGER)
            else:
                lbl.configure(text=f"A{i+1}\n—",
                              bg=theme.BG_TERTIARY, fg=theme.TEXT_MUTED)

        # Update summary
        readings = self.manager.get_all_readings()
        active   = sum(1 for v in readings if v is not None)
        total_w  = sum(v for v in readings if v is not None)

        self._conn_lbl.configure(text=f"{connected} / {config.NUM_ARDUINOS}")
        self._cells_lbl.configure(text=f"{active} / {config.TOTAL_CELLS}")
        self._total_lbl.configure(text=f"{total_w:.2f} g")

        self._after_id = self.after(2000, self._refresh)
