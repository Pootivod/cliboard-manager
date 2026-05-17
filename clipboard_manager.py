"""
Clipboard Manager — Indigo Dusk
Requirements: pip install PyQt6
"""

import json
import os
import sys
import uuid
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout,
    QScrollArea, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QPropertyAnimation,
    QEasingCurve, pyqtSignal, QObject, QMimeData,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QBrush, QPen, QFont,
    QLinearGradient, QDrag, QPixmap, QCursor, QFontMetrics,
    QRadialGradient,
)

# ── Paths ──────────────────────────────────────────────────────────────────────
SAVE_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_manager_v2.json")

# ── Design tokens ──────────────────────────────────────────────────────────────
BG       = "#1e1e2e"
PANEL    = "#2a2a3e"
CARD     = "#313147"
ACCENT   = "#7c6af7"
SUCCESS  = "#5fbf85"
DANGER   = "#ff7a7a"

C_FG1    = "rgba(255,255,255,0.92)"
C_FG2    = "rgba(255,255,255,0.65)"
C_FG3    = "rgba(255,255,255,0.45)"
C_FG4    = "rgba(255,255,255,0.28)"

PICKER_EMOJI = ["📧","🏢","📞","📍","🔗","🔑","💳","📝","⚡","🌐","📁","⭐"]

DEFAULT_TABLES = [
    {
        "id": "work", "emoji": "💼", "name": "Work",
        "cells": [
            {"emoji": "📧", "label": "Email",   "text": "alex.morgan@northwind.co"},
            None,
            {"emoji": "🏢", "label": "Office",  "text": "500 7th Ave, Floor 12\nNew York, NY 10018"},
            None,
            {"emoji": "📞", "label": "Phone",   "text": "+1 (415) 555 · 0182"},
            None, None,
            {"emoji": "📍", "label": "ZIP",     "text": "94110-2381"},
            None,
            {"emoji": "⚡", "label": "Snippet", "text": "function debounce(fn,ms){…}"},
            None, None,
        ],
    },
    {"id": "personal", "emoji": "🏠", "name": "Personal", "cells": [None]*12},
    {"id": "codes",    "emoji": "🔑", "name": "Codes",    "cells": [None]*12},
    {"id": "links",    "emoji": "🔗", "name": "Links",    "cells": [None]*12},
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def hex_color(h):
    return QColor(h)

def accent_alpha(a):
    c = QColor(ACCENT)
    c.setAlpha(a)
    return c

# ── Cell widget ────────────────────────────────────────────────────────────────
class CellWidget(QWidget):
    clicked     = pyqtSignal(int)
    drag_start  = pyqtSignal(int)

    def __init__(self, index, cell, edit_mode, parent=None):
        super().__init__(parent)
        self.index     = index
        self.cell      = cell
        self.edit_mode = edit_mode
        self._hovered  = False
        self._flash    = False
        self._drop_tgt = False
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_tooltip)
        self._drag_start_pos = None
        self.setFixedSize(82, 82)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_drop_target(self, v):
        self._drop_tgt = v
        self.update()

    def flash_copy(self):
        self._flash = True
        self.update()
        QTimer.singleShot(250, self._clear_flash)

    def _clear_flash(self):
        self._flash = False
        self.update()

    def _show_tooltip(self):
        if self._hovered and self.cell and not self.edit_mode:
            win = self.window()
            if hasattr(win, "show_tooltip"):
                win.show_tooltip(self.index, self)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 14, 14)

        if self.cell is None:
            if self.edit_mode:
                # Ghost slot
                p.setClipPath(path)
                p.fillPath(path, QColor(255, 255, 255, 3))
                pen = QPen(QColor(255, 255, 255, 33))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
                # "+" glyph
                p.setPen(QColor(255, 255, 255, 71))
                font = QFont("Inter", 20, QFont.Weight.Light)
                p.setFont(font)
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, "+")
            # Normal mode: invisible empty slot
            return

        # Dragging placeholder
        if hasattr(self, "_is_placeholder") and self._is_placeholder:
            pen = QPen(accent_alpha(136))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.fillPath(path, accent_alpha(16))
            p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
            return

        # Filled cell background
        if self._drop_tgt:
            bg = QColor(ACCENT)
            bg.setAlpha(60)
        elif self._hovered:
            bg = QColor("#3a3a56")
        else:
            bg = QColor(CARD)

        p.fillPath(path, bg)

        # Border
        if self._flash:
            pen = QPen(QColor(ACCENT))
            pen.setWidth(2)
        elif self._drop_tgt:
            pen = QPen(accent_alpha(170))
            pen.setWidth(2)
        else:
            pen = QPen(QColor(255, 255, 255, 10))
            pen.setWidth(1)
        p.setPen(pen)
        p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)

        p.setClipPath(path)

        # Drag handle in edit mode
        if self.edit_mode:
            p.setPen(QColor(255, 255, 255, 89))
            f = QFont("Inter", 10)
            p.setFont(f)
            p.drawText(QRect(6, 5, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        # Emoji
        emoji_font = QFont("Segoe UI Emoji", 24)
        p.setFont(emoji_font)
        p.setPen(Qt.GlobalColor.white)
        emoji_rect = QRect(0, 8, r.width(), 44)
        p.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

        # Label
        label_font = QFont("Inter", 9, QFont.Weight.Medium)
        p.setFont(label_font)
        p.setPen(QColor(255, 255, 255, 166))
        label_rect = QRect(4, 54, r.width()-8, 22)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.cell["label"])

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        if self.cell and not self.edit_mode:
            self._tooltip_timer.start(3000)

    def leaveEvent(self, e):
        self._hovered = False
        self.update()
        self._tooltip_timer.stop()
        win = self.window()
        if hasattr(win, "hide_tooltip"):
            win.hide_tooltip()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = e.pos()

    def mouseMoveEvent(self, e):
        self._tooltip_timer.stop()
        win = self.window()
        if hasattr(win, "hide_tooltip"):
            win.hide_tooltip()

        if not self.edit_mode or self.cell is None:
            return
        if self._drag_start_pos is None:
            return
        if (e.pos() - self._drag_start_pos).manhattanLength() > 6:
            self.drag_start.emit(self.index)
            self._drag_start_pos = None

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if self._drag_start_pos is not None:
                self.clicked.emit(self.index)
            self._drag_start_pos = None


# ── Lifted cell overlay (drag in flight) ──────────────────────────────────────
class LiftedCell(QWidget):
    def __init__(self, cell, parent=None):
        super().__init__(parent)
        self.cell = cell
        self.setFixedSize(92, 92)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.SubWindow)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(2, 2, r.width()-4, r.height()-4, 14, 14)

        # Glow effect (fake with painted shadow)
        glow = QPen(accent_alpha(80))
        glow.setWidth(6)
        p.setPen(glow)
        p.drawRoundedRect(2, 2, r.width()-4, r.height()-4, 14, 14)

        bg = QColor(49, 49, 71, 220)
        p.fillPath(path, bg)

        border_pen = QPen(accent_alpha(180))
        border_pen.setWidth(2)
        p.setPen(border_pen)
        p.drawRoundedRect(2, 2, r.width()-4, r.height()-4, 13, 13)

        p.setClipPath(path)

        # Drag handle
        p.setPen(QColor(255, 255, 255, 140))
        f = QFont("Inter", 10)
        p.setFont(f)
        p.drawText(QRect(8, 6, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        # Emoji
        emoji_font = QFont("Segoe UI Emoji", 24)
        p.setFont(emoji_font)
        p.setPen(Qt.GlobalColor.white)
        p.drawText(QRect(0, 10, r.width(), 44), Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

        # Label
        label_font = QFont("Inter", 9, QFont.Weight.Medium)
        p.setFont(label_font)
        p.setPen(QColor(255, 255, 255, 204))
        p.drawText(QRect(4, 58, r.width()-8, 22), Qt.AlignmentFlag.AlignCenter, self.cell["label"])


# ── Tooltip widget ─────────────────────────────────────────────────────────────
class TooltipWidget(QWidget):
    def __init__(self, cell, parent=None):
        super().__init__(parent)
        self.cell = cell
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMaximumWidth(220)
        self._calc_size()

    def _calc_size(self):
        self.setFixedHeight(52)
        self.setFixedWidth(min(220, max(140, len(self.cell.get("text","")) * 6 + 40)))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 10, 10)

        bg = QColor(20, 20, 30, 235)
        p.fillPath(path, bg)

        border_pen = QPen(QColor(255, 255, 255, 15))
        border_pen.setWidth(1)
        p.setPen(border_pen)
        p.drawRoundedRect(0, 0, r.width()-1, r.height()-1, 10, 10)

        p.setClipPath(path)

        # Header
        header = f"{self.cell['emoji']} {self.cell['label']}"
        hf = QFont("Inter", 11, QFont.Weight.DemiBold)
        p.setFont(hf)
        p.setPen(QColor(255, 255, 255, 242))
        p.drawText(QRect(11, 8, r.width()-22, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, header)

        # Preview text
        text = self.cell.get("text", "").replace("\n", " ")
        tf = QFont("JetBrains Mono", 10)
        p.setFont(tf)
        p.setPen(QColor(255, 255, 255, 158))
        p.drawText(QRect(11, 28, r.width()-22, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


# ── Sidebar item ───────────────────────────────────────────────────────────────
class SidebarItem(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, table, active=False, parent=None):
        super().__init__(parent)
        self.table   = table
        self.active  = active
        self._hovered = False
        self.setFixedSize(76, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, v):
        self.active = v
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        opacity = 1.0 if self.active else 0.55
        p.setOpacity(opacity)

        # Active pip
        if self.active:
            pip = QPainterPath()
            pip.addRoundedRect(3, 23, 3, 14, 1.5, 1.5)
            p.setOpacity(1.0)
            p.fillPath(pip, QColor(ACCENT))
            p.setOpacity(1.0)

        # Circle
        cx, cy = 38, 22
        cr = 20
        circle_path = QPainterPath()
        circle_path.addEllipse(cx - cr, cy - cr, cr*2, cr*2)

        if self.active:
            bg = accent_alpha(31)
            p.fillPath(circle_path, bg)
            pen = QPen(accent_alpha(102))
            pen.setWidth(1)
            p.setPen(pen)
            p.drawEllipse(cx - cr, cy - cr, cr*2, cr*2)
        else:
            p.setOpacity(0.55)

        # Emoji
        ef = QFont("Segoe UI Emoji", 17)
        p.setFont(ef)
        p.setPen(Qt.GlobalColor.white)
        p.drawText(QRect(cx-cr, cy-cr, cr*2, cr*2), Qt.AlignmentFlag.AlignCenter, self.table["emoji"])

        # Label
        p.setOpacity(opacity)
        lf = QFont("Inter", 8, QFont.Weight.Medium)
        p.setFont(lf)
        color = QColor(255, 255, 255, 217 if self.active else 127)
        p.setPen(color)
        p.drawText(QRect(4, cy+cr+2, 68, 14), Qt.AlignmentFlag.AlignCenter, self.table["name"])

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.table["id"])


# ── Add table button ───────────────────────────────────────────────────────────
class AddTableButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(76, 50)
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, cr = 38, 20, 20
        path = QPainterPath()
        path.addEllipse(cx-cr, cy-cr, cr*2, cr*2)
        pen = QPen(QColor(255, 255, 255, 40))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawEllipse(cx-cr+1, cy-cr+1, (cr-1)*2, (cr-1)*2)
        f = QFont("Inter", 18, QFont.Weight.Light)
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 102))
        p.drawText(QRect(cx-cr, cy-cr, cr*2, cr*2), Qt.AlignmentFlag.AlignCenter, "+")

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ── Sidebar drop target indicator ─────────────────────────────────────────────
class SidebarDropTarget(QWidget):
    """Visual highlight ring drawn over a sidebar item during drag-over."""
    def __init__(self, table_id, parent=None):
        super().__init__(parent)
        self.table_id = table_id
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(accent_alpha(180))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawEllipse(18, 2, 40, 40)


# ── Edit Cell Modal ────────────────────────────────────────────────────────────
class EditModal(QWidget):
    saved   = pyqtSignal(dict)
    deleted = pyqtSignal()
    closed  = pyqtSignal()

    def __init__(self, cell, mode, parent=None):
        super().__init__(parent)
        self.mode = mode  # 'edit' or 'new'
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setGeometry(parent.rect() if parent else QRect(0,0,480,580))

        self._selected_emoji = cell["emoji"] if cell else PICKER_EMOJI[0]
        self._confirm_delete = False
        self._delete_timer   = None

        self._build_ui(cell)
        self.raise_()

    def _build_ui(self, cell):
        # Full-window backdrop
        self.setStyleSheet("background: rgba(10,10,16,140);")

        # Modal box
        box = QFrame(self)
        box.setFixedSize(300, 230)
        pw, ph = self.width(), self.height()
        box.move((pw-300)//2, (ph-230)//2)
        box.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 16px;
            }}
        """)
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(60)
        eff.setOffset(0, 20)
        eff.setColor(QColor(0,0,0,153))
        box.setGraphicsEffect(eff)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header
        header = QLabel("EDIT CELL")
        header.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; font-weight: 600; letter-spacing: 1.2px;")
        layout.addWidget(header)

        # Emoji picker
        picker_frame = QFrame()
        picker_frame.setStyleSheet("background: rgba(0,0,0,56); border-radius: 10px; padding: 4px;")
        picker_layout = QHBoxLayout(picker_frame)
        picker_layout.setContentsMargins(8, 4, 8, 4)
        picker_layout.setSpacing(4)

        self._selected_lbl = QLabel(self._selected_emoji)
        self._selected_lbl.setStyleSheet(f"font-size: 24px; padding: 0 4px;")
        picker_layout.addWidget(self._selected_lbl)

        divider = QFrame()
        divider.setFixedSize(1, 22)
        divider.setStyleSheet("background: rgba(255,255,255,0.08);")
        picker_layout.addWidget(divider)

        others = [e for e in PICKER_EMOJI if e != self._selected_emoji][:8]
        for em in others:
            btn = QPushButton(em)
            btn.setFixedSize(26, 26)
            btn.setStyleSheet("font-size: 13px; background: transparent; border: none; border-radius: 6px; opacity: 0.7; padding: 0;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, e=em: self._pick_emoji(e))
            picker_layout.addWidget(btn)

        picker_layout.addStretch()
        layout.addWidget(picker_frame)

        # Label field
        label_lbl = QLabel("LABEL")
        label_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 9px; font-weight: 600; letter-spacing: 0.8px;")
        layout.addWidget(label_lbl)

        self._label_input = QLineEdit(cell["label"] if cell else "")
        self._label_input.setFixedHeight(32)
        self._label_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(0,0,0,71);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                padding: 0 10px;
                color: rgba(255,255,255,0.92);
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT}88;
            }}
        """)
        layout.addWidget(self._label_input)

        # Content field
        content_lbl = QLabel("CONTENT")
        content_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 9px; font-weight: 600; letter-spacing: 0.8px;")
        layout.addWidget(content_lbl)

        self._content_input = QTextEdit(cell["text"] if cell else "")
        self._content_input.setFixedHeight(56)
        self._content_input.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(0,0,0,71);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                padding: 7px 10px;
                color: rgba(255,255,255,0.78);
                font-family: 'JetBrains Mono';
                font-size: 10px;
                line-height: 1.45;
            }}
            QTextEdit:focus {{
                border: 1px solid {ACCENT}88;
            }}
        """)
        layout.addWidget(self._content_input)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if self.mode == "edit":
            self._del_btn = QPushButton("Delete")
            self._del_btn.setFixedHeight(30)
            self._del_btn.setStyleSheet("""
                QPushButton {
                    padding: 0 14px;
                    border-radius: 8px;
                    border: 1px solid rgba(255,80,80,0.3);
                    background: rgba(255,80,80,0.08);
                    color: #ff7a7a;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover { background: rgba(255,80,80,0.15); }
            """)
            self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._del_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(self._del_btn)

        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(30)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0 16px;
                border-radius: 8px;
                border: none;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {ACCENT},stop:1 {ACCENT}cc);
                color: white;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

        self._label_input.setFocus()

    def _pick_emoji(self, emoji):
        self._selected_emoji = emoji
        self._selected_lbl.setText(emoji)

    def _on_save(self):
        label = self._label_input.text().strip()
        text  = self._content_input.toPlainText().strip()
        if not label or not text:
            return
        self.saved.emit({"emoji": self._selected_emoji, "label": label, "text": text})

    def _on_delete(self):
        if self._confirm_delete:
            self.deleted.emit()
        else:
            self._confirm_delete = True
            self._del_btn.setText("Confirm?")
            self._delete_timer = QTimer.singleShot(2000, self._reset_delete)

    def _reset_delete(self):
        self._confirm_delete = False
        if hasattr(self, "_del_btn"):
            self._del_btn.setText("Delete")

    def mousePressEvent(self, e):
        # Click outside modal box → close
        box = self.findChild(QFrame)
        if box and not box.geometry().contains(e.pos()):
            self.closed.emit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.closed.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(10, 10, 16, 140))


# ── Main window ────────────────────────────────────────────────────────────────
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipboard Manager")
        self.setFixedSize(480, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._edit_mode   = False
        self._drag_index  = None
        self._drag_cell   = None
        self._drag_pos    = QPoint()
        self._lifted      = None
        self._drag_over   = None
        self._sidebar_over = None
        self._tooltip_wgt = None
        self._toolbar_drag_pos = None
        self._modal       = None

        self._tables         = []
        self._active_table_id = ""
        self._load_state()

        self._build_ui()
        self._refresh()

    # ── State ──────────────────────────────────────────────────────────────────
    def _load_state(self):
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            self._tables = data.get("tables", DEFAULT_TABLES)
            self._active_table_id = data.get("activeTableId", self._tables[0]["id"])
        except Exception:
            import copy
            self._tables = copy.deepcopy(DEFAULT_TABLES)
            self._active_table_id = self._tables[0]["id"]

    def _save_state(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump({"tables": self._tables, "activeTableId": self._active_table_id}, f)
        except Exception:
            pass

    def _active_table(self):
        for t in self._tables:
            if t["id"] == self._active_table_id:
                return t
        return self._tables[0]

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._main = QWidget(self)
        self._main.setGeometry(0, 0, 480, 580)
        self._main.setStyleSheet(f"background: {BG}; border-radius: 16px;")

        root = QVBoxLayout(self._main)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        self._toolbar = self._make_toolbar()
        root.addWidget(self._toolbar)

        # Body (grid + sidebar)
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        body_layout.addWidget(self._grid_container, 1)

        self._sidebar_container = self._make_sidebar()
        body_layout.addWidget(self._sidebar_container)

        root.addWidget(body, 1)

        # Status bar
        self._statusbar = self._make_statusbar()
        root.addWidget(self._statusbar)

    def _make_toolbar(self):
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"background: rgba(255,255,255,5); border-bottom: 1px solid rgba(255,255,255,13);")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        # App icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ACCENT},stop:1 {ACCENT}aa);
            border-radius: 7px;
        """)

        # Title
        title = QLabel("Clipboard")
        title.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 13px; font-weight: 600; letter-spacing: 0.1px;")

        self._table_suffix = QLabel()
        self._table_suffix.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px;")

        left = QHBoxLayout()
        left.setSpacing(9)
        left.addWidget(icon_lbl)
        left.addWidget(title)
        left.addWidget(self._table_suffix)
        layout.addLayout(left)
        layout.addStretch()

        # Search icon
        search_btn = QPushButton()
        search_btn.setFixedSize(22, 22)
        search_btn.setStyleSheet("background: transparent; border: none; color: rgba(255,255,255,0.45);")
        search_btn.setText("⌕")
        search_btn.setFont(QFont("Inter", 15))
        layout.addWidget(search_btn)

        # Pencil
        self._pencil_btn = QPushButton()
        self._pencil_btn.setFixedSize(28, 28)
        self._pencil_btn.setText("✎")
        self._pencil_btn.setFont(QFont("Inter", 13))
        self._pencil_btn.setStyleSheet("background: transparent; border: none; border-radius: 8px; color: rgba(255,255,255,0.6);")
        self._pencil_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pencil_btn.clicked.connect(self._toggle_edit)
        layout.addWidget(self._pencil_btn)

        bar.mousePressEvent   = self._toolbar_mouse_press
        bar.mouseMoveEvent    = self._toolbar_mouse_move
        bar.mouseReleaseEvent = self._toolbar_mouse_release
        return bar

    def _make_sidebar(self):
        container = QWidget()
        container.setFixedWidth(76)
        container.setStyleSheet("background: transparent; border-left: 1px solid rgba(255,255,255,9);")
        self._sidebar_layout = QVBoxLayout(container)
        self._sidebar_layout.setContentsMargins(0, 14, 0, 14)
        self._sidebar_layout.setSpacing(4)
        self._sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        return container

    def _make_statusbar(self):
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet("background: rgba(255,255,255,5); border-top: 1px solid rgba(255,255,255,10);")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)

        self._status_left = QLabel()
        self._status_left.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 10px; font-weight: 500; letter-spacing: 0.3px;")

        hint = QLabel("Ctrl+V")
        hint.setStyleSheet("color: rgba(255,255,255,0.32); font-family: 'JetBrains Mono'; font-size: 10px;")

        layout.addWidget(self._status_left)
        layout.addStretch()
        layout.addWidget(hint)
        return bar

    # ── Refresh UI ─────────────────────────────────────────────────────────────
    def _refresh(self):
        self._refresh_toolbar()
        self._refresh_grid()
        self._refresh_sidebar()
        self._refresh_statusbar()

    def _refresh_toolbar(self):
        t = self._active_table()
        self._table_suffix.setText(f"· {t['name']}")
        if self._edit_mode:
            self._toolbar.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {ACCENT}1f,stop:1 {ACCENT}0a);
                border-bottom: 1px solid {ACCENT}55;
            """)
            self._pencil_btn.setStyleSheet(f"""
                background: {ACCENT}33; border: none; border-radius: 8px;
                color: {ACCENT};
            """)
        else:
            self._toolbar.setStyleSheet("background: rgba(255,255,255,5); border-bottom: 1px solid rgba(255,255,255,13);")
            self._pencil_btn.setStyleSheet("background: transparent; border: none; border-radius: 8px; color: rgba(255,255,255,0.6);")

    def _refresh_grid(self):
        # Remove old grid widget
        old = self._grid_container.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)

        cells = self._active_table()["cells"]
        grid_layout = QGridLayout(self._grid_container)
        grid_layout.setContentsMargins(12, 14, 12, 10)
        grid_layout.setSpacing(9)

        self._cell_widgets = []
        for i, cell in enumerate(cells):
            row, col = divmod(i, 4)
            w = CellWidget(i, cell, self._edit_mode, self._grid_container)
            w.clicked.connect(self._on_cell_clicked)
            w.drag_start.connect(self._on_drag_start)
            grid_layout.addWidget(w, row, col)
            self._cell_widgets.append(w)

    def _refresh_sidebar(self):
        layout = self._sidebar_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for t in self._tables:
            item = SidebarItem(t, t["id"] == self._active_table_id)
            item.clicked.connect(self._switch_table)
            layout.addWidget(item)

        layout.addStretch()

        if self._edit_mode:
            add_btn = AddTableButton()
            add_btn.clicked.connect(self._add_table)
            layout.addWidget(add_btn)

    def _refresh_statusbar(self):
        cells = self._active_table()["cells"]
        filled = sum(1 for c in cells if c is not None)
        free   = sum(1 for c in cells if c is None)
        if self._edit_mode:
            dot_color = ACCENT
            text = f"● EDIT MODE"
        else:
            dot_color = SUCCESS
            text = f"● {filled} ITEMS · {free} FREE"
        self._status_left.setText(text)
        self._status_left.setStyleSheet(f"color: {dot_color if self._edit_mode else SUCCESS}; font-size: 10px; font-weight: 500; letter-spacing: 0.3px;")

    # ── Actions ────────────────────────────────────────────────────────────────
    def _toggle_edit(self):
        self._edit_mode = not self._edit_mode
        self.hide_tooltip()
        self._close_modal()
        self._refresh()

    def _switch_table(self, table_id):
        self._active_table_id = table_id
        self._close_modal()
        self.hide_tooltip()
        self._refresh()
        self._save_state()

    def _add_table(self):
        new_id = str(uuid.uuid4())[:8]
        self._tables.append({
            "id": new_id, "emoji": "📂", "name": "New",
            "cells": [None] * 12,
        })
        self._active_table_id = new_id
        self._refresh()
        self._save_state()

    def _on_cell_clicked(self, idx):
        cells = self._active_table()["cells"]
        cell  = cells[idx]
        if self._edit_mode:
            mode = "edit" if cell else "new"
            self._open_modal(idx, cell, mode)
        else:
            if cell:
                self._copy_cell(idx, cell)

    def _copy_cell(self, idx, cell):
        QApplication.clipboard().setText(cell["text"])
        # Flash
        if idx < len(self._cell_widgets):
            self._cell_widgets[idx].flash_copy()
        # Status
        self._status_left.setText("● COPIED")
        self._status_left.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: 500; letter-spacing: 0.3px;")
        QTimer.singleShot(1500, self._refresh_statusbar)

    def _open_modal(self, idx, cell, mode):
        self._close_modal()
        modal = EditModal(cell, mode, self._main)
        modal.setGeometry(0, 0, 480, 580)
        modal.saved.connect(lambda c: self._modal_save(idx, c))
        modal.deleted.connect(lambda: self._modal_delete(idx))
        modal.closed.connect(self._close_modal)
        modal.show()
        self._modal = modal

    def _close_modal(self):
        if self._modal:
            self._modal.hide()
            self._modal.deleteLater()
            self._modal = None

    def _modal_save(self, idx, cell_data):
        t = self._active_table()
        t["cells"][idx] = cell_data
        self._close_modal()
        self._refresh()
        self._save_state()

    def _modal_delete(self, idx):
        t = self._active_table()
        t["cells"][idx] = None
        self._close_modal()
        self._refresh()
        self._save_state()

    # ── Drag & Drop (edit mode internal reorder) ───────────────────────────────
    def _on_drag_start(self, from_index):
        cells = self._active_table()["cells"]
        cell  = cells[from_index]
        if cell is None:
            return
        self._drag_index = from_index
        self._drag_cell  = cell
        self._drag_over  = None

        # Show placeholder in origin
        if from_index < len(self._cell_widgets):
            w = self._cell_widgets[from_index]
            w._is_placeholder = True
            w.update()

        # Create lifted cell overlay
        if self._lifted:
            self._lifted.hide()
            self._lifted = None
        self._lifted = LiftedCell(cell, self._main)
        cursor_pos = self._main.mapFromGlobal(QCursor.pos())
        self._lifted.move(cursor_pos.x() - 46, cursor_pos.y() - 46)
        self._lifted.show()
        self._lifted.raise_()

        self.setMouseTracking(True)
        self._main.setMouseTracking(True)
        self._grid_container.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        if self._drag_index is None:
            return
        pos = e.pos()
        if self._lifted:
            self._lifted.move(pos.x() - 46, pos.y() - 46)

        # Detect which cell is under cursor
        grid_pos = self._grid_container.mapFrom(self, pos)
        new_over = None
        for i, w in enumerate(self._cell_widgets):
            if i == self._drag_index:
                continue
            local = w.mapFrom(self._grid_container, grid_pos)
            if w.rect().contains(local):
                new_over = i
                break

        if new_over != self._drag_over:
            if self._drag_over is not None and self._drag_over < len(self._cell_widgets):
                self._cell_widgets[self._drag_over].set_drop_target(False)
            self._drag_over = new_over
            if new_over is not None and new_over < len(self._cell_widgets):
                self._cell_widgets[new_over].set_drop_target(True)

    def mouseReleaseEvent(self, e):
        if self._drag_index is None:
            return
        if self._drag_over is not None:
            # Swap cells
            t = self._active_table()
            cells = t["cells"]
            cells[self._drag_index], cells[self._drag_over] = cells[self._drag_over], cells[self._drag_index]
            self._save_state()

        # Cleanup
        if self._lifted:
            self._lifted.hide()
            self._lifted.deleteLater()
            self._lifted = None

        self._drag_index = None
        self._drag_cell  = None
        self._drag_over  = None
        self.setMouseTracking(False)
        self._main.setMouseTracking(False)
        self._grid_container.setMouseTracking(False)
        self._refresh()

    # ── Tooltip ────────────────────────────────────────────────────────────────
    def show_tooltip(self, cell_index, cell_widget):
        self.hide_tooltip()
        cells = self._active_table()["cells"]
        cell  = cells[cell_index]
        if not cell:
            return
        t = TooltipWidget(cell, self._main)
        # Position: below-right of cell
        cell_pos = cell_widget.mapTo(self._main, QPoint(0, cell_widget.height() + 10))
        x = cell_pos.x() + cell_widget.width() // 2
        y = cell_pos.y()
        # Clamp to window
        x = min(x, 480 - t.width() - 8)
        y = min(y, 580 - t.height() - 8)
        t.move(x, y)
        t.raise_()
        t.show()
        self._tooltip_wgt = t

    def hide_tooltip(self):
        if self._tooltip_wgt:
            self._tooltip_wgt.hide()
            self._tooltip_wgt.deleteLater()
            self._tooltip_wgt = None

    # ── Toolbar drag (window move) ─────────────────────────────────────────────
    def _toolbar_mouse_press(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._toolbar_drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _toolbar_mouse_move(self, e):
        if self._toolbar_drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._toolbar_drag_pos)

    def _toolbar_mouse_release(self, e):
        self._toolbar_drag_pos = None

    # ── Paint window background with rounded corners ───────────────────────────
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.fillPath(path, QColor(BG))

    # ── Keyboard shortcuts ─────────────────────────────────────────────────────
    def keyPressEvent(self, e):
        modifiers = e.modifiers()
        ctrl = Qt.KeyboardModifier.ControlModifier
        if modifiers & ctrl and e.key() == Qt.Key.Key_E:
            self._toggle_edit()
        elif e.key() == Qt.Key.Key_Escape:
            self._close_modal()
        elif modifiers & ctrl:
            key = e.key()
            for i, t in enumerate(self._tables):
                if key == Qt.Key.Key_1 + i:
                    self._switch_table(t["id"])
                    break
        else:
            super().keyPressEvent(e)


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clipboard Manager")

    # Use Inter font if available
    QApplication.setFont(QFont("Inter", 10))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
