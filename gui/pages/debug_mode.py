"""
gui/pages/debug_mode.py – Raw serial monitor.

Shows raw bytes from one or all connected Arduinos.
Useful for verifying wiring, baud rate, calibration state.
"""
import tkinter as tk
from tkinter import ttk

import config
from gui import theme
from gui.pages.base_page import BasePage

_POLL_MS = 400


class DebugModePage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header("🐛  Debug Mode",
                          "Raw serial output from connected Arduinos")

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=theme.BG)
        ctrl.pack(fill=tk.X, padx=28, pady=(10, 6))

        tk.Label(ctrl, text="Monitor:", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(side=tk.LEFT)
        self._sel_var = tk.StringVar(value="All")
        choices = ["All"] + [f"Arduino {i + 1}" for i in range(config.NUM_ARDUINOS)]
        ttk.Combobox(ctrl, textvariable=self._sel_var,
                     values=choices, width=14, state="readonly"
                     ).pack(side=tk.LEFT, padx=(6, 20))

        ttk.Button(ctrl, text="🗑  Clear", command=self._clear
                   ).pack(side=tk.LEFT, padx=(0, 8))
        self._pause_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="Pause", variable=self._pause_var
                        ).pack(side=tk.LEFT)

        tk.Label(ctrl, text="⚠  Ensure A6 is HIGH on each Arduino to get output.",
                 bg=theme.BG, fg=theme.WARNING,
                 font=theme.F_SMALL).pack(side=tk.RIGHT)

        # ── Text area ─────────────────────────────────────────────────────────
        txt_frame = tk.Frame(self, bg=theme.BG)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 16))

        self._txt = tk.Text(
            txt_frame,
            bg=theme.BG_SECONDARY, fg=theme.TEXT,
            font=theme.F_MONO,
            wrap="none", state="disabled",
            selectbackground=theme.ACCENT, selectforeground=theme.BG,
        )
        vsb = ttk.Scrollbar(txt_frame, orient="vertical",
                            command=self._txt.yview)
        hsb = ttk.Scrollbar(txt_frame, orient="horizontal",
                            command=self._txt.xview)
        self._txt.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        self._txt.pack(fill=tk.BOTH, expand=True)

        # Tag colours
        self._txt.tag_configure("data",    foreground=theme.SUCCESS)
        self._txt.tag_configure("info",    foreground=theme.ACCENT)
        self._txt.tag_configure("timeout", foreground=theme.DANGER)

        self._seen_lines: dict[int, int] = {}  # aid -> num lines already shown

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self):
        self._seen_lines = {}
        self._poll()

    def on_hide(self):
        self._cancel_after()

    # ── Polling ───────────────────────────────────────────────────────────────

    def _poll(self):
        if not self._pause_var.get():
            sel = self._sel_var.get()
            for aid in range(config.NUM_ARDUINOS):
                if sel != "All" and sel != f"Arduino {aid + 1}":
                    continue
                conn = self.manager.arduinos.get(aid)
                if conn is None or not conn.connected:
                    continue
                all_lines = conn.get_raw_lines(200)
                seen      = self._seen_lines.get(aid, 0)
                new_lines = all_lines[seen:]
                if new_lines:
                    self._seen_lines[aid] = seen + len(new_lines)
                    self._append(aid, new_lines)

        self._after_id = self.after(_POLL_MS, self._poll)

    def _append(self, aid: int, lines: list[str]):
        self._txt.configure(state="normal")
        for line in lines:
            tag = "data" if "B1:" in line else "info"
            if "TO" in line:
                tag = "timeout"
            self._txt.insert("end", f"[A{aid + 1}] {line}\n", tag)
        # Keep buffer from growing forever (max 2000 lines)
        line_count = int(self._txt.index("end-1c").split(".")[0])
        if line_count > 2000:
            self._txt.delete("1.0", f"{line_count - 2000}.0")
        self._txt.configure(state="disabled")
        self._txt.see("end")

    def _clear(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")
        self._seen_lines = {}
