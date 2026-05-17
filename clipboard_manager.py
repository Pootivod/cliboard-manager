"""
Clipboard Manager — Grid Edition
Requirements: pip install tkinterdnd2
"""

import tkinter as tk
from tkinter import simpledialog
import json, os, copy

try:
    from tkinterdnd2 import DND_TEXT, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────
SAVE_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_grid.json")

COLS      = 4
CELL_SIZE = 82
CELL_GAP  = 6
SIDEBAR_W = 100

DARK_BG    = "#1e1e2e"
PANEL_BG   = "#2a2a3e"
CARD_BG    = "#313147"
CARD_HOVER = "#3d3d58"
CARD_DROP  = "#3a3870"
ACCENT     = "#7c6af7"
ACCENT2    = "#a78bfa"
TEXT_PRIMARY   = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED     = "#64748b"
BORDER     = "#3f3f5c"
DANGER     = "#f87171"
THUMB_BG   = "#4a4a6a"
THUMB_HOV  = "#6a6a9a"

TOOLTIP_DELAY = 3000   # ms

DEFAULT_DATA = {
    "active": 0,
    "tables": [
        {
            "name": "Основная",
            "icon": "📋",
            "cells": [
                {"emoji": "📧", "label": "Email",     "text": "hello@example.com"},
                {"emoji": "📞", "label": "Phone",     "text": "+1 (555) 123-4567"},
                {"emoji": "🏠", "label": "Address",   "text": "123 Main St, New York, NY 10001"},
                {"emoji": "✍",  "label": "Signature", "text": "Best regards,\nJohn Doe\nSenior Developer"},
            ]
        }
    ]
}


# ── Persistence ───────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_DATA)


def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")


# ── Dark scrollbar ─────────────────────────────────────────────────────────────
class DarkScrollbar(tk.Canvas):
    W = 6

    def __init__(self, parent, command, **kw):
        super().__init__(parent, width=self.W, bg=DARK_BG, highlightthickness=0, **kw)
        self._cmd = command
        self._thumb = self.create_rectangle(0, 0, self.W, 40, fill=THUMB_BG, outline="")
        self._pos = (0.0, 1.0)
        self._dy = self._dp = 0
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>",     self._drag)
        self.bind("<Enter>", lambda e: self.itemconfig(self._thumb, fill=THUMB_HOV))
        self.bind("<Leave>", lambda e: self.itemconfig(self._thumb, fill=THUMB_BG))

    def set(self, lo, hi):
        lo, hi = float(lo), float(hi)
        self._pos = (lo, hi)
        h  = self.winfo_height() or 1
        y0 = lo * h
        y1 = max(y0 + 20, hi * h)
        self.coords(self._thumb, 1, y0, self.W - 1, y1)
        self.itemconfig(self._thumb, state="normal" if (hi - lo) < 1.0 else "hidden")

    def _press(self, e):
        self._dy = e.y
        self._dp = self._pos[0]

    def _drag(self, e):
        h = self.winfo_height() or 1
        self._cmd("moveto", self._dp + (e.y - self._dy) / h)


# ── Cell widget ───────────────────────────────────────────────────────────────
class CellWidget(tk.Frame):
    def __init__(self, parent, cell, idx, grid_ref, app):
        super().__init__(parent, bg=CARD_BG,
                         width=CELL_SIZE, height=CELL_SIZE,
                         highlightthickness=1, highlightbackground=BORDER)
        self.pack_propagate(False)
        self.cell     = cell
        self.idx      = idx
        self.grid_ref = grid_ref
        self.app      = app

        self._tooltip_job = None
        self._tooltip_win = None
        self._dragging = False
        self._px = self._py = 0

        self._emoji_lbl = tk.Label(self, text=cell.get("emoji", "📄"),
                                   bg=CARD_BG, fg=TEXT_PRIMARY,
                                   font=("Helvetica", 28))
        self._emoji_lbl.place(relx=0.5, rely=0.42, anchor="center")

        self._name_lbl = tk.Label(self, text=cell.get("label", ""),
                                  bg=CARD_BG, fg=TEXT_MUTED,
                                  font=("Helvetica", 7))
        self._name_lbl.place(relx=0.5, rely=0.86, anchor="center")

        for w in (self, self._emoji_lbl, self._name_lbl):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        if self.app.edit_mode:
            # Edit mode: B1-Motion for in-grid reorder
            for w in (self, self._emoji_lbl, self._name_lbl):
                w.bind("<ButtonPress-1>",   self._on_press)
                w.bind("<B1-Motion>",       self._on_motion)
                w.bind("<ButtonRelease-1>", self._on_release)
        else:
            # Normal mode: external DnD (drag text to other apps)
            if DND_AVAILABLE:
                for w in (self, self._emoji_lbl, self._name_lbl):
                    try:
                        w.drag_source_register(DND_TEXT)
                        w.dnd_bind("<<DragInitCmd>>", self._drag_init)
                        w.dnd_bind("<<DragEndCmd>>",  self._drag_end)
                    except Exception:
                        pass
            for w in (self, self._emoji_lbl, self._name_lbl):
                w.bind("<ButtonPress-1>",   self._on_press)
                w.bind("<ButtonRelease-1>", self._on_click_release)

    # ── Hover / tooltip ──
    def _on_enter(self, _):
        self._set_bg(CARD_HOVER)
        if self._tooltip_job:
            self.after_cancel(self._tooltip_job)
        self._tooltip_job = self.after(TOOLTIP_DELAY, self._show_tooltip)

    def _on_leave(self, e):
        # Ignore if still inside this widget tree
        under = self.winfo_containing(e.x_root, e.y_root)
        if under and str(under).startswith(str(self)):
            return
        if not self._dragging:
            self._set_bg(CARD_BG)
        self._cancel_tooltip()

    def _show_tooltip(self):
        if self._tooltip_win:
            return
        x = self.winfo_rootx() + CELL_SIZE // 2
        y = self.winfo_rooty() + CELL_SIZE + 6

        w = tk.Toplevel(self)
        w.overrideredirect(True)
        w.configure(bg=PANEL_BG, highlightbackground=BORDER, highlightthickness=1)
        self._tooltip_win = w

        f = tk.Frame(w, bg=PANEL_BG, padx=10, pady=8)
        f.pack()

        tk.Label(f, text=self.cell.get("label", ""),
                 bg=PANEL_BG, fg=ACCENT2,
                 font=("Helvetica", 9, "bold")).pack(anchor="w")

        txt = self.cell.get("text", "")
        prev = txt[:160] + ("…" if len(txt) > 160 else "")
        tk.Label(f, text=prev or "—",
                 bg=PANEL_BG, fg=TEXT_PRIMARY,
                 font=("Helvetica", 9),
                 wraplength=260, justify="left").pack(anchor="w", pady=(3, 0))

        w.update_idletasks()
        tw = w.winfo_reqwidth()
        w.geometry(f"+{x - tw // 2}+{y}")

    def _cancel_tooltip(self):
        if self._tooltip_job:
            self.after_cancel(self._tooltip_job)
            self._tooltip_job = None
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None

    # ── Drag / click ──
    def _on_press(self, e):
        self._px, self._py = e.x_root, e.y_root
        self._dragging = False
        self._cancel_tooltip()

    # Normal mode: external DnD handlers
    def _drag_init(self, e):
        self._dragging = True
        return ("copy", DND_TEXT, self.cell["text"])

    def _drag_end(self, e):
        self._dragging = False

    def _on_click_release(self, e):
        dx = abs(e.x_root - self._px)
        dy = abs(e.y_root - self._py)
        if dx < 6 and dy < 6 and not self._dragging:
            self.app.copy_text(self.cell["text"])

    # Edit mode: in-grid reorder handlers
    def _on_motion(self, e):
        if abs(e.x_root - self._px) > 7 or abs(e.y_root - self._py) > 7:
            self._dragging = True
        if self._dragging:
            self.grid_ref.drag_over(e.x_root, e.y_root, self.idx)

    def _on_release(self, e):
        if self._dragging:
            self.grid_ref.drag_drop(e.x_root, e.y_root, self.idx)
            self._dragging = False
        else:
            self.app.copy_text(self.cell["text"])

    # ── Visuals ──
    def _set_bg(self, color):
        self.configure(bg=color)
        self._emoji_lbl.configure(bg=color)
        self._name_lbl.configure(bg=color)

    def set_drop_highlight(self, on: bool):
        if on:
            self._set_bg(CARD_DROP)
            self.configure(highlightbackground=ACCENT)
        else:
            self._set_bg(CARD_HOVER)
            self.configure(highlightbackground=BORDER)

    def refresh(self):
        self._emoji_lbl.configure(text=self.cell.get("emoji", "📄"))
        self._name_lbl.configure(text=self.cell.get("label", ""))


# ── Table grid ────────────────────────────────────────────────────────────────
class TableGrid(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=DARK_BG)
        self.app = app
        self._widgets: list[CellWidget] = []
        self._drop_target = None

    def render(self, table):
        for w in self.winfo_children():
            w.destroy()
        self._widgets.clear()
        self._drop_target = None

        cells = table.get("cells", [])
        for i, cell in enumerate(cells):
            cw = CellWidget(self, cell, i, self, self.app)
            r, c = divmod(i, COLS)
            cw.grid(row=r, column=c, padx=CELL_GAP, pady=CELL_GAP)
            self._widgets.append(cw)

        # "+" add cell
        plus_r, plus_c = divmod(len(cells), COLS)
        plus = tk.Frame(self, bg=CARD_BG, width=CELL_SIZE, height=CELL_SIZE,
                        highlightthickness=1, highlightbackground=BORDER,
                        cursor="hand2")
        plus.grid(row=plus_r, column=plus_c, padx=CELL_GAP, pady=CELL_GAP)
        plus.pack_propagate(False)
        lbl = tk.Label(plus, text="+", bg=CARD_BG, fg=TEXT_MUTED,
                       font=("Helvetica", 26), cursor="hand2")
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        for w in (plus, lbl):
            w.bind("<Button-1>", lambda e: self.app.add_cell())
            w.bind("<Enter>", lambda e: [plus.configure(bg=CARD_HOVER), lbl.configure(bg=CARD_HOVER)])
            w.bind("<Leave>", lambda e: [plus.configure(bg=CARD_BG),    lbl.configure(bg=CARD_BG)])

        for c in range(COLS):
            self.grid_columnconfigure(c, weight=0)

    def drag_over(self, x, y, src):
        t = self._cell_at(x, y)
        if t == self._drop_target:
            return
        if self._drop_target is not None and self._drop_target < len(self._widgets):
            self._widgets[self._drop_target].set_drop_highlight(False)
        self._drop_target = t
        if t is not None and t != src and t < len(self._widgets):
            self._widgets[t].set_drop_highlight(True)

    def drag_drop(self, x, y, src):
        t = self._cell_at(x, y)
        if self._drop_target is not None and self._drop_target < len(self._widgets):
            self._widgets[self._drop_target].set_drop_highlight(False)
        self._drop_target = None
        if t is not None and t != src:
            self.app.swap_cells(src, t)

    def _cell_at(self, x, y):
        for w in self._widgets:
            wx, wy = w.winfo_rootx(), w.winfo_rooty()
            if wx <= x <= wx + CELL_SIZE and wy <= y <= wy + CELL_SIZE:
                return w.idx
        return None


# ── Sidebar ───────────────────────────────────────────────────────────────────
class Sidebar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=PANEL_BG, width=SIDEBAR_W)
        self.app = app
        self.pack_propagate(False)

    def render(self, tables, active_idx):
        for w in self.winfo_children():
            w.destroy()

        for i, t in enumerate(tables):
            active = (i == active_idx)
            bg     = CARD_BG if active else PANEL_BG
            border = ACCENT  if active else BORDER

            sq = tk.Frame(self, bg=bg,
                          width=SIDEBAR_W - 14, height=SIDEBAR_W - 14,
                          highlightthickness=2, highlightbackground=border,
                          cursor="hand2")
            sq.pack(pady=(8, 0), padx=7)
            sq.pack_propagate(False)

            icon = tk.Label(sq, text=t.get("icon", "📋"),
                            bg=bg, font=("Helvetica", 22), cursor="hand2")
            icon.place(relx=0.5, rely=0.38, anchor="center")

            name = tk.Label(sq, text=t["name"][:8],
                            bg=bg,
                            fg=TEXT_PRIMARY if active else TEXT_MUTED,
                            font=("Helvetica", 7), cursor="hand2")
            name.place(relx=0.5, rely=0.82, anchor="center")

            def _hover_in(e, sq=sq, icon=icon, name=name, active=active):
                if not active:
                    sq.configure(bg=CARD_BG)
                    icon.configure(bg=CARD_BG)
                    name.configure(bg=CARD_BG)

            def _hover_out(e, sq=sq, icon=icon, name=name, active=active):
                if not active:
                    sq.configure(bg=PANEL_BG)
                    icon.configure(bg=PANEL_BG)
                    name.configure(bg=PANEL_BG)

            for w in (sq, icon, name):
                w.bind("<Button-1>", lambda e, idx=i: self.app.switch_table(idx))
                w.bind("<Enter>", _hover_in)
                w.bind("<Leave>", _hover_out)

        # Add table
        add = tk.Frame(self, bg=PANEL_BG,
                       width=SIDEBAR_W - 14, height=36,
                       highlightthickness=1, highlightbackground=BORDER,
                       cursor="hand2")
        add.pack(pady=(8, 0), padx=7)
        add.pack_propagate(False)
        lbl = tk.Label(add, text="+ стол", bg=PANEL_BG, fg=TEXT_MUTED,
                       font=("Helvetica", 8), cursor="hand2")
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        for w in (add, lbl):
            w.bind("<Button-1>", lambda e: self.app.add_table())
            w.bind("<Enter>", lambda e: [add.configure(bg=CARD_BG), lbl.configure(bg=CARD_BG)])
            w.bind("<Leave>", lambda e: [add.configure(bg=PANEL_BG), lbl.configure(bg=PANEL_BG)])


# ── Editor window ─────────────────────────────────────────────────────────────
class EditorWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Редактор — Clipboard Manager")
        self.configure(bg=DARK_BG)

        mx = app.root.winfo_x() + app.root.winfo_width() + 8
        my = app.root.winfo_y()
        self.geometry(f"420x560+{mx}+{my}")

        self._sel = app.data.get("active", 0)
        self._build()
        self.render()

    def _build(self):
        # Header bar (OS handles window chrome)
        bar = tk.Frame(self, bg=PANEL_BG, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="✎  Редактор", bg=PANEL_BG, fg=TEXT_PRIMARY,
                 font=("Helvetica", 11, "bold")).pack(side="left", padx=14)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        # Left: tables list
        self._tpanel = tk.Frame(body, bg=PANEL_BG, width=136)
        self._tpanel.pack(side="left", fill="y")
        self._tpanel.pack_propagate(False)

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # Right: cells
        self._cpanel = tk.Frame(body, bg=DARK_BG)
        self._cpanel.pack(side="left", fill="both", expand=True)

    def render(self):
        self._render_tables()
        self._render_cells()

    # ── Tables list (left panel) ──
    def _render_tables(self):
        for w in self._tpanel.winfo_children():
            w.destroy()

        tk.Label(self._tpanel, text="ТАБЛИЦЫ",
                 bg=PANEL_BG, fg=TEXT_MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        for i, t in enumerate(self.app.data["tables"]):
            sel = (i == self._sel)
            bg  = CARD_BG if sel else PANEL_BG

            row = tk.Frame(self._tpanel, bg=bg, cursor="hand2")
            row.pack(fill="x", padx=4, pady=1)

            tk.Label(row, text=t.get("icon", "📋"),
                     bg=bg, font=("Helvetica", 13), cursor="hand2").pack(side="left", padx=6, pady=5)
            tk.Label(row, text=t["name"][:14],
                     bg=bg,
                     fg=TEXT_PRIMARY if sel else TEXT_SECONDARY,
                     font=("Helvetica", 9), cursor="hand2").pack(side="left")

            for w in (row,) + row.winfo_children():
                w.bind("<Button-1>", lambda e, idx=i: self._select_table(idx))
                if not sel:
                    w.bind("<Enter>", lambda e, r=row, kids=row.winfo_children():
                           [r.configure(bg=CARD_BG)] + [k.configure(bg=CARD_BG) for k in kids])
                    w.bind("<Leave>", lambda e, r=row, kids=row.winfo_children():
                           [r.configure(bg=PANEL_BG)] + [k.configure(bg=PANEL_BG) for k in kids])

        tk.Button(self._tpanel, text="+ Таблица",
                  bg=PANEL_BG, fg=ACCENT2,
                  font=("Helvetica", 9), relief="flat", cursor="hand2",
                  activebackground=CARD_BG, activeforeground=ACCENT2,
                  command=self._add_table, pady=5).pack(fill="x", padx=6, pady=(10, 4))

    def _select_table(self, idx):
        self._sel = idx
        self.render()

    # ── Cells list (right panel) ──
    def _render_cells(self):
        for w in self._cpanel.winfo_children():
            w.destroy()

        tables = self.app.data["tables"]
        if not tables:
            return

        if self._sel >= len(tables):
            self._sel = len(tables) - 1

        table = tables[self._sel]

        # Table header row
        hdr = tk.Frame(self._cpanel, bg=DARK_BG, pady=8)
        hdr.pack(fill="x", padx=10)

        icon_btn = tk.Button(hdr, text=table.get("icon", "📋"),
                             bg=CARD_BG, font=("Helvetica", 18), relief="flat",
                             cursor="hand2", bd=0, padx=4,
                             command=lambda: self._edit_table_icon(table))
        icon_btn.pack(side="left", padx=(0, 6))

        name_var = tk.StringVar(value=table["name"])
        tk.Entry(hdr, textvariable=name_var,
                 bg=PANEL_BG, fg=TEXT_PRIMARY,
                 insertbackground=TEXT_PRIMARY,
                 font=("Helvetica", 11, "bold"), relief="flat", bd=0).pack(
            side="left", fill="x", expand=True, ipady=5)
        name_var.trace("w", lambda *_: self._set(table, "name", name_var.get()))

        tk.Button(hdr, text="Удалить таблицу", bg=PANEL_BG, fg=DANGER,
                  font=("Helvetica", 8), relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=DANGER,
                  command=self._delete_table, pady=4).pack(side="right")

        tk.Frame(self._cpanel, bg=BORDER, height=1).pack(fill="x", padx=10)

        # Scrollable cell list
        wrap = tk.Frame(self._cpanel, bg=DARK_BG)
        wrap.pack(fill="both", expand=True)

        cv = tk.Canvas(wrap, bg=DARK_BG, highlightthickness=0)
        sb = DarkScrollbar(wrap, command=cv.yview)
        inner = tk.Frame(cv, bg=DARK_BG)

        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=inner, anchor="nw", tags="f")
        cv.configure(yscrollcommand=sb.set)
        cv.bind("<Configure>", lambda e: cv.itemconfig("f", width=e.width))
        cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(-1*(e.delta//120), "units"))
        cv.bind("<Button-4>",   lambda e: cv.yview_scroll(-1, "units"))
        cv.bind("<Button-5>",   lambda e: cv.yview_scroll(1,  "units"))

        sb.pack(side="right", fill="y", pady=4, padx=(0, 2))
        cv.pack(side="left", fill="both", expand=True)

        for i, cell in enumerate(table.get("cells", [])):
            self._cell_row(inner, table, cell)

        tk.Button(inner, text="+ Добавить ячейку",
                  bg=PANEL_BG, fg=ACCENT2,
                  font=("Helvetica", 9), relief="flat", cursor="hand2",
                  activebackground=CARD_BG, activeforeground=ACCENT2,
                  command=lambda: self._add_cell(table), pady=5).pack(
            fill="x", padx=10, pady=(8, 4))

    def _cell_row(self, parent, table, cell):
        row = tk.Frame(parent, bg=CARD_BG, padx=8, pady=8)
        row.pack(fill="x", padx=10, pady=4)

        # Top: emoji + label + move + delete
        top = tk.Frame(row, bg=CARD_BG)
        top.pack(fill="x")

        tk.Button(top, text=cell.get("emoji", "📄"),
                  bg=PANEL_BG, font=("Helvetica", 16), relief="flat",
                  cursor="hand2", bd=0, padx=4,
                  command=lambda c=cell: self._edit_emoji(c, table)).pack(side="left", padx=(0, 6))

        label_v = tk.StringVar(value=cell.get("label", ""))
        tk.Entry(top, textvariable=label_v,
                 bg=PANEL_BG, fg=TEXT_PRIMARY,
                 insertbackground=TEXT_PRIMARY,
                 font=("Helvetica", 10), relief="flat", bd=0).pack(
            side="left", fill="x", expand=True, ipady=3)
        label_v.trace("w", lambda *_, c=cell, v=label_v: self._set_cell(c, table, "label", v.get()))

        # Move to table menu
        other_tables = [(j, t) for j, t in enumerate(self.app.data["tables"])
                        if j != self._sel]
        if other_tables:
            mb = tk.Menubutton(top, text="→ перенести",
                               bg=PANEL_BG, fg=TEXT_SECONDARY,
                               font=("Helvetica", 8), relief="flat",
                               cursor="hand2", activebackground=BORDER, bd=0, padx=4)
            mb.pack(side="right", padx=2)
            menu = tk.Menu(mb, tearoff=0, bg=PANEL_BG, fg=TEXT_PRIMARY,
                           activebackground=ACCENT, activeforeground="#ffffff",
                           font=("Helvetica", 9))
            mb["menu"] = menu
            for j, t in other_tables:
                menu.add_command(
                    label=f"{t.get('icon','')} {t['name']}",
                    command=lambda c=cell, ti=j: self._move_cell(c, table, ti)
                )

        tk.Button(top, text="✕", bg=PANEL_BG, fg=DANGER,
                  font=("Helvetica", 10), relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=DANGER, bd=0, padx=4,
                  command=lambda c=cell: self._delete_cell(c, table)).pack(side="right", padx=(2, 0))

        # Text area
        txt = tk.Text(row, bg=PANEL_BG, fg=TEXT_PRIMARY,
                      insertbackground=TEXT_PRIMARY,
                      font=("Helvetica", 9), relief="flat", bd=0,
                      wrap="word", height=3)
        txt.insert("1.0", cell.get("text", ""))
        txt.pack(fill="x", pady=(6, 0))
        txt.edit_modified(False)
        txt.bind("<<Modified>>", lambda e, t=txt, c=cell: self._text_changed(t, c, table))

    # ── Edit handlers ──
    def _edit_emoji(self, cell, table):
        v = simpledialog.askstring("Эмодзи", "Введи эмодзи:",
                                   initialvalue=cell.get("emoji", ""), parent=self)
        if v is not None:
            cell["emoji"] = v.strip() or cell.get("emoji", "📄")
            self._sync()

    def _edit_table_icon(self, table):
        v = simpledialog.askstring("Иконка таблицы", "Введи эмодзи:",
                                   initialvalue=table.get("icon", ""), parent=self)
        if v is not None:
            table["icon"] = v.strip() or table.get("icon", "📋")
            self._sync()

    def _set(self, table, key, value):
        table[key] = value
        self._quiet_sync()

    def _set_cell(self, cell, table, key, value):
        cell[key] = value
        self._quiet_sync()

    def _text_changed(self, txt, cell, table):
        if not txt.edit_modified():
            return
        cell["text"] = txt.get("1.0", tk.END).rstrip("\n")
        txt.edit_modified(False)
        self._quiet_sync()

    def _add_cell(self, table):
        table.setdefault("cells", []).append({"emoji": "📄", "label": "Новая", "text": ""})
        self._sync()

    def _delete_cell(self, cell, table):
        table["cells"].remove(cell)
        self._sync()

    def _move_cell(self, cell, src_table, dst_idx):
        src_table["cells"].remove(cell)
        self.app.data["tables"][dst_idx].setdefault("cells", []).append(cell)
        self._sync()

    def _add_table(self):
        name = simpledialog.askstring("Новая таблица", "Название:", parent=self)
        if not name:
            return
        self.app.data["tables"].append({"name": name, "icon": "📁", "cells": []})
        self._sel = len(self.app.data["tables"]) - 1
        self._sync()

    def _delete_table(self):
        tables = self.app.data["tables"]
        if len(tables) <= 1:
            return
        tables.pop(self._sel)
        self._sel = max(0, self._sel - 1)
        if self.app.data.get("active", 0) >= len(tables):
            self.app.data["active"] = len(tables) - 1
        self._sync()

    def _sync(self):
        save_data(self.app.data)
        self.app.refresh()
        self.render()

    def _quiet_sync(self):
        save_data(self.app.data)
        self.app.refresh()


# ── App ───────────────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("Clipboard Manager")
        self.root.geometry("480x580+180+80")
        self.root.configure(bg=DARK_BG)

        self.data      = load_data()
        self._editor   = None
        self.edit_mode = False

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── Toolbar (replaces custom titlebar — OS handles window chrome) ──
        bar = tk.Frame(self.root, bg=PANEL_BG, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="📋  Clipboard", bg=PANEL_BG, fg=TEXT_PRIMARY,
                 font=("Helvetica", 12, "bold")).pack(side="left", padx=16)

        self._pencil_btn = tk.Button(
            bar, text="✎", bg=PANEL_BG, fg=TEXT_SECONDARY,
            font=("Helvetica", 13), relief="flat", cursor="hand2",
            activebackground=BORDER, activeforeground=ACCENT2,
            command=self._toggle_editor, bd=0, padx=12)
        self._pencil_btn.pack(side="right")

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── Body: sidebar + grid ──
        body = tk.Frame(self.root, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        self._sidebar = Sidebar(body, self)
        self._sidebar.pack(side="left", fill="y")

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        grid_wrap = tk.Frame(body, bg=DARK_BG)
        grid_wrap.pack(side="left", fill="both", expand=True)

        self._canvas = tk.Canvas(grid_wrap, bg=DARK_BG, highlightthickness=0)
        self._scrollbar = DarkScrollbar(grid_wrap, command=self._canvas.yview)
        self._grid = TableGrid(self._canvas, self)

        self._canvas.create_window((0, 0), window=self._grid, anchor="nw", tags="g")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._grid.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig("g", width=e.width))

        self._scrollbar.pack(side="right", fill="y", pady=4, padx=(0, 2))
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1,  "units"))

        # ── Status ──
        self._status = tk.StringVar(value="Клик — копировать • Перетащи в другое приложение")
        tk.Label(self.root, textvariable=self._status,
                 bg=PANEL_BG, fg=TEXT_MUTED,
                 font=("Helvetica", 9), pady=6).pack(fill="x", side="bottom")

    # ── Public API ──
    def refresh(self):
        tables = self.data.get("tables", [])
        active = self.data.get("active", 0)
        if active >= len(tables):
            active = 0
            self.data["active"] = 0
        self._sidebar.render(tables, active)
        if tables:
            self._grid.render(tables[active])

    def switch_table(self, idx):
        self.data["active"] = idx
        save_data(self.data)
        self.refresh()

    def swap_cells(self, i, j):
        cells = self._active_table()["cells"]
        cells[i], cells[j] = cells[j], cells[i]
        save_data(self.data)
        self._grid.render(self._active_table())

    def add_cell(self):
        self._active_table().setdefault("cells", []).append(
            {"emoji": "📄", "label": "Новая", "text": ""})
        save_data(self.data)
        self.refresh()

    def add_table(self):
        name = simpledialog.askstring("Новая таблица", "Название:", parent=self.root)
        if not name:
            return
        self.data["tables"].append({"name": name, "icon": "📁", "cells": []})
        self.data["active"] = len(self.data["tables"]) - 1
        save_data(self.data)
        self.refresh()

    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        short = text[:50] + ("…" if len(text) > 50 else "")
        self._status.set(f"✓ Скопировано: {short}")
        idle = ("✎ Режим редактирования: перетащи ячейки для перестановки"
                if self.edit_mode else
                "Клик — копировать • Перетащи в другое приложение")
        self.root.after(3000, lambda: self._status.set(idle))

    def _active_table(self):
        return self.data["tables"][self.data.get("active", 0)]

    def _toggle_editor(self):
        if self.edit_mode:
            # Exit edit mode
            self.edit_mode = False
            self._pencil_btn.configure(bg=PANEL_BG, fg=TEXT_SECONDARY)
            self._status.set("Клик — копировать • Перетащи в другое приложение")
            if self._editor and self._editor.winfo_exists():
                self._editor.destroy()
            self.refresh()
        else:
            # Enter edit mode
            self.edit_mode = True
            self._pencil_btn.configure(bg=CARD_BG, fg=ACCENT2)
            self._status.set("✎ Режим редактирования: перетащи ячейки для перестановки")
            self.refresh()
            self._editor = EditorWindow(self)
            self._editor.protocol("WM_DELETE_WINDOW", self._toggle_editor)



    def _close(self):
        save_data(self.data)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
