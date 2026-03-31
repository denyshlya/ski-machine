"""
gui/pages/system_reboot.py

Soft reboot: disconnect all serial ports, pause, reconnect.
Useful after a crash or USB re-plug without restarting the exe.
"""
import threading
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage


class SystemRebootPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._running = False
        self._build()

    def _build(self):
        self._page_header("🔄  System Soft Reboot",
                          "Close and reopen all serial connections without restarting the app")

        centre = tk.Frame(self, bg=theme.BG)
        centre.pack(expand=True)

        tk.Label(
            centre,
            text=(
                "A soft reboot:\n\n"
                "  1. Disconnects all 15 Arduino serial ports\n"
                "  2. Waits 1.5 seconds\n"
                "  3. Reconnects using the stored COM port config\n\n"
                "Use this if Arduinos stopped responding or a USB\n"
                "cable was briefly unplugged and re-plugged."
            ),
            bg=theme.BG, fg=theme.TEXT_SEC,
            font=theme.F_BODY, justify="left",
        ).pack(pady=(0, 24))

        self._btn = ttk.Button(
            centre, text="🔄  Reboot all connections",
            style="Primary.TButton",
            command=self._do_reboot)
        self._btn.pack(pady=(0, 16))

        self._progress = ttk.Progressbar(centre, mode="indeterminate", length=300)
        self._progress.pack(pady=(0, 10))

        self._log = tk.Text(
            centre, height=12, width=60,
            bg=theme.BG_SECONDARY, fg=theme.TEXT,
            font=theme.F_MONO, state="disabled")
        self._log.pack()
        self._log.tag_configure("ok",   foreground=theme.SUCCESS)
        self._log.tag_configure("err",  foreground=theme.DANGER)
        self._log.tag_configure("info", foreground=theme.ACCENT)

    # ── Reboot logic ──────────────────────────────────────────────────────────

    def _do_reboot(self):
        if self._running:
            return
        self._running = True
        self._btn.configure(state="disabled")
        self._progress.start(12)
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        threading.Thread(target=self._reboot_thread, daemon=True).start()

    def _reboot_thread(self):
        def log(msg: str, tag: str = "info"):
            self.after(0, lambda: self._append_log(msg, tag))

        def progress(step: int, msg: str):
            log(msg)

        log("Starting soft reboot…")
        results = self.manager.reconnect_all(progress_cb=progress)

        ok  = sum(1 for v in results.values() if v)
        tot = len(results)
        for aid, success in results.items():
            port = self.manager._ports.get(aid, "?")
            if success:
                log(f"  Arduino {aid + 1}  ({port})  → connected", "ok")
            else:
                conn = self.manager.arduinos.get(aid)
                err  = conn.error_msg if conn else "unknown"
                log(f"  Arduino {aid + 1}  ({port})  → FAILED: {err}", "err")

        log(f"\nReboot complete: {ok}/{tot} Arduinos connected.",
            "ok" if ok == tot else "err")
        self.after(0, self._reboot_done)

    def _reboot_done(self):
        self._progress.stop()
        self._btn.configure(state="normal")
        self._running = False

    def _append_log(self, msg: str, tag: str = "info"):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n", tag)
        self._log.configure(state="disabled")
        self._log.see("end")
