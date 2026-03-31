"""
gui/theme.py – Color palette, fonts, and ttk style definitions.
"""
import tkinter as tk
from tkinter import ttk

# ── Palette ───────────────────────────────────────────────────────────────────
BG           = "#1e1e2e"
BG_SECONDARY = "#181825"
BG_TERTIARY  = "#313244"
BG_CARD      = "#24273a"

TEXT         = "#cdd6f4"
TEXT_SEC     = "#a6adc8"
TEXT_MUTED   = "#6c7086"

ACCENT       = "#89b4fa"
SUCCESS      = "#a6e3a1"
WARNING      = "#f9e2af"
DANGER       = "#f38ba8"
INFO         = "#89dceb"

SIDEBAR_W    = 230

# ── Fonts ─────────────────────────────────────────────────────────────────────
F_TITLE   = ("Segoe UI", 18, "bold")
F_HEADING = ("Segoe UI", 13, "bold")
F_BODY    = ("Segoe UI", 11)
F_SMALL   = ("Segoe UI", 9)
F_MONO    = ("Consolas", 10)
F_HUGE    = ("Segoe UI", 36, "bold")
F_LARGE   = ("Segoe UI", 22, "bold")


def apply(root: tk.Tk):
    """Apply the dark theme to the whole application."""
    root.configure(bg=BG)
    s = ttk.Style(root)
    s.theme_use("clam")

    # Base
    s.configure(".",
        background=BG, foreground=TEXT,
        font=F_BODY, borderwidth=0, focusthickness=0)

    s.configure("TFrame",   background=BG)
    s.configure("TLabel",   background=BG, foreground=TEXT, font=F_BODY)
    s.configure("TPanedwindow", background=BG)

    # Entry / Combobox
    s.configure("TEntry",
        fieldbackground=BG_TERTIARY, foreground=TEXT,
        insertcolor=TEXT, padding=6)
    s.configure("TCombobox",
        fieldbackground=BG_TERTIARY, foreground=TEXT,
        selectbackground=ACCENT, selectforeground=BG,
        arrowcolor=TEXT_SEC)
    s.map("TCombobox", fieldbackground=[("readonly", BG_TERTIARY)])

    # Standard button
    s.configure("TButton",
        background=BG_TERTIARY, foreground=TEXT,
        font=F_BODY, padding=(12, 6), relief="flat")
    s.map("TButton",
        background=[("active", ACCENT), ("pressed", "#6ea3e8")],
        foreground=[("active", BG)])

    # Accent / primary button
    s.configure("Primary.TButton",
        background=ACCENT, foreground=BG,
        font=("Segoe UI", 11, "bold"), padding=(14, 7))
    s.map("Primary.TButton",
        background=[("active", "#6ea3e8")])

    # Danger (e-stop) button
    s.configure("Danger.TButton",
        background=DANGER, foreground=BG,
        font=("Segoe UI", 16, "bold"), padding=(24, 14))
    s.map("Danger.TButton",
        background=[("active", "#e06080")])

    # Success button
    s.configure("Success.TButton",
        background=SUCCESS, foreground=BG,
        font=F_BODY, padding=(12, 6))
    s.map("Success.TButton",
        background=[("active", "#80c97e")])

    # Warning button
    s.configure("Warning.TButton",
        background=WARNING, foreground=BG,
        font=F_BODY, padding=(12, 6))
    s.map("Warning.TButton",
        background=[("active", "#d9be7a")])

    # Sidebar labels (section headings)
    s.configure("Sidebar.TLabel",
        background=BG_SECONDARY, foreground=TEXT_MUTED,
        font=("Segoe UI", 8, "bold"), padding=(18, 10, 18, 4))

    # Card frame
    s.configure("Card.TFrame", background=BG_CARD)

    # Treeview
    s.configure("Treeview",
        background=BG_SECONDARY, foreground=TEXT,
        fieldbackground=BG_SECONDARY, rowheight=30, borderwidth=0)
    s.configure("Treeview.Heading",
        background=BG_TERTIARY, foreground=TEXT_SEC,
        font=("Segoe UI", 10, "bold"), borderwidth=0, relief="flat")
    s.map("Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", BG)])

    # Scrollbar
    s.configure("TScrollbar",
        background=BG_TERTIARY, troughcolor=BG_SECONDARY,
        borderwidth=0, arrowcolor=TEXT_SEC, relief="flat")
    s.map("TScrollbar", background=[("active", ACCENT)])

    # Separator
    s.configure("TSeparator", background=BG_TERTIARY)

    # Progressbar
    s.configure("TProgressbar",
        troughcolor=BG_TERTIARY, background=ACCENT,
        borderwidth=0, thickness=6)
