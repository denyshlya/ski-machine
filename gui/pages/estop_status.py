"""
gui/pages/estop_status.py – Software E-Stop control.

Hardware not yet wired; this is a software-only implementation.
When armed:  stops live updates, sends "STOP" to all connected Arduinos.
When cleared: resumes normal operation.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from gui import theme
from gui.pages.base_page import BasePage


class EStopPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header("⛔  E-Stop Status",
                          "Software emergency stop · hardware not yet wired")

        centre = tk.Frame(self, bg=theme.BG)
        centre.pack(expand=True)

        # ── Big status indicator ──────────────────────────────────────────────
        self._status_lbl = tk.Label(
            centre, text="● CLEAR",
            bg=theme.BG, fg=theme.SUCCESS, font=("Segoe UI", 42, "bold"))
        self._status_lbl.pack(pady=(0, 12))

        self._detail_lbl = tk.Label(
            centre,
            text="System is running normally.\nPress the button below to arm the E-Stop.",
            bg=theme.BG, fg=theme.TEXT_SEC, font=theme.F_BODY,
            justify="center")
        self._detail_lbl.pack(pady=(0, 28))

        # ── E-Stop button ─────────────────────────────────────────────────────
        self._estop_btn = tk.Button(
            centre,
            text="⛔  EMERGENCY STOP",
            bg=theme.DANGER, fg=theme.BG,
            font=("Segoe UI", 20, "bold"),
            width=26, height=3,
            relief="flat", cursor="hand2",
            activebackground="#d04060", activeforeground=theme.BG,
            command=self._arm,
        )
        self._estop_btn.pack(pady=(0, 20))

        # ── Clear button ──────────────────────────────────────────────────────
        self._clear_btn = ttk.Button(
            centre, text="✔  Clear E-Stop & resume",
            style="Success.TButton",
            command=self._clear, state="disabled")
        self._clear_btn.pack()

        # ── Note ──────────────────────────────────────────────────────────────
        tk.Label(
            centre,
            text="⚠  Hardware E-Stop is not wired yet.\n"
                 "This is a software-only control that sends STOP commands over serial.",
            bg=theme.BG, fg=theme.WARNING, font=theme.F_SMALL, justify="center",
        ).pack(pady=(32, 0))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._sync_state()

    def _sync_state(self):
        """Synchronise UI with manager.estop_active."""
        if self.manager.estop_active:
            self._status_lbl.configure(text="⛔ ARMED", fg=theme.DANGER)
            self._detail_lbl.configure(
                text="E-Stop is ARMED.\n"
                     "All live updates are paused and STOP was sent to all Arduinos.")
            self._estop_btn.configure(state="disabled", bg=theme.BG_TERTIARY)
            self._clear_btn.configure(state="normal")
        else:
            self._status_lbl.configure(text="● CLEAR", fg=theme.SUCCESS)
            self._detail_lbl.configure(
                text="System is running normally.\n"
                     "Press the button below to arm the E-Stop.")
            self._estop_btn.configure(state="normal", bg=theme.DANGER)
            self._clear_btn.configure(state="disabled")
        # propagate to top-bar indicator
        self.main_win.set_estop(self.manager.estop_active)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _arm(self):
        if messagebox.askyesno(
            "Arm E-Stop?",
            "This will send a STOP command to all connected Arduinos "
            "and pause all live readings.\n\nContinue?",
            icon="warning", parent=self,
        ):
            self.manager.trigger_estop()
            self._sync_state()

    def _clear(self):
        self.manager.clear_estop()
        self._sync_state()
