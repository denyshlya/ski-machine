"""
gui/pages/system_check.py

Displays connection status for all 15 Arduinos.
Allows editing COM port assignments and reconnecting.
"""
import time
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage


class SystemCheckPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._port_vars: dict[int, tk.StringVar] = {}
        self._build()

    def _build(self):
        self._page_header("🔧  System Check",
                          "View connection status · configure COM ports · reconnect")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=28, pady=12)

        # ── COM port config grid ───────────────────────────────────────────────
        tk.Label(body, text="COM port assignments",
                 bg=theme.BG, fg=theme.TEXT_SEC,
                 font=theme.F_HEADING).grid(row=0, column=0, sticky="w",
                                            columnspan=6, pady=(0, 6))

        headers = ["Arduino", "COM port", "Status", "Last seen", "Error"]
        for col, h in enumerate(headers):
            tk.Label(body, text=h, bg=theme.BG, fg=theme.TEXT_MUTED,
                     font=("Segoe UI", 9, "bold")).grid(
                         row=1, column=col, sticky="w", padx=(0, 16), pady=(0, 4))

        self._status_rows: dict[int, dict[str, tk.Label]] = {}

        available_ports = self.manager.list_available_ports()

        for i in range(config.NUM_ARDUINOS):
            row = i + 2
            tk.Label(body, text=f"Arduino {i + 1}", bg=theme.BG,
                     fg=theme.TEXT, font=theme.F_BODY).grid(
                         row=row, column=0, sticky="w", padx=(0, 16), pady=2)

            # COM port combobox
            var = tk.StringVar(value=self.manager._ports.get(i, ""))
            self._port_vars[i] = var
            cb = ttk.Combobox(body, textvariable=var,
                              values=[""] + available_ports, width=10)
            cb.grid(row=row, column=1, sticky="w", padx=(0, 16), pady=2)

            # Status indicator
            stat_lbl = tk.Label(body, text="—", bg=theme.BG,
                                fg=theme.TEXT_MUTED, font=theme.F_BODY)
            stat_lbl.grid(row=row, column=2, sticky="w", padx=(0, 16))

            # Last seen
            last_lbl = tk.Label(body, text="—", bg=theme.BG,
                                fg=theme.TEXT_MUTED, font=theme.F_SMALL)
            last_lbl.grid(row=row, column=3, sticky="w", padx=(0, 16))

            # Error message
            err_lbl = tk.Label(body, text="", bg=theme.BG,
                               fg=theme.DANGER, font=theme.F_SMALL, width=30,
                               anchor="w")
            err_lbl.grid(row=row, column=4, sticky="w")

            self._status_rows[i] = {
                "status": stat_lbl,
                "last":   last_lbl,
                "error":  err_lbl,
            }

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = config.NUM_ARDUINOS + 2 + 1
        btn_frame = tk.Frame(body, bg=theme.BG)
        btn_frame.grid(row=btn_row, column=0, columnspan=6,
                       sticky="w", pady=(14, 0))

        ttk.Button(btn_frame, text="💾  Save port config",
                   command=self._save_ports).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🔄  Reconnect all",
                   style="Primary.TButton",
                   command=self._reconnect).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🔍  Refresh available ports",
                   command=self._refresh_ports).pack(side=tk.LEFT)

        self._log_lbl = tk.Label(body, text="", bg=theme.BG,
                                 fg=theme.TEXT_MUTED, font=theme.F_SMALL)
        self._log_lbl.grid(row=btn_row + 1, column=0, columnspan=6,
                           sticky="w", pady=(6, 0))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._update_status()

    def on_hide(self):
        self._cancel_after()

    def _update_status(self):
        statuses = self.manager.get_status()
        now = time.time()
        for i, row_widgets in self._status_rows.items():
            s = statuses.get(i, {})
            if s.get("connected"):
                row_widgets["status"].configure(text="✓ Connected",
                                                fg=theme.SUCCESS)
                last_s = now - s.get("last_update", now)
                row_widgets["last"].configure(
                    text=f"{last_s:.0f}s ago", fg=theme.TEXT_MUTED)
                row_widgets["error"].configure(text="")
            elif s.get("port"):
                row_widgets["status"].configure(text="✗ Error", fg=theme.DANGER)
                row_widgets["last"].configure(text="—", fg=theme.TEXT_MUTED)
                row_widgets["error"].configure(text=s.get("error", ""))
            else:
                row_widgets["status"].configure(text="— Not configured",
                                                fg=theme.TEXT_MUTED)
                row_widgets["last"].configure(text="—", fg=theme.TEXT_MUTED)
                row_widgets["error"].configure(text="")
        self._after_id = self.after(3000, self._update_status)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _save_ports(self):
        ports = {i: var.get().strip()
                 for i, var in self._port_vars.items()
                 if var.get().strip()}
        config.save_port_config(ports)
        self.manager.set_ports(ports)
        self._log_lbl.configure(
            text="COM port config saved.  Click 'Reconnect all' to apply.",
            fg=theme.WARNING)

    def _reconnect(self):
        self._log_lbl.configure(text="Reconnecting…", fg=theme.INFO)
        self.update_idletasks()

        def progress(step, msg):
            self._log_lbl.configure(text=msg, fg=theme.INFO)
            self.update_idletasks()

        results = self.manager.reconnect_all(progress_cb=progress)
        ok  = sum(1 for v in results.values() if v)
        tot = len(results)
        self._log_lbl.configure(
            text=f"Reconnect complete: {ok}/{tot} connected.",
            fg=theme.SUCCESS if ok == tot else theme.WARNING)
        self._update_status()

    def _refresh_ports(self):
        ports = [""] + self.manager.list_available_ports()
        # Update all comboboxes
        for widget in self.winfo_children():
            self._update_comboboxes(widget, ports)
        self._log_lbl.configure(
            text=f"Found: {', '.join(ports[1:]) or 'none'}", fg=theme.TEXT_SEC)

    def _update_comboboxes(self, widget, ports):
        if isinstance(widget, ttk.Combobox):
            widget["values"] = ports
        for child in widget.winfo_children():
            self._update_comboboxes(child, ports)
