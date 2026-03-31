"""
gui/pages/saved_measurements.py

Browse all saved CSVs in ~/Documents/SkiLoadcell/.
Click a row to load the full measurement and render the 120-cell chart.
"""
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

import config
from gui import theme
from gui.pages.base_page import BasePage
from gui.widgets.loadcell_chart import LoadcellChart
from core import data_store


class SavedMeasurementsPage(BasePage):
    def __init__(self, parent, manager, navigate, main_win):
        super().__init__(parent, manager, navigate, main_win)
        self._build()

    def _build(self):
        self._page_header("📁  Saved Measurements",
                          f"Stored in: {config.DOCUMENTS_DIR}")

        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=theme.BG)
        bar.pack(fill=tk.X, padx=28, pady=(10, 6))

        ttk.Button(bar, text="🔄  Refresh", command=self._load_list
                   ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(bar, text="📂  Open folder", command=self._open_folder
                   ).pack(side=tk.LEFT, padx=(0, 8))
        self._del_btn = ttk.Button(bar, text="🗑  Delete selected",
                                   style="Warning.TButton",
                                   command=self._delete, state="disabled")
        self._del_btn.pack(side=tk.LEFT)

        # ── Paned layout (list left, chart right) ─────────────────────────────
        pane = tk.PanedWindow(self, orient=tk.VERTICAL, bg=theme.BG,
                              sashwidth=6, sashrelief="flat")
        pane.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 12))

        # Top pane: file list
        list_frame = tk.Frame(pane, bg=theme.BG)
        pane.add(list_frame, minsize=180)

        cols = ("timestamp", "ski_model", "total_weight", "filename")
        self._tree = ttk.Treeview(list_frame, columns=cols, show="headings",
                                  selectmode="browse", height=8)
        for col, heading, width in [
            ("timestamp",    "Date / Time",      200),
            ("ski_model",    "Ski model",        180),
            ("total_weight", "Total weight (g)", 140),
            ("filename",     "File",             340),
        ]:
            self._tree.heading(col, text=heading,
                               command=lambda c=col: self._sort(c))
            self._tree.column(col, width=width, anchor="w")

        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Bottom pane: chart + metadata
        detail_frame = tk.Frame(pane, bg=theme.BG)
        pane.add(detail_frame, minsize=220)

        meta_row = tk.Frame(detail_frame, bg=theme.BG)
        meta_row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(meta_row, text="Total weight:", bg=theme.BG,
                 fg=theme.TEXT_SEC, font=theme.F_BODY).pack(side=tk.LEFT)
        self._weight_lbl = tk.Label(meta_row, text="—", bg=theme.BG,
                                    fg=theme.ACCENT, font=theme.F_LARGE)
        self._weight_lbl.pack(side=tk.LEFT, padx=8)
        self._meta_lbl = tk.Label(meta_row, text="Select a measurement above",
                                  bg=theme.BG, fg=theme.TEXT_MUTED,
                                  font=theme.F_SMALL)
        self._meta_lbl.pack(side=tk.LEFT, padx=8)

        self._chart = LoadcellChart(detail_frame, height_in=3.4)
        self._chart.pack(fill=tk.BOTH, expand=True)

        self._rows: list[dict] = []   # parallel to tree items
        self._load_list()

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        self._load_list()

    def _load_list(self):
        self._tree.delete(*self._tree.get_children())
        self._rows = data_store.list_measurements()
        for m in self._rows:
            self._tree.insert("", "end", values=(
                m["timestamp"], m["ski_model"],
                m["total_weight"], m["filename"],
            ))
        self._del_btn.configure(state="disabled")
        self._chart.update_data([None] * config.TOTAL_CELLS)
        self._weight_lbl.configure(text="—")
        self._meta_lbl.configure(text=f"{len(self._rows)} measurements found")

    def _on_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx   = self._tree.index(sel[0])
        entry = self._rows[idx]
        self._del_btn.configure(state="normal")
        try:
            meta, readings = data_store.load_measurement(entry["path"])
            self._chart.update_data(readings)
            self._weight_lbl.configure(text=f"{meta['total_weight']} g")
            self._meta_lbl.configure(
                text=f"{meta['timestamp']}  ·  {meta['ski_model']}",
                fg=theme.TEXT_SEC)
        except Exception as exc:
            messagebox.showerror("Load error", str(exc), parent=self)

    def _delete(self):
        sel = self._tree.selection()
        if not sel:
            return
        idx   = self._tree.index(sel[0])
        entry = self._rows[idx]
        if not messagebox.askyesno("Delete?",
                                   f"Delete '{entry['filename']}'?",
                                   parent=self):
            return
        try:
            entry["path"].unlink()
        except Exception as exc:
            messagebox.showerror("Delete failed", str(exc), parent=self)
        self._load_list()

    def _open_folder(self):
        path = config.DOCUMENTS_DIR
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _sort(self, col: str):
        items = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        items.sort(reverse=False)
        for rank, (_, k) in enumerate(items):
            self._tree.move(k, "", rank)
