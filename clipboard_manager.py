"""
Clipboard Manager with Drag & Drop
Requirements: pip install tkinterdnd2
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

try:
    from tkinterdnd2 import DND_TEXT, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_manager.json")

DARK_BG   = "#1e1e2e"
PANEL_BG  = "#2a2a3e"
CARD_BG   = "#313147"
CARD_HOVER= "#3d3d58"
ACCENT    = "#7c6af7"
ACCENT2   = "#a78bfa"
TEXT_PRIMARY   = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED     = "#64748b"
BORDER    = "#3f3f5c"
DANGER    = "#f87171"
SELECT_BG = "#4c4a7a"
THUMB_BG  = "#4a4a6a"
THUMB_HOVER = "#6a6a9a"


def load_items():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"label": "Email",     "text": "hello@example.com"},
        {"label": "Phone",     "text": "+1 (555) 123-4567"},
        {"label": "Address",   "text": "123 Main St, New York, NY 10001"},
        {"label": "Signature", "text": "Best regards,\nJohn Doe\nSenior Developer"},
    ]


def save_items(items):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")


# ─── Custom scrollbar (Canvas-based, fully styled) ───────────────────────────

class DarkScrollbar(tk.Canvas):
    """Thin dark scrollbar that replaces ttk.Scrollbar."""

    WIDTH = 6

    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, width=self.WIDTH, bg=DARK_BG,
                         highlightthickness=0, **kwargs)
        self._command = command
        self._thumb = self.create_rectangle(0, 0, self.WIDTH, 40,
                                            fill=THUMB_BG, outline="", width=0)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self.itemconfig(self._thumb, fill=THUMB_HOVER))
        self.bind("<Leave>", lambda e: self.itemconfig(self._thumb, fill=THUMB_BG))
        self._drag_start_y = 0
        self._drag_start_pos = 0.0
        self._pos = (0.0, 1.0)

    def set(self, lo, hi):
        lo, hi = float(lo), float(hi)
        self._pos = (lo, hi)
        h = self.winfo_height() or 1
        y0 = lo * h
        y1 = hi * h
        # minimum thumb height
        if y1 - y0 < 20:
            y1 = y0 + 20
        self.coords(self._thumb, 1, y0, self.WIDTH - 1, y1)
        # hide when content fits
        self.itemconfig(self._thumb,
                        state="normal" if (hi - lo) < 1.0 else "hidden")

    def _on_press(self, event):
        self._drag_start_y = event.y
        self._drag_start_pos = self._pos[0]

    def _on_drag(self, event):
        h = self.winfo_height() or 1
        delta = (event.y - self._drag_start_y) / h
        self._command("moveto", self._drag_start_pos + delta)

    def _on_release(self, event):
        pass


# ─── Clip card ────────────────────────────────────────────────────────────────

class ClipCard(tk.Frame):
    def __init__(self, parent, item, on_copy, **kwargs):
        super().__init__(parent, bg=CARD_BG, relief="flat", **kwargs)
        self.item    = item
        self.on_copy = on_copy
        self._hover    = False
        self._dragging = False
        self._press_x  = 0
        self._press_y  = 0
        self._build()

    def _build(self):
        self.configure(padx=14, pady=10)

        # Label badge
        badge = tk.Frame(self, bg=ACCENT, padx=6, pady=2)
        badge.pack(anchor="w")
        self.label_lbl = tk.Label(badge, text=self.item["label"],
                                  bg=ACCENT, fg="#ffffff",
                                  font=("Helvetica", 9, "bold"))
        self.label_lbl.pack()

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(8, 6))

        text_frame = tk.Frame(self, bg=CARD_BG)
        text_frame.pack(fill="x")

        drag_icon = tk.Label(text_frame, text="⠿", bg=CARD_BG, fg=TEXT_MUTED,
                             font=("Helvetica", 14), cursor="fleur")
        drag_icon.pack(side="left", padx=(0, 8))

        lines = self.item["text"].count("\n") + 1
        self.text_widget = tk.Text(
            text_frame,
            bg=CARD_BG, fg=TEXT_PRIMARY,
            font=("Helvetica", 10),
            relief="flat", bd=0,
            wrap="word", height=lines,
            cursor="fleur",
            selectbackground=SELECT_BG,
            selectforeground=TEXT_PRIMARY,
            inactiveselectbackground=SELECT_BG,
        )
        self.text_widget.insert("1.0", self.item["text"])
        self.text_widget.configure(state="disabled")
        self.text_widget.pack(side="left", fill="x", expand=True, pady=2)

        # Hover → auto-select
        for w in (self, badge, text_frame, drag_icon, self.text_widget):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        # DnD
        if DND_AVAILABLE:
            for w in (self, drag_icon, self.text_widget):
                try:
                    w.drag_source_register(DND_TEXT)
                    w.dnd_bind("<<DragInitCmd>>", self._drag_init)
                    w.dnd_bind("<<DragEndCmd>>",  self._drag_end)
                except Exception:
                    pass
            for w in (self, drag_icon, self.text_widget):
                w.bind("<ButtonPress-1>",   self._on_press)
                w.bind("<ButtonRelease-1>", self._on_click_release)
        else:
            for w in (self, drag_icon, self.text_widget):
                w.bind("<ButtonPress-1>",   self._on_press)
                w.bind("<B1-Motion>",        self._on_motion)
                w.bind("<ButtonRelease-1>", self._on_release_nodndt)

    # ── DnD ──
    def _drag_init(self, event):
        self._dragging = True
        return ("copy", DND_TEXT, self.item["text"])

    def _drag_end(self, event):
        self._dragging = False

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root

    def _on_click_release(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx < 5 and dy < 5 and not self._dragging:
            self.on_copy(self.item["text"])

    def _on_motion(self, event):
        pass  # needed to prevent text-widget default selection during drag

    def _on_release_nodndt(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx < 5 and dy < 5:
            self.on_copy(self.item["text"])

    # ── Hover ──
    def _on_enter(self, event):
        if not self._hover:
            self._hover = True
            self._set_bg(CARD_HOVER)
            self._select_all()

    def _on_leave(self, event):
        under = self.winfo_containing(event.x_root, event.y_root)
        if under and (under is self or str(under).startswith(str(self))):
            return
        self._hover = False
        self._set_bg(CARD_BG)
        self._deselect()

    def _select_all(self):
        self.text_widget.configure(state="normal")
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.configure(state="disabled")

    def _deselect(self):
        self.text_widget.configure(state="normal")
        self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
        self.text_widget.configure(state="disabled")

    def _set_bg(self, color):
        self.text_widget.configure(bg=color)
        self.configure(bg=color)
        for w in self.winfo_children():
            try:
                if w.cget("bg") not in (ACCENT, PANEL_BG) and not isinstance(w, tk.Text):
                    w.configure(bg=color)
                    for ww in w.winfo_children():
                        try:
                            if ww.cget("bg") not in (ACCENT, PANEL_BG) and not isinstance(ww, tk.Text):
                                ww.configure(bg=color)
                        except Exception:
                            pass
            except Exception:
                pass

    def refresh(self):
        self.label_lbl.configure(text=self.item["label"])
        lines = self.item["text"].count("\n") + 1
        self.text_widget.configure(state="normal", height=lines)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", self.item["text"])
        self.text_widget.configure(state="disabled")


# ─── Editor window ────────────────────────────────────────────────────────────

class EditorWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.overrideredirect(True)
        self.configure(bg=DARK_BG)
        self.resizable(False, False)

        w, h = 380, 520
        rx = app.root.winfo_x()
        ry = app.root.winfo_y()
        rw = app.root.winfo_width()
        self.geometry(f"{w}x{h}+{rx + rw + 8}+{ry}")

        self._selected_idx = None
        self._build()
        self._refresh_list()

    def _build(self):
        # ── Titlebar ──
        bar = tk.Frame(self, bg=PANEL_BG, height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="✎  Редактор", bg=PANEL_BG, fg=TEXT_PRIMARY,
                 font=("Helvetica", 11, "bold")).pack(side="left", padx=14)

        tk.Button(bar, text="✕", bg=PANEL_BG, fg=DANGER,
                  font=("Helvetica", 11), relief="flat", cursor="hand2",
                  activebackground="#3d1a1a", activeforeground=DANGER,
                  command=self.destroy, bd=0, padx=10, pady=8).pack(side="right")

        tk.Button(bar, text="+ Добавить", bg=ACCENT, fg="#ffffff",
                  font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2",
                  activebackground=ACCENT2, activeforeground="#ffffff",
                  command=self._add_item, bd=0, padx=10, pady=6).pack(side="right", padx=8)

        bar.bind("<ButtonPress-1>", self._bar_press)
        bar.bind("<B1-Motion>",     self._bar_drag)

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")

        # ── Left: item list ──
        body = tk.Frame(self, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        list_frame = tk.Frame(body, bg=DARK_BG, width=160)
        list_frame.pack(side="left", fill="y")
        list_frame.pack_propagate(False)

        self.listbox = tk.Listbox(
            list_frame,
            bg=PANEL_BG, fg=TEXT_PRIMARY,
            selectbackground=ACCENT, selectforeground="#ffffff",
            font=("Helvetica", 10),
            relief="flat", bd=0,
            activestyle="none",
            highlightthickness=0,
        )
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # ── Right: edit panel ──
        edit_panel = tk.Frame(body, bg=DARK_BG)
        edit_panel.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        tk.Label(edit_panel, text="Название", bg=DARK_BG, fg=TEXT_MUTED,
                 font=("Helvetica", 9)).pack(anchor="w")
        self.label_var = tk.StringVar()
        self.label_var.trace("w", self._on_field_change)
        label_entry = tk.Entry(edit_panel, textvariable=self.label_var,
                               bg=PANEL_BG, fg=TEXT_PRIMARY,
                               insertbackground=TEXT_PRIMARY,
                               font=("Helvetica", 10), relief="flat", bd=0)
        label_entry.pack(fill="x", ipady=6, pady=(2, 10))

        tk.Label(edit_panel, text="Текст", bg=DARK_BG, fg=TEXT_MUTED,
                 font=("Helvetica", 9)).pack(anchor="w")
        self.text_box = tk.Text(edit_panel,
                                bg=PANEL_BG, fg=TEXT_PRIMARY,
                                insertbackground=TEXT_PRIMARY,
                                font=("Helvetica", 10), relief="flat", bd=0,
                                wrap="word", height=10)
        self.text_box.pack(fill="both", expand=True, pady=(2, 10))
        self.text_box.bind("<<Modified>>", self._on_text_modified)

        btn_row = tk.Frame(edit_panel, bg=DARK_BG)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Удалить", bg=PANEL_BG, fg=DANGER,
                  font=("Helvetica", 9), relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=DANGER,
                  command=self._delete_item, padx=8, pady=4).pack(side="right")

        self._edit_state_widgets = [label_entry, self.text_box]
        self._set_edit_state("disabled")

    # ── List ──
    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for item in self.app.items:
            self.listbox.insert(tk.END, f"  {item['label']}")
        if self._selected_idx is not None:
            idx = min(self._selected_idx, len(self.app.items) - 1)
            if idx >= 0:
                self.listbox.selection_set(idx)
                self.listbox.activate(idx)

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._selected_idx = sel[0]
        item = self.app.items[self._selected_idx]
        self._set_edit_state("normal")

        self.label_var.set(item["label"])

        self.text_box.delete("1.0", tk.END)
        self.text_box.insert("1.0", item["text"])
        self.text_box.edit_modified(False)

    def _on_field_change(self, *_):
        if self._selected_idx is None:
            return
        self.app.items[self._selected_idx]["label"] = self.label_var.get()
        self._sync()

    def _on_text_modified(self, event):
        if not self.text_box.edit_modified():
            return
        if self._selected_idx is None:
            return
        self.app.items[self._selected_idx]["text"] = self.text_box.get("1.0", tk.END).rstrip("\n")
        self.text_box.edit_modified(False)
        self._sync()

    def _add_item(self):
        new = {"label": "Новый", "text": ""}
        self.app.items.append(new)
        self._selected_idx = len(self.app.items) - 1
        self._sync()
        self._refresh_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self._selected_idx)
        self._on_select(None)

    def _delete_item(self):
        if self._selected_idx is None:
            return
        self.app.items.pop(self._selected_idx)
        self._selected_idx = None
        self.label_var.set("")
        self.text_box.delete("1.0", tk.END)
        self._set_edit_state("disabled")
        self._sync()
        self._refresh_list()

    def _sync(self):
        save_items(self.app.items)
        self.app._render_cards(self.app.items)
        self._refresh_list()

    def _set_edit_state(self, state):
        for w in self._edit_state_widgets:
            try:
                w.configure(state=state)
            except Exception:
                pass

    # ── Window drag ──
    def _bar_press(self, e):
        self._bx = e.x_root - self.winfo_x()
        self._by = e.y_root - self.winfo_y()

    def _bar_drag(self, e):
        self.geometry(f"+{e.x_root - self._bx}+{e.y_root - self._by}")


# ─── Main app ─────────────────────────────────────────────────────────────────

class App:
    def __init__(self):
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.overrideredirect(True)
        self.root.geometry("480x620+200+80")
        self.root.configure(bg=DARK_BG)
        self.root.minsize(400, 400)

        self.items  = load_items()
        self.cards  = []
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        self._editor = None

        self._build_ui()
        self._render_cards(self.items)

    def _build_ui(self):
        # ── Custom titlebar ──
        bar = tk.Frame(self.root, bg=PANEL_BG, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="📋  Clipboard", bg=PANEL_BG, fg=TEXT_PRIMARY,
                 font=("Helvetica", 12, "bold")).pack(side="left", padx=16)

        # Close
        tk.Button(bar, text="✕", bg=PANEL_BG, fg=DANGER,
                  font=("Helvetica", 12), relief="flat", cursor="hand2",
                  activebackground="#3d1a1a", activeforeground=DANGER,
                  command=self._on_close, bd=0, padx=12, pady=10).pack(side="right")

        # Minimize
        tk.Button(bar, text="─", bg=PANEL_BG, fg=TEXT_MUTED,
                  font=("Helvetica", 12), relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT_PRIMARY,
                  command=self._minimize, bd=0, padx=10, pady=10).pack(side="right")

        # Editor (pencil)
        tk.Button(bar, text="✎", bg=PANEL_BG, fg=TEXT_SECONDARY,
                  font=("Helvetica", 13), relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=ACCENT2,
                  command=self._open_editor, bd=0, padx=12, pady=10).pack(side="right")

        # Window drag
        bar.bind("<ButtonPress-1>", self._bar_press)
        bar.bind("<B1-Motion>",     self._bar_drag)
        # Re-apply overrideredirect after un-minimizing
        self.root.bind("<Map>", lambda e: self.root.overrideredirect(True))

        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill="x")

        # ── Search ──
        sf = tk.Frame(self.root, bg=DARK_BG, padx=12, pady=8)
        sf.pack(fill="x")
        se = tk.Entry(sf, textvariable=self.search_var,
                      bg=PANEL_BG, fg=TEXT_PRIMARY,
                      insertbackground=TEXT_PRIMARY,
                      font=("Helvetica", 10), relief="flat", bd=0)
        se.pack(fill="x", ipady=7, padx=6)
        se.insert(0, "🔍  Поиск...")
        se.bind("<FocusIn>",  lambda e: se.delete(0, "end") if se.get().startswith("🔍") else None)
        se.bind("<FocusOut>", lambda e: se.insert(0, "🔍  Поиск...") if not se.get().strip() else None)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── Scrollable cards ──
        container = tk.Frame(self.root, bg=DARK_BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=DARK_BG, highlightthickness=0)
        self.scrollbar = DarkScrollbar(container, command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg=DARK_BG)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw", tags="frame")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig("frame", width=e.width))

        self.scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=4)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))
        self.canvas.bind_all("<Button-4>",   lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>",   lambda e: self.canvas.yview_scroll(1, "units"))

        # ── Status bar ──
        self.status_var = tk.StringVar(value="Наведи и перетащи текст в любое поле ввода")
        tk.Label(self.root, textvariable=self.status_var,
                 bg=PANEL_BG, fg=TEXT_MUTED,
                 font=("Helvetica", 9), pady=6).pack(fill="x", side="bottom")

    # ── Titlebar drag ──
    def _bar_press(self, e):
        self._bx = e.x_root - self.root.winfo_x()
        self._by = e.y_root - self.root.winfo_y()

    def _bar_drag(self, e):
        self.root.geometry(f"+{e.x_root - self._bx}+{e.y_root - self._by}")

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    # ── Cards ──
    def _render_cards(self, items):
        for c in self.cards:
            c.destroy()
        self.cards.clear()
        for item in items:
            card = ClipCard(self.cards_frame, item, on_copy=self._copy_text)
            card.pack(fill="x", padx=10, pady=5)
            self.cards.append(card)

    def _on_search(self, *_):
        q = self.search_var.get().lower().strip()
        filtered = self.items if (not q or q.startswith("🔍")) else [
            i for i in self.items if q in i["label"].lower() or q in i["text"].lower()
        ]
        self._render_cards(filtered)

    def _copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set(f"✓ Скопировано: {text[:48]}{'…' if len(text)>48 else ''}")
        self.root.after(3000, lambda: self.status_var.set("Наведи и перетащи текст в любое поле ввода"))

    # ── Editor ──
    def _open_editor(self):
        if self._editor and self._editor.winfo_exists():
            self._editor.lift()
            return
        self._editor = EditorWindow(self)

    # ── Close ──
    def _on_close(self):
        save_items(self.items)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
