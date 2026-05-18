"""
Clipboard Manager — all reusable widgets
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore  import Qt, QTimer, QPoint, QRect, QRectF, QSize, pyqtSignal, QMimeData
from PyQt6.QtGui   import (
    QColor, QPainter, QPainterPath, QPen, QFont, QDrag, QPixmap,
)

from cm_constants import (
    ACCENT, BG, PANEL, CARD, SUCCESS, DANGER, CELL_SIZE, PICKER_EMOJI,
)


# ── Colour helpers ─────────────────────────────────────────────────────────────
def _ac(alpha: int) -> QColor:
    c = QColor(ACCENT)
    c.setAlpha(alpha)
    return c


# ══════════════════════════════════════════════════════════════════════════════
#  CellWidget
# ══════════════════════════════════════════════════════════════════════════════
class CellWidget(QWidget):
    """Single emoji cell — handles both normal (external DnD) and edit (reorder) modes."""
    clicked     = pyqtSignal(int)   # emitted on clean click
    drag_start  = pyqtSignal(int)   # emitted when edit-mode drag gesture detected

    def __init__(self, index: int, cell: dict | None, edit_mode: bool, parent=None):
        super().__init__(parent)
        self.index      = index
        self.cell       = cell
        self.edit_mode  = edit_mode

        self._hovered         = False
        self._is_placeholder  = False   # show dashed outline while being dragged
        self._is_drop_target  = False
        self._flash           = False
        self._drag_start_pos  = None

        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._request_tooltip)

        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── public helpers ────────────────────────────────────────────────────────
    def set_placeholder(self, v: bool):
        self._is_placeholder = v
        self.update()

    def set_drop_target(self, v: bool):
        self._is_drop_target = v
        self.update()

    def flash_copy(self):
        self._flash = True
        self.update()
        QTimer.singleShot(250, self._clear_flash)

    def _clear_flash(self):
        self._flash = False
        self.update()

    def _request_tooltip(self):
        if self._hovered and self.cell and not self.edit_mode:
            win = self.window()
            if hasattr(win, "show_tooltip"):
                win.show_tooltip(self.index, self)

    # ── paint ─────────────────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 14, 14)

        # ── empty cell ────────────────────────────────────────────────────────
        if self.cell is None:
            if self.edit_mode:
                p.fillPath(path, QColor(255, 255, 255, 3))
                pen = QPen(QColor(255, 255, 255, 33))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
                p.setPen(QColor(255, 255, 255, 71))
                p.setFont(QFont("Inter", 20, QFont.Weight.Light))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, "+")
            return

        # ── drag placeholder (origin slot while cell is flying) ───────────────
        if self._is_placeholder:
            pen = QPen(_ac(136))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.fillPath(path, _ac(16))
            p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
            return

        # ── filled cell ───────────────────────────────────────────────────────
        if self._is_drop_target:
            bg = _ac(55)
        elif self._hovered:
            bg = QColor("#3a3a56")
        else:
            bg = QColor(CARD)
        p.fillPath(path, bg)

        # border / flash ring
        if self._flash:
            pen = QPen(QColor(ACCENT)); pen.setWidth(2)
        elif self._is_drop_target:
            pen = QPen(_ac(170)); pen.setWidth(2)
        else:
            pen = QPen(QColor(255, 255, 255, 10)); pen.setWidth(1)
        p.setPen(pen)
        p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)

        p.setClipPath(path)

        # drag handle (edit mode)
        if self.edit_mode:
            p.setPen(QColor(255, 255, 255, 89))
            p.setFont(QFont("Inter", 10))
            p.drawText(QRect(6, 5, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        # emoji  (centred in upper 60 % of cell)
        emoji_rect = QRect(0, 6, r.width(), int(r.height() * 0.62))
        p.setFont(QFont("Segoe UI Emoji", 22))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

        # label  (bottom 30 %)
        label_rect = QRect(4, int(r.height() * 0.66), r.width()-8, int(r.height() * 0.28))
        p.setFont(QFont("Inter", 9, QFont.Weight.Medium))
        p.setPen(QColor(255, 255, 255, 166))
        p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.cell["label"])

    # ── mouse events ──────────────────────────────────────────────────────────
    def enterEvent(self, _):
        self._hovered = True
        self.update()
        if self.cell and not self.edit_mode:
            self._tooltip_timer.stop()
            self._tooltip_timer.start(3000)

    def leaveEvent(self, _):
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
        # hide tooltip on movement
        self._tooltip_timer.stop()
        win = self.window()
        if hasattr(win, "hide_tooltip"):
            win.hide_tooltip()

        if self._drag_start_pos is None:
            return
        dist = (e.pos() - self._drag_start_pos).manhattanLength()
        if dist < 8:
            return

        if self.edit_mode:
            if self.cell is not None:
                self.drag_start.emit(self.index)
                # MainWindow calls grabMouse() — no further handling needed here
            self._drag_start_pos = None
            return
        else:
            # external drag — copy text to any app
            if self.cell is not None:
                self._start_external_drag(e.pos())
            self._drag_start_pos = None

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            self._drag_start_pos = None
            self.clicked.emit(self.index)

    def _start_external_drag(self, hot_spot):
        mime = QMimeData()
        mime.setText(self.cell["text"])

        drag = QDrag(self)
        drag.setMimeData(mime)

        # render the cell as the drag pixmap
        px = QPixmap(self.size())
        px.fill(Qt.GlobalColor.transparent)
        self.render(px)
        drag.setPixmap(px)
        drag.setHotSpot(hot_spot)

        drag.exec(Qt.DropAction.CopyAction)


# ══════════════════════════════════════════════════════════════════════════════
#  LiftedCell  (floating drag-in-flight overlay)
# ══════════════════════════════════════════════════════════════════════════════
class LiftedCell(QWidget):
    def __init__(self, cell: dict, parent=None):
        super().__init__(parent)
        self.cell = cell
        sz = CELL_SIZE + 8
        self.setFixedSize(sz, sz)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r  = self.rect()
        m  = 4                          # margin for glow halo
        iw = r.width()  - 2*m
        ih = r.height() - 2*m
        inner = QRectF(m, m, iw, ih)
        path  = QPainterPath()
        path.addRoundedRect(inner, 14, 14)

        # glow halo
        for i in range(3, 0, -1):
            glow = QPen(_ac(30 * i))
            glow.setWidth(i * 3)
            p.setPen(glow)
            p.drawRoundedRect(inner, 14, 14)

        # background
        p.fillPath(path, QColor(49, 49, 71, 220))

        # accent border
        p.setPen(QPen(_ac(180), 2))
        p.drawRoundedRect(inner.adjusted(1, 1, -1, -1), 13, 13)

        p.setClipPath(path)

        # drag handle
        p.setPen(QColor(255, 255, 255, 140))
        p.setFont(QFont("Inter", 10))
        p.drawText(QRect(m+6, m+5, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        # emoji
        er = QRect(m, m+6, iw, int(ih * 0.62))
        p.setFont(QFont("Segoe UI Emoji", 22))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(er, Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

        # label
        lr = QRect(m+4, m + int(ih*0.66), iw-8, int(ih*0.28))
        p.setFont(QFont("Inter", 9, QFont.Weight.Medium))
        p.setPen(QColor(255, 255, 255, 204))
        p.drawText(lr, Qt.AlignmentFlag.AlignCenter, self.cell["label"])


# ══════════════════════════════════════════════════════════════════════════════
#  TooltipWidget
# ══════════════════════════════════════════════════════════════════════════════
class TooltipWidget(QWidget):
    def __init__(self, cell: dict, parent=None):
        super().__init__(parent)
        self.cell = cell
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(210, 52)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 10, 10)

        p.fillPath(path, QColor(20, 20, 30, 235))
        p.setPen(QPen(QColor(255, 255, 255, 15), 1))
        p.drawRoundedRect(0, 0, r.width()-1, r.height()-1, 10, 10)
        p.setClipPath(path)

        header = f"{self.cell['emoji']} {self.cell['label']}"
        p.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        p.setPen(QColor(255, 255, 255, 242))
        p.drawText(QRect(11, 7, r.width()-22, 18), Qt.AlignmentFlag.AlignVCenter, header)

        preview = self.cell.get("text", "").replace("\n", " ")
        p.setFont(QFont("JetBrains Mono", 9))
        p.setPen(QColor(255, 255, 255, 158))
        # clip text manually
        fm = p.fontMetrics()
        preview = fm.elidedText(preview, Qt.TextElideMode.ElideRight, r.width()-22)
        p.drawText(QRect(11, 28, r.width()-22, 16), Qt.AlignmentFlag.AlignVCenter, preview)


# ══════════════════════════════════════════════════════════════════════════════
#  Sidebar widgets
# ══════════════════════════════════════════════════════════════════════════════
class SidebarItem(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, table: dict, active: bool = False, parent=None):
        super().__init__(parent)
        self.table   = table
        self.active  = active
        self.setFixedSize(76, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, v: bool):
        self.active = v
        self.update()

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, cr = 38, 22, 19

        # active pip (left edge)
        if self.active:
            pip = QPainterPath()
            pip.addRoundedRect(2, cy-7, 3, 14, 1.5, 1.5)
            p.fillPath(pip, QColor(ACCENT))

        p.setOpacity(1.0 if self.active else 0.55)

        # circle
        circle = QPainterPath()
        circle.addEllipse(cx-cr, cy-cr, cr*2, cr*2)
        if self.active:
            p.fillPath(circle, _ac(31))
            p.setPen(QPen(_ac(102), 1))
            p.drawEllipse(cx-cr, cy-cr, cr*2, cr*2)

        # emoji
        p.setFont(QFont("Segoe UI Emoji", 16))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(QRect(cx-cr, cy-cr, cr*2, cr*2), Qt.AlignmentFlag.AlignCenter, self.table["emoji"])

        # label
        p.setFont(QFont("Inter", 8, QFont.Weight.Medium))
        color = QColor(255, 255, 255, 217 if self.active else 127)
        p.setPen(color)
        p.drawText(QRect(4, cy+cr+3, 68, 14), Qt.AlignmentFlag.AlignCenter, self.table["name"])

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.table["id"])


class AddTableButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(76, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, cr = 38, 20, 18
        pen = QPen(QColor(255, 255, 255, 40), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawEllipse(cx-cr, cy-cr, cr*2, cr*2)
        p.setFont(QFont("Inter", 18, QFont.Weight.Light))
        p.setPen(QColor(255, 255, 255, 102))
        p.drawText(QRect(cx-cr, cy-cr, cr*2, cr*2), Qt.AlignmentFlag.AlignCenter, "+")

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ══════════════════════════════════════════════════════════════════════════════
#  EditModal
# ══════════════════════════════════════════════════════════════════════════════
class EditModal(QWidget):
    saved   = pyqtSignal(dict)
    deleted = pyqtSignal()
    closed  = pyqtSignal()

    def __init__(self, cell: dict | None, mode: str, parent=None):
        super().__init__(parent)
        self.mode              = mode   # 'edit' | 'new'
        self._selected_emoji   = cell["emoji"] if cell else PICKER_EMOJI[0]
        self._confirm_delete   = False
        self._del_btn          = None

        self.setGeometry(parent.rect() if parent else QRect(0, 0, 480, 580))
        self._build(cell)
        self.raise_()

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self, cell):
        # modal box — fixed width, auto height
        box = QFrame(self)
        box.setFixedWidth(300)
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
        eff.setColor(QColor(0, 0, 0, 153))
        box.setGraphicsEffect(eff)

        v = QVBoxLayout(box)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(8)

        # header
        hdr = QLabel("EDIT CELL")
        hdr.setStyleSheet("color:rgba(255,255,255,.5);font-size:11px;font-weight:600;letter-spacing:1.2px;background:transparent;border:none;")
        v.addWidget(hdr)

        # emoji picker row
        picker = QFrame()
        picker.setStyleSheet("background:rgba(0,0,0,56);border-radius:10px;border:none;")
        ph = QHBoxLayout(picker)
        ph.setContentsMargins(8, 6, 8, 6)
        ph.setSpacing(4)

        self._sel_lbl = QLabel(self._selected_emoji)
        self._sel_lbl.setStyleSheet("font-size:24px;padding:0 4px;background:transparent;border:none;")
        ph.addWidget(self._sel_lbl)

        div = QFrame()
        div.setFixedSize(1, 22)
        div.setStyleSheet("background:rgba(255,255,255,.08);border:none;")
        ph.addWidget(div)

        others = [e for e in PICKER_EMOJI if e != self._selected_emoji][:8]
        for em in others:
            btn = QPushButton(em)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet("font-size:13px;background:transparent;border:none;border-radius:6px;padding:0;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, e=em: self._pick(e))
            ph.addWidget(btn)
        ph.addStretch()
        v.addWidget(picker)

        # label field
        v.addWidget(self._field_label("LABEL"))
        self._lbl_input = QLineEdit(cell["label"] if cell else "")
        self._lbl_input.setFixedHeight(32)
        self._lbl_input.setStyleSheet(self._input_style())
        v.addWidget(self._lbl_input)

        # content field
        v.addWidget(self._field_label("CONTENT"))
        self._txt_input = QTextEdit(cell["text"] if cell else "")
        self._txt_input.setFixedHeight(62)
        self._txt_input.setStyleSheet(self._textarea_style())
        v.addWidget(self._txt_input)

        # button row
        row = QHBoxLayout()
        row.setSpacing(8)
        if self.mode == "edit":
            self._del_btn = QPushButton("Delete")
            self._del_btn.setFixedHeight(30)
            self._del_btn.setStyleSheet("""
                QPushButton{padding:0 14px;border-radius:8px;border:1px solid rgba(255,80,80,.3);
                            background:rgba(255,80,80,.08);color:#ff7a7a;font-size:11px;font-weight:600;}
                QPushButton:hover{background:rgba(255,80,80,.15);}
            """)
            self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._del_btn.clicked.connect(self._on_delete)
            row.addWidget(self._del_btn)
        row.addStretch()
        save = QPushButton("Save")
        save.setFixedHeight(30)
        save.setStyleSheet(f"""
            QPushButton{{padding:0 16px;border-radius:8px;border:none;
                         background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {ACCENT},stop:1 {ACCENT}cc);
                         color:white;font-size:11px;font-weight:600;}}
            QPushButton:hover{{opacity:.9;}}
        """)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._on_save)
        row.addWidget(save)
        v.addLayout(row)

        # size and centre
        box.adjustSize()
        pw, ph2 = self.width(), self.height()
        box.move((pw - box.width()) // 2, (ph2 - box.height()) // 2)

        self._lbl_input.setFocus()

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _field_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color:rgba(255,255,255,.4);font-size:9px;font-weight:600;"
                          "letter-spacing:.8px;background:transparent;border:none;")
        return lbl

    @staticmethod
    def _input_style():
        return f"""
            QLineEdit{{background:rgba(0,0,0,71);border:1px solid rgba(255,255,255,.06);
                       border-radius:8px;padding:0 10px;color:rgba(255,255,255,.92);font-size:12px;}}
            QLineEdit:focus{{border:1px solid {ACCENT}88;}}
        """

    @staticmethod
    def _textarea_style():
        return f"""
            QTextEdit{{background:rgba(0,0,0,71);border:1px solid rgba(255,255,255,.06);
                       border-radius:8px;padding:6px 10px;color:rgba(255,255,255,.78);
                       font-family:'JetBrains Mono';font-size:10px;line-height:1.45;}}
            QTextEdit:focus{{border:1px solid {ACCENT}88;}}
        """

    # ── slots ─────────────────────────────────────────────────────────────────
    def _pick(self, emoji):
        self._selected_emoji = emoji
        self._sel_lbl.setText(emoji)

    def _on_save(self):
        label = self._lbl_input.text().strip()
        text  = self._txt_input.toPlainText().strip()
        if label and text:
            self.saved.emit({"emoji": self._selected_emoji, "label": label, "text": text})

    def _on_delete(self):
        if self._confirm_delete:
            self.deleted.emit()
        else:
            self._confirm_delete = True
            self._del_btn.setText("Confirm?")
            QTimer.singleShot(2000, self._reset_delete)

    def _reset_delete(self):
        self._confirm_delete = False
        if self._del_btn:
            self._del_btn.setText("Delete")

    def mousePressEvent(self, e):
        box = self.findChild(QFrame)
        if box and not box.geometry().contains(e.pos()):
            self.closed.emit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.closed.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(10, 10, 16, 140))
