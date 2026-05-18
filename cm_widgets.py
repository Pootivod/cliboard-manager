"""
Clipboard Manager — all reusable widgets
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QScrollArea,
)
from PyQt6.QtCore  import Qt, QTimer, QPoint, QRect, QRectF, QSize, pyqtSignal, QMimeData
from PyQt6.QtGui   import (
    QColor, QPainter, QPainterPath, QPen, QFont, QDrag, QPixmap,
)

from cm_constants import (
    ACCENT, BG, PANEL, CARD, SUCCESS, DANGER, CELL_SIZE, PICKER_EMOJI,
)

# ── Colour helper ──────────────────────────────────────────────────────────────
def _ac(alpha: int) -> QColor:
    c = QColor(ACCENT)
    c.setAlpha(alpha)
    return c

# ── Emoji categories ───────────────────────────────────────────────────────────
EMOJI_CATEGORIES = [
    ("😊", "Смайлы", [
        "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇",
        "🥰","😍","🤩","😘","😗","😚","😙","😋","😛","😜","🤪","😝","🤑",
        "🤗","🤔","🤐","😐","😑","😶","😏","😒","🙄","😬","😌","😔","😪",
        "😴","😷","🤒","🤕","🤢","🤧","🥵","🥶","😵","🤯","🤠","🥳","😎",
        "🤓","🧐","😕","😟","🙁","☹️","😮","😲","😳","🥺","😦","😧","😨",
        "😰","😥","😢","😭","😱","😖","😣","😞","😓","😩","😫","😤","😡",
        "😠","🤬","😈","👿","💀","☠️","💩","🤡","👹","👻","👽","🤖",
    ]),
    ("👋", "Жесты", [
        "👋","🤚","🖐","✋","🖖","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙",
        "👈","👉","👆","🖕","👇","☝️","👍","👎","✊","👊","🤛","🤜","👏",
        "🙌","👐","🤲","🤝","🙏","✍️","💅","💪","💋","👄","👅","👁","👀",
        "👤","👥","🫂","🧠","🦷","🦴","👂","👃",
    ]),
    ("🐶", "Животные", [
        "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
        "🐸","🐵","🐔","🐧","🐦","🦆","🦅","🦉","🦇","🐺","🐴","🦄","🐝",
        "🦋","🐌","🐞","🐜","🐢","🐍","🦎","🐙","🦑","🐡","🐠","🐟","🐬",
        "🐳","🦈","🐊","🐘","🦏","🦛","🦒","🦘","🐕","🐈","🐓","🦃","🕊",
        "🐇","🦝","🦦","🐁","🐀","🐿","🦔",
    ]),
    ("🌺", "Природа", [
        "🌸","💐","🌹","🥀","🌺","🌻","🌼","🌷","🌱","🌲","🌳","🌴","🌵",
        "🌾","🌿","☘️","🍀","🍁","🍂","🍃","🍄","🌰","🌍","🌎","🌏","🌙",
        "🌟","💫","✨","⚡","☄️","💥","🔥","🌈","☀️","⛅","☁️","🌧","⛈",
        "❄️","☃️","⛄","💨","🌪","🌊","💧","💦","🌀",
    ]),
    ("🍕", "Еда", [
        "🍎","🍊","🍋","🍇","🍓","🫐","🍒","🍑","🥭","🍍","🥥","🥝","🍅",
        "🍆","🥑","🥦","🌽","🥕","🍞","🥐","🥚","🍳","🥞","🧇","🥓","🥩",
        "🍗","🍖","🌭","🍔","🍟","🍕","🌮","🌯","🥙","🍿","🥫","🍱","🍣",
        "🍜","🍝","🍛","🍦","🍧","🍨","🍩","🍪","🎂","🍰","🧁","🍫","🍬",
        "🍭","🍯","☕","🍵","🧃","🥤","🧋","🍺","🍷","🥂","🍸","🍹","🧉",
    ]),
    ("⚽", "Активность", [
        "⚽","🏀","🏈","⚾","🎾","🏐","🏉","🎱","🏓","🏸","🥊","🥋","🎽",
        "🛹","🛷","⛸","🎿","⛷","🏂","🏋️","🏄","🏊","🚣","🚵","🚴","🏆",
        "🥇","🥈","🥉","🏅","🎖","🎯","🎳","🎮","🎲","♟","🧩","🎭","🎨",
        "🎬","🎤","🎧","🎼","🎹","🥁","🎷","🎺","🎸","🎻","🎪","🤹",
    ]),
    ("💼", "Работа", [
        "💼","📁","📂","🗂","📋","📊","📈","📉","📝","✏️","✒️","📌","📍",
        "📎","🖇","📐","📏","🔒","🔓","🔑","🗝","🔨","⚙️","🔧","🔩","🔗",
        "🧰","🔬","🔭","📡","💉","💊","🩺","🛒","💡","🔦","📱","💻","🖥",
        "🖨","⌨️","🖱","💾","💿","📀","📺","📷","📸","📹","🎥","📞","☎️",
        "📟","📠","📧","📨","📩","📤","📥","📦","📫","📪","📬","📭","📮",
        "🗳","✉️","📃","📄","📑","🗒","🗓","📆","📅","🗑","📇","📁","🗃",
    ]),
    ("🚗", "Транспорт", [
        "🚗","🚕","🚙","🚌","🚎","🚑","🚒","🚓","🚐","🚚","🚛","🚜","🏎",
        "🛻","🚲","🛴","🛵","🏍","🚨","🚥","🚦","🛑","⛽","🚀","✈️","🛸",
        "🚁","🛶","⛵","🚤","🛳","⚓","🗺","🧭","🏔","⛰","🌋","🏕","🏖",
        "🏙","🏛","🏟","🏠","🏡","🏢","🏣","🏤","🏥","🏦","🏨","🏩","🏪",
        "🏫","🏬","🏭","🏯","🏰","💒","🗼","🗽","⛪","🕌","⛩","🕍",
    ]),
    ("💡", "Символы", [
        "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","❣️","💕","💞",
        "💓","💗","💖","💘","💝","💯","✅","❌","⭕","🛑","⛔","📛","🚫",
        "💢","♨️","🔔","🔕","🔇","🔈","🔉","🔊","📣","📢","💬","💭","🗯",
        "♻️","⚜️","🔰","✴️","❇️","🆗","🆙","🆒","🆕","🆓","🆖","🆘",
        "❗","❕","❓","❔","‼️","⁉️","🔱","📛","🔅","🔆","🔱","⚛️","☮️",
        "✝️","☪️","🕉","✡️","☯️","☦️","🛐","⛎","♈","♉","♊","♋","♌",
        "♍","♎","♏","♐","♑","♒","♓","⭐","🌟","💥","🔥","🌈","☀️",
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════
#  EmojiGrid — custom-painted grid (fast, no per-emoji widget overhead)
# ══════════════════════════════════════════════════════════════════════════════
class EmojiGrid(QWidget):
    emoji_selected = pyqtSignal(str)
    COLS      = 8
    CELL      = 30

    def __init__(self, emojis: list, selected: str, parent=None):
        super().__init__(parent)
        self.emojis   = emojis
        self.selected = selected
        self._hover   = -1
        rows = (len(emojis) + self.COLS - 1) // self.COLS
        self.setFixedSize(self.COLS * self.CELL, rows * self.CELL)
        self.setMouseTracking(True)

    def _idx(self, pos) -> int:
        col = pos.x() // self.CELL
        row = pos.y() // self.CELL
        idx = row * self.COLS + col
        if 0 <= col < self.COLS and 0 <= idx < len(self.emojis):
            return idx
        return -1

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cs = self.CELL
        for i, em in enumerate(self.emojis):
            row, col = divmod(i, self.COLS)
            r = QRect(col * cs, row * cs, cs, cs)
            if em == self.selected:
                p.fillRect(r, _ac(70))
                p.setPen(QPen(_ac(180), 1))
                p.drawRoundedRect(r.adjusted(1,1,-1,-1), 4, 4)
            elif i == self._hover:
                p.fillRect(r, QColor(255, 255, 255, 18))
            p.setFont(QFont("Segoe UI Emoji", 14))
            p.setPen(Qt.GlobalColor.white)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, em)

    def mouseMoveEvent(self, e):
        idx = self._idx(e.pos())
        if idx != self._hover:
            self._hover = idx
            self.update()
            self.setCursor(Qt.CursorShape.PointingHandCursor if idx >= 0
                           else Qt.CursorShape.ArrowCursor)

    def leaveEvent(self, _):
        self._hover = -1
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            idx = self._idx(e.pos())
            if idx >= 0:
                self.selected = self.emojis[idx]
                self.emoji_selected.emit(self.emojis[idx])
                self.update()


# ══════════════════════════════════════════════════════════════════════════════
#  EmojiPickerWidget — category tabs + scrollable grid
# ══════════════════════════════════════════════════════════════════════════════
class EmojiPickerWidget(QWidget):
    emoji_selected = pyqtSignal(str)

    def __init__(self, selected: str = "📧", parent=None):
        super().__init__(parent)
        self._selected  = selected
        self._cat_idx   = 0
        self._cat_btns  = []
        self._build()

    def get_selected(self) -> str:
        return self._selected

    def _build(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        # ── Category tab bar ──────────────────────────────────────────────────
        cat_frame = QWidget()
        cat_frame.setStyleSheet("background:rgba(0,0,0,0.2);border-radius:8px;")
        cat_row = QHBoxLayout(cat_frame)
        cat_row.setContentsMargins(4, 4, 4, 4)
        cat_row.setSpacing(2)

        for i, (icon, name, _) in enumerate(EMOJI_CATEGORIES):
            btn = QPushButton(icon)
            btn.setFixedSize(24, 24)
            btn.setToolTip(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._cat_style(False))
            btn.clicked.connect(lambda _, i=i: self._show_cat(i))
            cat_row.addWidget(btn)
            self._cat_btns.append(btn)
        cat_row.addStretch()
        vbox.addWidget(cat_frame)

        # ── Emoji scroll area ─────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setFixedHeight(150)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{width:4px;background:transparent;}"
            "QScrollBar::handle:vertical{background:rgba(255,255,255,0.2);border-radius:2px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        )
        vbox.addWidget(self._scroll)

        self._show_cat(0)

    @staticmethod
    def _cat_style(active: bool) -> str:
        if active:
            return (f"QPushButton{{font-size:14px;background:rgba(124,106,247,51);"
                    f"border:1px solid rgba(124,106,247,136);border-radius:5px;padding:0;}}")
        return ("QPushButton{font-size:14px;background:transparent;border:none;"
                "border-radius:5px;padding:0;}"
                "QPushButton:hover{background:rgba(255,255,255,0.1);}")

    def _show_cat(self, idx: int):
        self._cat_idx = idx
        for i, btn in enumerate(self._cat_btns):
            btn.setStyleSheet(self._cat_style(i == idx))

        _, _, emojis = EMOJI_CATEGORIES[idx]
        grid = EmojiGrid(emojis, self._selected)
        grid.emoji_selected.connect(self._on_pick)
        self._scroll.setWidget(grid)

    def _on_pick(self, emoji: str):
        self._selected = emoji
        self.emoji_selected.emit(emoji)
        # refresh grid to reflect new selection highlight
        _, _, emojis = EMOJI_CATEGORIES[self._cat_idx]
        grid = EmojiGrid(emojis, self._selected)
        grid.emoji_selected.connect(self._on_pick)
        self._scroll.setWidget(grid)


# ══════════════════════════════════════════════════════════════════════════════
#  CellWidget
# ══════════════════════════════════════════════════════════════════════════════
class CellWidget(QWidget):
    clicked    = pyqtSignal(int)
    drag_start = pyqtSignal(int)

    def __init__(self, index: int, cell: dict | None, edit_mode: bool,
                 parent=None, cell_size: int = CELL_SIZE):
        super().__init__(parent)
        self.index      = index
        self.cell       = cell
        self.edit_mode  = edit_mode
        self._hovered        = False
        self._is_placeholder = False
        self._is_drop_target = False
        self._flash          = False
        self._drag_start_pos = None
        self._tooltip_timer  = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._request_tooltip)
        self.setFixedSize(cell_size, cell_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

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

    def paintEvent(self, _):
        p    = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r    = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 14, 14)

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

        if self._is_placeholder:
            pen = QPen(_ac(136)); pen.setWidth(2); pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.fillPath(path, _ac(16))
            p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
            return

        bg = _ac(55) if self._is_drop_target else (QColor("#3a3a56") if self._hovered else QColor(CARD))
        p.fillPath(path, bg)

        if self._flash:
            pen = QPen(QColor(ACCENT)); pen.setWidth(2)
        elif self._is_drop_target:
            pen = QPen(_ac(170)); pen.setWidth(2)
        else:
            pen = QPen(QColor(255, 255, 255, 10)); pen.setWidth(1)
        p.setPen(pen)
        p.drawRoundedRect(1, 1, r.width()-2, r.height()-2, 13, 13)
        p.setClipPath(path)

        if self.edit_mode:
            p.setPen(QColor(255, 255, 255, 89))
            p.setFont(QFont("Inter", 10))
            p.drawText(QRect(6, 5, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        p.setFont(QFont("Segoe UI Emoji", 22))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(QRect(0, 6, r.width(), int(r.height()*0.62)),
                   Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

        p.setFont(QFont("Inter", 9, QFont.Weight.Medium))
        p.setPen(QColor(255, 255, 255, 166))
        p.drawText(QRect(4, int(r.height()*0.66), r.width()-8, int(r.height()*0.28)),
                   Qt.AlignmentFlag.AlignCenter, self.cell["label"])

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
        self._tooltip_timer.stop()
        win = self.window()
        if hasattr(win, "hide_tooltip"):
            win.hide_tooltip()
        if self._drag_start_pos is None:
            return
        if (e.pos() - self._drag_start_pos).manhattanLength() < 8:
            return
        if self.edit_mode:
            if self.cell is not None:
                self.drag_start.emit(self.index)
            self._drag_start_pos = None
            return
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
        px = QPixmap(self.size())
        px.fill(Qt.GlobalColor.transparent)
        self.render(px)
        drag.setPixmap(px)
        drag.setHotSpot(hot_spot)
        drag.exec(Qt.DropAction.CopyAction)


# ══════════════════════════════════════════════════════════════════════════════
#  LiftedCell
# ══════════════════════════════════════════════════════════════════════════════
class LiftedCell(QWidget):
    def __init__(self, cell: dict, parent=None, cell_size: int = CELL_SIZE):
        super().__init__(parent)
        self.cell = cell
        sz = cell_size + 8
        self.setFixedSize(sz, sz)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r  = self.rect()
        m  = 4
        iw = r.width()  - 2*m
        ih = r.height() - 2*m
        inner = QRectF(m, m, iw, ih)
        path  = QPainterPath()
        path.addRoundedRect(inner, 14, 14)

        for i in range(3, 0, -1):
            p.setPen(QPen(_ac(30 * i), i * 3))
            p.drawRoundedRect(inner, 14, 14)

        p.fillPath(path, QColor(49, 49, 71, 220))
        p.setPen(QPen(_ac(180), 2))
        p.drawRoundedRect(inner.adjusted(1, 1, -1, -1), 13, 13)
        p.setClipPath(path)

        p.setPen(QColor(255, 255, 255, 140))
        p.setFont(QFont("Inter", 10))
        p.drawText(QRect(m+6, m+5, 20, 14), Qt.AlignmentFlag.AlignLeft, "⠿")

        er = QRect(m, m+6, iw, int(ih * 0.62))
        p.setFont(QFont("Segoe UI Emoji", 22))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(er, Qt.AlignmentFlag.AlignCenter, self.cell["emoji"])

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
        p    = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r    = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, r.width(), r.height(), 10, 10)
        p.fillPath(path, QColor(20, 20, 30, 235))
        p.setPen(QPen(QColor(255, 255, 255, 15), 1))
        p.drawRoundedRect(0, 0, r.width()-1, r.height()-1, 10, 10)
        p.setClipPath(path)

        p.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        p.setPen(QColor(255, 255, 255, 242))
        p.drawText(QRect(11, 7, r.width()-22, 18), Qt.AlignmentFlag.AlignVCenter,
                   f"{self.cell['emoji']} {self.cell['label']}")

        preview = self.cell.get("text", "").replace("\n", " ")
        p.setFont(QFont("JetBrains Mono", 9))
        p.setPen(QColor(255, 255, 255, 158))
        fm = p.fontMetrics()
        preview = fm.elidedText(preview, Qt.TextElideMode.ElideRight, r.width()-22)
        p.drawText(QRect(11, 28, r.width()-22, 16), Qt.AlignmentFlag.AlignVCenter, preview)


# ══════════════════════════════════════════════════════════════════════════════
#  SidebarItem
# ══════════════════════════════════════════════════════════════════════════════
class SidebarItem(QWidget):
    clicked    = pyqtSignal(str)
    move_up    = pyqtSignal(str)
    move_down  = pyqtSignal(str)
    edit_table = pyqtSignal(str)

    def __init__(self, table: dict, active: bool = False,
                 edit_mode: bool = False, parent=None):
        super().__init__(parent)
        self.table     = table
        self.active    = active
        self.edit_mode = edit_mode
        self.setFixedSize(76, 82 if edit_mode else 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if edit_mode:
            self._add_edit_controls()

    def _add_edit_controls(self):
        """Add ▲ ▼ ✎ buttons at the bottom in edit mode."""
        btn_style = (
            "QPushButton{font-size:10px;background:rgba(255,255,255,0.06);"
            "border:none;border-radius:4px;color:rgba(255,255,255,0.5);padding:0;}"
            "QPushButton:hover{background:rgba(255,255,255,0.15);color:white;}"
        )
        y = 66

        up = QPushButton("▲", self)
        up.setFixedSize(20, 14)
        up.move(7, y)
        up.setStyleSheet(btn_style)
        up.setCursor(Qt.CursorShape.PointingHandCursor)
        up.clicked.connect(lambda: self.move_up.emit(self.table["id"]))

        dn = QPushButton("▼", self)
        dn.setFixedSize(20, 14)
        dn.move(29, y)
        dn.setStyleSheet(btn_style)
        dn.setCursor(Qt.CursorShape.PointingHandCursor)
        dn.clicked.connect(lambda: self.move_down.emit(self.table["id"]))

        ed = QPushButton("✎", self)
        ed.setFixedSize(16, 14)
        ed.move(51, y)
        ed.setStyleSheet(btn_style)
        ed.setCursor(Qt.CursorShape.PointingHandCursor)
        ed.clicked.connect(lambda: self.edit_table.emit(self.table["id"]))

    def set_active(self, v: bool):
        self.active = v
        self.update()

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, cr = 38, 22, 19

        if self.active:
            pip = QPainterPath()
            pip.addRoundedRect(2, cy-7, 3, 14, 1.5, 1.5)
            p.fillPath(pip, QColor(ACCENT))

        p.setOpacity(1.0 if self.active else 0.55)

        circle = QPainterPath()
        circle.addEllipse(cx-cr, cy-cr, cr*2, cr*2)
        if self.active:
            p.fillPath(circle, _ac(31))
            p.setPen(QPen(_ac(102), 1))
            p.drawEllipse(cx-cr, cy-cr, cr*2, cr*2)

        p.setFont(QFont("Segoe UI Emoji", 16))
        p.setPen(Qt.GlobalColor.white)
        p.drawText(QRect(cx-cr, cy-cr, cr*2, cr*2), Qt.AlignmentFlag.AlignCenter,
                   self.table["emoji"])

        p.setFont(QFont("Inter", 8, QFont.Weight.Medium))
        p.setPen(QColor(255, 255, 255, 217 if self.active else 127))
        p.drawText(QRect(4, cy+cr+3, 68, 14), Qt.AlignmentFlag.AlignCenter,
                   self.table["name"])

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # only fire if not clicking the control buttons at the bottom
            if not self.edit_mode or e.pos().y() < 62:
                self.clicked.emit(self.table["id"])


# ══════════════════════════════════════════════════════════════════════════════
#  AddTableButton
# ══════════════════════════════════════════════════════════════════════════════
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
#  Shared modal base
# ══════════════════════════════════════════════════════════════════════════════
def _input_style(focus_border=True):
    fb = "border:1px solid rgba(124,106,247,136);" if focus_border else ""
    return (f"QLineEdit{{background:rgba(0,0,0,71);border:1px solid rgba(255,255,255,.06);"
            f"border-radius:8px;padding:0 10px;color:rgba(255,255,255,.92);font-size:12px;}}"
            f"QLineEdit:focus{{{fb}}}")


def _textarea_style():
    return (f"QTextEdit{{background:rgba(0,0,0,71);border:1px solid rgba(255,255,255,.06);"
            f"border-radius:8px;padding:6px 10px;color:rgba(255,255,255,.78);"
            f"font-family:'JetBrains Mono';font-size:10px;line-height:1.45;}}"
            f"QTextEdit:focus{{border:1px solid rgba(124,106,247,136);}}")


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:rgba(255,255,255,.4);font-size:9px;font-weight:600;"
                      "letter-spacing:.8px;background:transparent;border:none;")
    return lbl


def _modal_box(parent: QWidget, width: int = 300) -> tuple[QFrame, QVBoxLayout]:
    box = QFrame(parent)
    box.setFixedWidth(width)
    box.setStyleSheet(f"QFrame{{background:{PANEL};border:1px solid rgba(255,255,255,0.07);"
                      f"border-radius:16px;}}")
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(60); eff.setOffset(0, 20); eff.setColor(QColor(0, 0, 0, 153))
    box.setGraphicsEffect(eff)
    v = QVBoxLayout(box)
    v.setContentsMargins(16, 14, 16, 14)
    v.setSpacing(8)
    return box, v


# ══════════════════════════════════════════════════════════════════════════════
#  EditModal — edit / create a cell
# ══════════════════════════════════════════════════════════════════════════════
class EditModal(QWidget):
    saved   = pyqtSignal(dict)
    deleted = pyqtSignal()
    closed  = pyqtSignal()

    def __init__(self, cell: dict | None, mode: str, parent=None):
        super().__init__(parent)
        self.mode             = mode
        self._confirm_delete  = False
        self._del_btn         = None
        self.setGeometry(parent.rect() if parent else QRect(0, 0, 480, 580))
        self._build(cell)
        self.raise_()

    def _build(self, cell):
        box, v = _modal_box(self)

        # header
        hdr = QLabel("EDIT CELL")
        hdr.setStyleSheet("color:rgba(255,255,255,.5);font-size:11px;font-weight:600;"
                          "letter-spacing:1.2px;background:transparent;border:none;")
        v.addWidget(hdr)

        # emoji picker
        self._picker = EmojiPickerWidget(cell["emoji"] if cell else "📧")
        v.addWidget(self._picker)

        # selected emoji display
        row_em = QHBoxLayout()
        self._sel_lbl = QLabel(self._picker.get_selected())
        self._sel_lbl.setStyleSheet("font-size:22px;background:transparent;border:none;")
        row_em.addWidget(QLabel("Выбрано:"))
        row_em.addWidget(self._sel_lbl)
        row_em.addStretch()
        row_em.itemAt(0).widget().setStyleSheet(
            "color:rgba(255,255,255,.4);font-size:9px;font-weight:600;"
            "letter-spacing:.8px;background:transparent;border:none;")
        v.addLayout(row_em)
        self._picker.emoji_selected.connect(lambda e: self._sel_lbl.setText(e))

        # label
        v.addWidget(_field_label("LABEL"))
        self._lbl = QLineEdit(cell["label"] if cell else "")
        self._lbl.setFixedHeight(32)
        self._lbl.setStyleSheet(_input_style())
        v.addWidget(self._lbl)

        # content
        v.addWidget(_field_label("CONTENT"))
        self._txt = QTextEdit(cell["text"] if cell else "")
        self._txt.setFixedHeight(62)
        self._txt.setStyleSheet(_textarea_style())
        v.addWidget(self._txt)

        # buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        if self.mode == "edit":
            self._del_btn = QPushButton("Delete")
            self._del_btn.setFixedHeight(30)
            self._del_btn.setStyleSheet(
                "QPushButton{padding:0 14px;border-radius:8px;"
                "border:1px solid rgba(255,80,80,.3);background:rgba(255,80,80,.08);"
                "color:#ff7a7a;font-size:11px;font-weight:600;}"
                "QPushButton:hover{background:rgba(255,80,80,.15);}")
            self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._del_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(self._del_btn)
        btn_row.addStretch()
        save = QPushButton("Save")
        save.setFixedHeight(30)
        save.setStyleSheet(
            f"QPushButton{{padding:0 16px;border-radius:8px;border:none;"
            f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {ACCENT},stop:1 rgba(124,106,247,204));"
            f"color:white;font-size:11px;font-weight:600;}}")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)
        v.addLayout(btn_row)

        box.adjustSize()
        pw, ph = self.width(), self.height()
        box.move((pw - box.width()) // 2, max(10, (ph - box.height()) // 2))
        self._lbl.setFocus()

    def _on_save(self):
        label = self._lbl.text().strip()
        text  = self._txt.toPlainText().strip()
        if label and text:
            self.saved.emit({"emoji": self._picker.get_selected(), "label": label, "text": text})

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


# ══════════════════════════════════════════════════════════════════════════════
#  EditTableModal — edit table name / emoji
# ══════════════════════════════════════════════════════════════════════════════
class EditTableModal(QWidget):
    saved   = pyqtSignal(dict)   # {"emoji": ..., "name": ..., "cols": ...}
    deleted = pyqtSignal()
    closed  = pyqtSignal()

    def __init__(self, table: dict, can_delete: bool, parent=None):
        super().__init__(parent)
        self._confirm_delete = False
        self._del_btn        = None
        self.setGeometry(parent.rect() if parent else QRect(0, 0, 480, 580))
        self._build(table, can_delete)
        self.raise_()

    def _build(self, table, can_delete):
        box, v = _modal_box(self)

        hdr = QLabel("EDIT TABLE")
        hdr.setStyleSheet("color:rgba(255,255,255,.5);font-size:11px;font-weight:600;"
                          "letter-spacing:1.2px;background:transparent;border:none;")
        v.addWidget(hdr)

        self._picker = EmojiPickerWidget(table["emoji"])
        v.addWidget(self._picker)

        row_em = QHBoxLayout()
        self._sel_lbl = QLabel(table["emoji"])
        self._sel_lbl.setStyleSheet("font-size:22px;background:transparent;border:none;")
        lbl_sel = QLabel("Выбрано:")
        lbl_sel.setStyleSheet("color:rgba(255,255,255,.4);font-size:9px;font-weight:600;"
                              "letter-spacing:.8px;background:transparent;border:none;")
        row_em.addWidget(lbl_sel)
        row_em.addWidget(self._sel_lbl)
        row_em.addStretch()
        v.addLayout(row_em)
        self._picker.emoji_selected.connect(lambda e: self._sel_lbl.setText(e))

        v.addWidget(_field_label("НАЗВАНИЕ"))
        self._name = QLineEdit(table["name"])
        self._name.setFixedHeight(32)
        self._name.setStyleSheet(_input_style())
        v.addWidget(self._name)

        # ── Column count selector ──────────────────────────────────────────────
        v.addWidget(_field_label("СТОЛБЦЫ"))
        self._selected_cols = table.get("cols", 4)
        self._cols_btns: list[tuple[int, QPushButton]] = []
        cols_row = QHBoxLayout()
        cols_row.setSpacing(6)
        for n in (2, 3, 4, 5):
            btn = QPushButton(str(n))
            btn.setFixedSize(38, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._cols_btn_style(n == self._selected_cols))
            btn.clicked.connect(lambda _, nb=n: self._select_cols(nb))
            cols_row.addWidget(btn)
            self._cols_btns.append((n, btn))
        cols_row.addStretch()
        v.addLayout(cols_row)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        if can_delete:
            self._del_btn = QPushButton("Удалить")
            self._del_btn.setFixedHeight(30)
            self._del_btn.setStyleSheet(
                "QPushButton{padding:0 14px;border-radius:8px;"
                "border:1px solid rgba(255,80,80,.3);background:rgba(255,80,80,.08);"
                "color:#ff7a7a;font-size:11px;font-weight:600;}"
                "QPushButton:hover{background:rgba(255,80,80,.15);}")
            self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._del_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(self._del_btn)
        btn_row.addStretch()
        save = QPushButton("Сохранить")
        save.setFixedHeight(30)
        save.setStyleSheet(
            f"QPushButton{{padding:0 16px;border-radius:8px;border:none;"
            f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {ACCENT},stop:1 rgba(124,106,247,204));"
            f"color:white;font-size:11px;font-weight:600;}}")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)
        v.addLayout(btn_row)

        box.adjustSize()
        pw, ph = self.width(), self.height()
        box.move((pw - box.width()) // 2, max(10, (ph - box.height()) // 2))
        self._name.setFocus()

    @staticmethod
    def _cols_btn_style(active: bool) -> str:
        if active:
            return (f"QPushButton{{border-radius:7px;border:1px solid rgba(124,106,247,160);"
                    f"background:rgba(124,106,247,60);color:white;"
                    f"font-size:12px;font-weight:600;}}")
        return ("QPushButton{border-radius:7px;border:1px solid rgba(255,255,255,0.08);"
                "background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.6);"
                "font-size:12px;font-weight:600;}"
                "QPushButton:hover{background:rgba(255,255,255,0.12);color:white;}")

    def _select_cols(self, n: int):
        self._selected_cols = n
        for nb, btn in self._cols_btns:
            btn.setStyleSheet(self._cols_btn_style(nb == n))

    def _on_save(self):
        name = self._name.text().strip()
        if name:
            self.saved.emit({
                "emoji": self._picker.get_selected(),
                "name": name,
                "cols": self._selected_cols,
            })

    def _on_delete(self):
        if self._confirm_delete:
            self.deleted.emit()
        else:
            self._confirm_delete = True
            self._del_btn.setText("Точно?")
            QTimer.singleShot(2000, self._reset_delete)

    def _reset_delete(self):
        self._confirm_delete = False
        if self._del_btn:
            self._del_btn.setText("Удалить")

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
