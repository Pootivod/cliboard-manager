"""
Clipboard Manager with Drag & Drop
Requirements: pip install tkinterdnd2
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

try:
    from tkinterdnd2 import DND_TEXT, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_manager.json")

DARK_BG = "#1e1e2e"
PANEL_BG = "#2a2a3e"
CARD_BG = "#313147"
CARD_HOVER = "#3d3d58"
ACCENT = "#7c6af7"
ACCENT2 = "#a78bfa"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
BORDER = "#3f3f5c"
SUCCESS = "#4ade80"
DANGER = "#f87171"
SELECT_BG = "#4c4a7a"


def load_items():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"label": "Email", "text": "hello@example.com"},
        {"label": "Phone", "text": "+1 (555) 123-4567"},
        {"label": "Address", "text": "123 Main St, New York, NY 10001"},
        {"label": "Signature", "text": "Best regards,\nJohn Doe\nSenior Developer"},
    ]


def save_items(items):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")


class ClipCard(tk.Frame):
    def __init__(self, parent, item, on_copy, on_edit, on_delete, **kwargs):
        super().__init__(parent, bg=CARD_BG, relief="flat", **kwargs)
        self.item = item
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._hover = False
        self._dragging = False
        self._drag_started = False
        self._press_x = 0
        self._press_y = 0
        self._build()

    def _build(self):
        self.configure(padx=14, pady=10)

        top = tk.Frame(self, bg=CARD_BG)
        top.pack(fill="x")

        label_frame = tk.Frame(top, bg=ACCENT, padx=6, pady=2)
        label_frame.pack(side="left")
        self.label_lbl = tk.Label(
            label_frame, text=self.item["label"],
            bg=ACCENT, fg="#ffffff",
            font=("Helvetica", 9, "bold")
        )
        self.label_lbl.pack()

        btn_frame = tk.Frame(top, bg=CARD_BG)
        btn_frame.pack(side="right")

        copy_btn = tk.Button(
            btn_frame, text="Copy", bg=PANEL_BG, fg=ACCENT2,
            font=("Helvetica", 9), relief="flat", cursor="hand2",
            activebackground=BORDER, activeforeground=ACCENT2,
            command=lambda: self.on_copy(self.item["text"]), padx=6
        )
        copy_btn.pack(side="left", padx=2)

        edit_btn = tk.Button(
            btn_frame, text="Edit", bg=PANEL_BG, fg=TEXT_SECONDARY,
            font=("Helvetica", 9), relief="flat", cursor="hand2",
            activebackground=BORDER, activeforeground=TEXT_PRIMARY,
            command=lambda: self.on_edit(self), padx=4
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = tk.Button(
            btn_frame, text="Del", bg=PANEL_BG, fg=DANGER,
            font=("Helvetica", 9), relief="flat", cursor="hand2",
            activebackground=BORDER, activeforeground=DANGER,
            command=lambda: self.on_delete(self), padx=4
        )
        del_btn.pack(side="left", padx=2)

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(8, 6))

        text_frame = tk.Frame(self, bg=CARD_BG)
        text_frame.pack(fill="x")

        drag_icon = tk.Label(
            text_frame, text="⠿", bg=CARD_BG, fg=TEXT_MUTED,
            font=("Helvetica", 14), cursor="fleur"
        )
        drag_icon.pack(side="left", padx=(0, 8))

        line_count = self.item["text"].count("\n") + 1
        self.text_widget = tk.Text(
            text_frame,
            bg=CARD_BG, fg=TEXT_PRIMARY,
            font=("Helvetica", 10),
            relief="flat", bd=0,
            wrap="word",
            height=line_count,
            cursor="fleur",
            selectbackground=SELECT_BG,
            selectforeground=TEXT_PRIMARY,
            inactiveselectbackground=SELECT_BG,
        )
        self.text_widget.insert("1.0", self.item["text"])
        self.text_widget.configure(state="disabled")
        self.text_widget.pack(side="left", fill="x", expand=True, pady=2)

        # Hover: auto-select text
        hover_targets = [self, top, text_frame, drag_icon, self.text_widget]
        for w in hover_targets:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        if DND_AVAILABLE:
            # Register drag sources — do NOT bind B1-Motion manually,
            # it would intercept events before tkinterdnd2 detects the drag gesture
            for w in (self, drag_icon, self.text_widget):
                try:
                    w.drag_source_register(DND_TEXT)
                    w.dnd_bind("<<DragInitCmd>>", self._drag_init)
                    w.dnd_bind("<<DragEndCmd>>", self._drag_end)
                except Exception:
                    pass
            # Click detection: if mouse released without drag, treat as copy
            for w in (self, drag_icon, self.text_widget):
                w.bind("<ButtonPress-1>", self._on_press)
                w.bind("<ButtonRelease-1>", self._on_click_release)
        else:
            # Fallback without DnD: click to copy
            for w in (self, drag_icon, self.text_widget):
                w.bind("<ButtonPress-1>", self._on_press)
                w.bind("<B1-Motion>", self._on_motion)
                w.bind("<ButtonRelease-1>", self._on_release)

    def _drag_init(self, event):
        self._dragging = True
        return ("copy", DND_TEXT, self.item["text"])

    def _drag_end(self, event):
        self._dragging = False

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root
        self._drag_started = False

    def _on_click_release(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx < 5 and dy < 5 and not self._dragging:
            self.on_copy(self.item["text"])

    # Fallback handlers (no DnD)
    def _on_motion(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx > 5 or dy > 5:
            self._drag_started = True

    def _on_release(self, event):
        if not self._drag_started:
            self.on_copy(self.item["text"])

    def _on_enter(self, event):
        if not self._hover:
            self._hover = True
            self._set_bg(CARD_HOVER)
            self._select_all()

    def _on_leave(self, event):
        widget_under = self.winfo_containing(event.x_root, event.y_root)
        if widget_under and (widget_under is self or str(widget_under).startswith(str(self))):
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
        for w in self.winfo_children():
            try:
                if isinstance(w, tk.Frame):
                    if w.cget("bg") not in (ACCENT, PANEL_BG):
                        w.configure(bg=color)
                        for ww in w.winfo_children():
                            try:
                                if ww.cget("bg") not in (ACCENT, PANEL_BG) and not isinstance(ww, tk.Text):
                                    ww.configure(bg=color)
                            except Exception:
                                pass
            except Exception:
                pass
        try:
            self.configure(bg=color)
        except Exception:
            pass

    def refresh(self):
        self.label_lbl.configure(text=self.item["label"])
        line_count = self.item["text"].count("\n") + 1
        self.text_widget.configure(state="normal", height=line_count)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", self.item["text"])
        self.text_widget.configure(state="disabled")


class App:
    def __init__(self):
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("Clipboard Manager")
        self.root.geometry("500x620")
        self.root.configure(bg=DARK_BG)
        self.root.resizable(True, True)
        self.root.minsize(400, 400)

        self.items = load_items()
        self.cards = []
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)

        self._build_ui()
        self._render_cards(self.items)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=PANEL_BG, padx=20, pady=16)
        header.pack(fill="x")

        title = tk.Label(
            header, text="\U0001f4cb Clipboard Manager",
            bg=PANEL_BG, fg=TEXT_PRIMARY,
            font=("Helvetica", 16, "bold")
        )
        title.pack(side="left")

        add_btn = tk.Button(
            header, text="+ Add",
            bg=ACCENT, fg="#ffffff",
            font=("Helvetica", 10, "bold"),
            relief="flat", cursor="hand2",
            activebackground=ACCENT2,
            activeforeground="#ffffff",
            padx=12, pady=4,
            command=self._add_item
        )
        add_btn.pack(side="right")

        search_frame = tk.Frame(self.root, bg=DARK_BG, padx=16, pady=10)
        search_frame.pack(fill="x")

        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            bg=PANEL_BG, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            font=("Helvetica", 11),
            relief="flat", bd=0
        )
        search_entry.pack(fill="x", ipady=8, padx=8)
        search_entry.insert(0, "\U0001f50d  Search...")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, "end") if search_entry.get().startswith("\U0001f50d") else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "\U0001f50d  Search...") if not search_entry.get().strip() else None)

        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill="x")

        if not DND_AVAILABLE:
            warn = tk.Label(
                self.root,
                text="⚠  tkinterdnd2 not installed. pip install tkinterdnd2",
                bg="#3b2f00", fg="#fbbf24",
                font=("Helvetica", 9), padx=10, pady=5
            )
            warn.pack(fill="x")

        container = tk.Frame(self.root, bg=DARK_BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.cards_frame = tk.Frame(canvas, bg=DARK_BG)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.cards_frame, anchor="nw", tags="frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("frame", width=e.width))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.canvas = canvas

        self.status_var = tk.StringVar(value="Наведи на карточку и перетащи текст в любое поле ввода")
        status = tk.Label(
            self.root, textvariable=self.status_var,
            bg=PANEL_BG, fg=TEXT_MUTED,
            font=("Helvetica", 9), pady=6
        )
        status.pack(fill="x", side="bottom")

    def _render_cards(self, items):
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        for item in items:
            card = ClipCard(
                self.cards_frame, item,
                on_copy=self._copy_text,
                on_edit=self._edit_card,
                on_delete=self._delete_card
            )
            card.pack(fill="x", padx=12, pady=6)
            self.cards.append(card)

    def _on_search(self, *args):
        q = self.search_var.get().lower().strip()
        if not q or q.startswith("\U0001f50d"):
            filtered = self.items
        else:
            filtered = [i for i in self.items if q in i["label"].lower() or q in i["text"].lower()]
        self._render_cards(filtered)

    def _copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set(f"✓ Скопировано: {text[:50]}{'…' if len(text) > 50 else ''}")
        self.root.after(3000, lambda: self.status_var.set("Наведи на карточку и перетащи текст в любое поле ввода"))

    def _add_item(self):
        label = simpledialog.askstring("Новый элемент", "Название:", parent=self.root)
        if not label:
            return
        text = simpledialog.askstring("Новый элемент", "Текст:", parent=self.root)
        if text is None:
            return
        self.items.append({"label": label, "text": text})
        save_items(self.items)
        self._render_cards(self.items)

    def _edit_card(self, card):
        item = card.item
        label = simpledialog.askstring("Редактировать", "Название:", initialvalue=item["label"], parent=self.root)
        if label is None:
            return
        text = simpledialog.askstring("Редактировать", "Текст:", initialvalue=item["text"], parent=self.root)
        if text is None:
            return
        item["label"] = label
        item["text"] = text
        save_items(self.items)
        self._render_cards(self.items)

    def _delete_card(self, card):
        if messagebox.askyesno("Удалить", f'Удалить "{card.item["label"]}"?', parent=self.root):
            self.items.remove(card.item)
            save_items(self.items)
            self._render_cards(self.items)

    def _on_close(self):
        save_items(self.items)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
