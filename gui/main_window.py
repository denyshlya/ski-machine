"""
gui/main_window.py

Main application window.
Layout:
  ┌─────────────────────────────────────────────────┐
  │  top bar  (title + e-stop indicator)             │
  ├──────────┬──────────────────────────────────────┤
  │ sidebar  │  page area                            │
  │          │                                       │
  │ Settings │                                       │
  │  ...     │                                       │
  │ Measure  │                                       │
  │  ...     │                                       │
  │          │                                       │
  │ [Exit]   │                                       │
  ├──────────┴──────────────────────────────────────┤
  │  status bar  (per-Arduino connection dots)       │
  └─────────────────────────────────────────────────┘
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import config
from gui import theme


# ─────────────────────────────────────────────────────────────────────────────

class MainWindow:
    def __init__(self, root: tk.Tk, manager):
        self.root    = root
        self.manager = manager

        self._pages: dict[str, tk.Frame] = {}
        self._current: str = ""
        self._nav_btns: dict[str, tk.Button] = {}

        root.title(f"{config.APP_TITLE}  v{config.APP_VERSION}")
        root.geometry("1440x860")
        root.minsize(1100, 680)
        theme.apply(root)

        self._build_top_bar()
        self._build_layout()
        self._build_status_bar()
        self._init_pages()
        self.navigate("home")
        self._status_tick()

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _build_top_bar(self):
        bar = tk.Frame(self.root, bg=theme.BG_SECONDARY, height=50)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        tk.Label(
            bar, text="⛷  Ski Load Cell System",
            bg=theme.BG_SECONDARY, fg=theme.TEXT, font=theme.F_TITLE,
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            bar, text=f"v{config.APP_VERSION}",
            bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED, font=theme.F_SMALL,
        ).pack(side=tk.LEFT)

        # E-stop indicator (clickable, top-right)
        self._estop_lbl = tk.Label(
            bar, text="● E-STOP: CLEAR",
            bg=theme.BG_SECONDARY, fg=theme.SUCCESS,
            font=("Segoe UI", 12, "bold"), cursor="hand2",
        )
        self._estop_lbl.pack(side=tk.RIGHT, padx=24)
        self._estop_lbl.bind("<Button-1>",
                             lambda _: self.navigate("estop_status"))

    # ── Main layout ───────────────────────────────────────────────────────────

    def _build_layout(self):
        container = tk.Frame(self.root, bg=theme.BG)
        container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self._sidebar = tk.Frame(container, bg=theme.BG_SECONDARY,
                                 width=theme.SIDEBAR_W)
        self._sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self._sidebar.pack_propagate(False)

        # 1-px separator
        tk.Frame(container, bg=theme.BG_TERTIARY, width=1).pack(
            fill=tk.Y, side=tk.LEFT)

        # Page area
        self._page_area = tk.Frame(container, bg=theme.BG)
        self._page_area.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar()

    def _build_sidebar(self):
        sb = self._sidebar

        # ── Home ──────────────────────────────────────────────────────────────
        self._nav_btn(sb, "home", "🏠  Home")
        self._sidebar_sep(sb)

        # ── Settings section ──────────────────────────────────────────────────
        self._sidebar_heading(sb, "SETTINGS")
        self._nav_btn(sb, "calibration_mode",    "  Calibration Mode")
        self._nav_btn(sb, "debug_mode",          "  Debug Mode")
        self._nav_btn(sb, "loadcell_calibration","  Load Cell Calibration")
        self._nav_btn(sb, "actuator_calibration","  Actuator Calibration")
        self._nav_btn(sb, "system_check",        "  System Check")
        self._nav_btn(sb, "actuator_manual",     "  Actuator Manual Control")
        self._nav_btn(sb, "estop_status",        "  E-Stop Status")
        self._nav_btn(sb, "system_reboot",       "  System Soft Reboot")
        self._sidebar_sep(sb)

        # ── Measurements section ───────────────────────────────────────────────
        self._sidebar_heading(sb, "MEASUREMENTS")
        self._nav_btn(sb, "single_measurement",  "  Single Measurement")
        self._nav_btn(sb, "live_view",           "  Live View")
        self._nav_btn(sb, "saved_measurements",  "  Saved Measurements")

        # Spacer
        tk.Frame(sb, bg=theme.BG_SECONDARY).pack(fill=tk.BOTH, expand=True)

        # ── Exit ──────────────────────────────────────────────────────────────
        tk.Frame(sb, bg=theme.BG_TERTIARY, height=1).pack(fill=tk.X)
        tk.Button(
            sb, text="⏻  Exit",
            bg=theme.BG_SECONDARY, fg=theme.DANGER,
            font=theme.F_BODY, bd=0, anchor="w",
            padx=18, pady=10, cursor="hand2",
            activebackground=theme.BG_TERTIARY,
            activeforeground=theme.DANGER,
            command=self._on_exit,
        ).pack(fill=tk.X)

    def _sidebar_heading(self, parent: tk.Widget, text: str):
        tk.Label(
            parent, text=text,
            bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
            font=("Segoe UI", 8, "bold"), anchor="w",
            padx=18, pady=6,
        ).pack(fill=tk.X)

    def _sidebar_sep(self, parent: tk.Widget):
        tk.Frame(parent, bg=theme.BG_TERTIARY, height=1).pack(fill=tk.X,
                                                               pady=2)

    def _nav_btn(self, parent: tk.Widget, page_id: str, label: str):
        btn = tk.Button(
            parent, text=label,
            bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
            font=theme.F_BODY, bd=0, anchor="w",
            padx=18, pady=9, cursor="hand2",
            activebackground=theme.BG_TERTIARY,
            activeforeground=theme.TEXT,
            command=lambda p=page_id: self.navigate(p),
        )
        btn.pack(fill=tk.X)
        self._nav_btns[page_id] = btn

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=theme.BG_SECONDARY, height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        tk.Label(bar, text="Arduinos:", bg=theme.BG_SECONDARY,
                 fg=theme.TEXT_MUTED, font=theme.F_SMALL).pack(side=tk.LEFT,
                                                                padx=(8, 4))
        self._dot_labels: list[tk.Label] = []
        for i in range(config.NUM_ARDUINOS):
            lbl = tk.Label(bar, text=f"A{i+1}",
                           bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
                           font=theme.F_SMALL)
            lbl.pack(side=tk.LEFT, padx=3)
            self._dot_labels.append(lbl)

        # Total weight in status bar
        tk.Frame(bar, bg=theme.BG_TERTIARY, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=8)
        tk.Label(bar, text="Total:", bg=theme.BG_SECONDARY,
                 fg=theme.TEXT_MUTED, font=theme.F_SMALL).pack(side=tk.LEFT)
        self._sb_weight = tk.Label(bar, text="—",
                                   bg=theme.BG_SECONDARY, fg=theme.ACCENT,
                                   font=theme.F_SMALL)
        self._sb_weight.pack(side=tk.LEFT, padx=(4, 0))

        # Save path
        tk.Label(
            bar,
            text=f"  ·  Saved to: {config.DOCUMENTS_DIR}",
            bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
            font=theme.F_SMALL,
        ).pack(side=tk.LEFT, padx=8)

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self, page_id: str):
        # Hide current page
        if self._current and self._current in self._pages:
            old = self._pages[self._current]
            old.pack_forget()
            if hasattr(old, "on_hide"):
                old.on_hide()

        # Highlight new button
        for pid, btn in self._nav_btns.items():
            if pid == page_id:
                btn.configure(
                    bg=theme.BG_TERTIARY, fg=theme.ACCENT,
                    font=("Segoe UI", 11, "bold"))
            else:
                btn.configure(
                    bg=theme.BG_SECONDARY, fg=theme.TEXT_MUTED,
                    font=theme.F_BODY)

        # Show new page
        self._current = page_id
        page = self._pages.get(page_id)
        if page:
            page.pack(fill=tk.BOTH, expand=True)
            if hasattr(page, "on_show"):
                page.on_show()

    # ── Page registration ─────────────────────────────────────────────────────

    def _init_pages(self):
        from gui.pages.home                 import HomePage
        from gui.pages.calibration_mode     import CalibrationModePage
        from gui.pages.debug_mode           import DebugModePage
        from gui.pages.loadcell_calibration import LoadcellCalibrationPage
        from gui.pages.actuator_calibration import ActuatorCalibrationPage
        from gui.pages.system_check         import SystemCheckPage
        from gui.pages.actuator_manual      import ActuatorManualPage
        from gui.pages.estop_status         import EStopPage
        from gui.pages.system_reboot        import SystemRebootPage
        from gui.pages.saved_measurements   import SavedMeasurementsPage
        from gui.pages.single_measurement   import SingleMeasurementPage
        from gui.pages.live_view            import LiveViewPage

        page_map = {
            "home":                  HomePage,
            "calibration_mode":      CalibrationModePage,
            "debug_mode":            DebugModePage,
            "loadcell_calibration":  LoadcellCalibrationPage,
            "actuator_calibration":  ActuatorCalibrationPage,
            "system_check":          SystemCheckPage,
            "actuator_manual":       ActuatorManualPage,
            "estop_status":          EStopPage,
            "system_reboot":         SystemRebootPage,
            "saved_measurements":    SavedMeasurementsPage,
            "single_measurement":    SingleMeasurementPage,
            "live_view":             LiveViewPage,
        }

        for page_id, cls in page_map.items():
            page = cls(self._page_area, self.manager, self.navigate, self)
            self._pages[page_id] = page

    # ── Public: e-stop indicator ──────────────────────────────────────────────

    def set_estop(self, active: bool):
        if active:
            self._estop_lbl.configure(text="⛔ E-STOP: ARMED", fg=theme.DANGER)
        else:
            self._estop_lbl.configure(text="● E-STOP: CLEAR", fg=theme.SUCCESS)

    # ── Status bar polling ────────────────────────────────────────────────────

    def _status_tick(self):
        statuses = self.manager.get_status()
        for i, lbl in enumerate(self._dot_labels):
            s = statuses.get(i, {})
            if s.get("connected"):
                lbl.configure(fg=theme.SUCCESS)
            elif s.get("port"):
                lbl.configure(fg=theme.DANGER)
            else:
                lbl.configure(fg=theme.TEXT_MUTED)

        total_w = self.manager.get_total_weight()
        self._sb_weight.configure(text=f"{total_w:.1f} g")

        # Sync e-stop indicator
        self.set_estop(self.manager.estop_active)

        self.root.after(2000, self._status_tick)

    # ── Exit ──────────────────────────────────────────────────────────────────

    def _on_exit(self):
        if messagebox.askyesno("Exit", "Close Ski Load Cell System?",
                               parent=self.root):
            # Stop live view if running
            if self._current in self._pages:
                page = self._pages[self._current]
                if hasattr(page, "on_hide"):
                    page.on_hide()
            self.manager.disconnect_all()
            self.root.quit()
            self.root.destroy()
