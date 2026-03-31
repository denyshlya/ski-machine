"""
gui/pages/base_page.py – Base class every page inherits from.
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from gui import theme

if TYPE_CHECKING:
    from core.arduino_manager import ArduinoManager
    from gui.main_window import MainWindow


class BasePage(ttk.Frame):
    """
    All pages extend this class.

    Parameters
    ----------
    parent      : parent widget (the page_area frame in MainWindow)
    manager     : shared ArduinoManager instance
    navigate    : callable(page_id: str) – switch active page
    main_win    : MainWindow reference (for e-stop indicator etc.)
    """

    def __init__(
        self,
        parent: tk.Widget,
        manager: "ArduinoManager",
        navigate: Callable[[str], None],
        main_win: "MainWindow",
    ):
        super().__init__(parent)
        self.configure(style="TFrame")
        self.manager  = manager
        self.navigate = navigate
        self.main_win = main_win
        self._after_id: str | None = None   # store scheduled after() IDs

    # ── Lifecycle hooks (override as needed) ──────────────────────────────────

    def on_show(self):
        """Called when this page becomes visible."""

    def on_hide(self):
        """Called when navigating away from this page."""
        self._cancel_after()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cancel_after(self):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _section_label(self, parent: tk.Widget, text: str) -> ttk.Label:
        lbl = ttk.Label(parent, text=text, font=theme.F_HEADING,
                        foreground=theme.ACCENT)
        return lbl

    def _card(self, parent: tk.Widget, **kwargs) -> ttk.Frame:
        f = ttk.Frame(parent, style="Card.TFrame", padding=16)
        return f

    def _page_header(self, title: str, subtitle: str = ""):
        hdr = tk.Frame(self, bg=theme.BG)
        hdr.pack(fill=tk.X, pady=(24, 6), padx=28)
        tk.Label(hdr, text=title, bg=theme.BG, fg=theme.TEXT,
                 font=theme.F_TITLE).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=theme.BG, fg=theme.TEXT_SEC,
                     font=theme.F_BODY).pack(anchor="w")
        ttk.Separator(self).pack(fill=tk.X, padx=28, pady=(4, 0))
