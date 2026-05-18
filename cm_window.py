"""
Clipboard Manager — MainWindow
"""
import uuid

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore    import Qt, QTimer, QPoint
from PyQt6.QtGui     import QColor, QPainter, QPainterPath, QFont, QCursor

from cm_constants import (
    WIN_W, WIN_H, TOOLBAR_H, STATUSBAR_H, SIDEBAR_W,
    GRID_ROWS, CELL_SIZE, GRID_GAP, ACCENT, BG, SUCCESS,
    grid_metrics, load_state, save_state,
)

_GRID_HOST_H = WIN_H - TOOLBAR_H - STATUSBAR_H
from cm_widgets import (
    CellWidget, LiftedCell, TooltipWidget,
    SidebarItem, AddTableButton, EditModal, EditTableModal,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipboard Manager")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._edit_mode        = False
        self._drag_idx         = None
        self._drag_over        = None
        self._lifted           = None
        self._tooltip          = None
        self._modal            = None
        self._toolbar_drag_pos = None
        self._cell_widgets:  list[CellWidget] = []
        self._ghost_widgets: list[CellWidget] = []
        # updated by _refresh_grid to reflect active table's column count
        self._cols      = 4
        self._cell_size = 88
        self._cell_x: list[int] = []
        self._cell_y: list[int] = []

        self._tables, self._active_id = load_state()

        self._build_ui()
        self._refresh()

    # ── active table ───────────────────────────────────────────────────────────
    def _active(self):
        for t in self._tables:
            if t["id"] == self._active_id:
                return t
        return self._tables[0]

    # ── one-time UI skeleton ───────────────────────────────────────────────────
    def _build_ui(self):
        self._canvas = QWidget(self)
        self._canvas.setGeometry(0, 0, WIN_W, WIN_H)
        self._canvas.setStyleSheet(f"background:{BG};border-radius:16px;")

        root = QVBoxLayout(self._canvas)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._mk_toolbar())

        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        # grid area — plain QWidget, cells positioned manually (no layout)
        # initial size uses 4-col default; _apply_cols() resizes it dynamically
        _default_grid_w = 2*12 + 4*CELL_SIZE + 3*9   # matches WIN_W default
        self._grid_host = QWidget()
        self._grid_host.setFixedSize(_default_grid_w, WIN_H - TOOLBAR_H - STATUSBAR_H)
        self._grid_host.setStyleSheet("background:transparent;")
        bl.addWidget(self._grid_host)

        # sidebar — uses a VBoxLayout (vertical list only, no layout conflict)
        self._sidebar_host = QWidget()
        self._sidebar_host.setFixedWidth(SIDEBAR_W)
        self._sidebar_host.setStyleSheet(
            "background:transparent;border-left:1px solid rgba(255,255,255,9);"
        )
        self._sidebar_vbox = QVBoxLayout(self._sidebar_host)
        self._sidebar_vbox.setContentsMargins(0, 14, 0, 14)
        self._sidebar_vbox.setSpacing(2)
        self._sidebar_vbox.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        bl.addWidget(self._sidebar_host)

        root.addWidget(body, 1)
        root.addWidget(self._mk_statusbar())

    def _mk_toolbar(self):
        bar = QWidget()
        bar.setFixedHeight(TOOLBAR_H)
        bar.setObjectName("toolbar")
        bar.setStyleSheet(
            "QWidget#toolbar{background:rgba(255,255,255,5);"
            "border-bottom:1px solid rgba(255,255,255,13);}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(9)

        icon = QLabel()
        icon.setFixedSize(22, 22)
        icon.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ACCENT},stop:1 rgba(124,106,247,170));"
            "border-radius:7px;"
        )
        h.addWidget(icon)

        title = QLabel("Clipboard")
        # background:transparent prevents the label from covering the toolbar gradient
        title.setStyleSheet(
            "background:transparent;"
            "color:rgba(255,255,255,235);font-size:13px;font-weight:600;letter-spacing:.1px;"
        )
        h.addWidget(title)

        self._suffix = QLabel()
        self._suffix.setStyleSheet("background:transparent;color:rgba(255,255,255,102);font-size:11px;")
        h.addWidget(self._suffix)
        h.addStretch()

        self._pencil = QPushButton("✎")
        self._pencil.setFixedSize(28, 28)
        self._pencil.setFont(QFont("Inter", 13))
        self._pencil.setStyleSheet(
            "background:transparent;border:none;border-radius:8px;color:rgba(255,255,255,153);"
        )
        self._pencil.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pencil.clicked.connect(self._toggle_edit)
        h.addWidget(self._pencil)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Inter", 11))
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;"
            "color:rgba(255,255,255,102);}"
            "QPushButton:hover{background:rgba(255,100,100,40);color:#ff7a7a;}"
        )
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        h.addWidget(close_btn)

        bar.mousePressEvent   = self._tb_press
        bar.mouseMoveEvent    = self._tb_move
        bar.mouseReleaseEvent = self._tb_release
        self._toolbar_bar = bar
        return bar

    def _mk_statusbar(self):
        bar = QWidget()
        bar.setFixedHeight(STATUSBAR_H)
        bar.setStyleSheet(
            "background:rgba(255,255,255,5);border-top:1px solid rgba(255,255,255,10);"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        self._status_lbl = QLabel()
        self._status_lbl.setStyleSheet(
            f"color:{SUCCESS};font-size:10px;font-weight:500;letter-spacing:.3px;"
        )
        hint = QLabel("Ctrl+V")
        hint.setStyleSheet(
            "color:rgba(255,255,255,.32);font-family:'JetBrains Mono';font-size:10px;"
        )
        h.addWidget(self._status_lbl)
        h.addStretch()
        h.addWidget(hint)
        return bar

    # ── refresh (called on every state change) ─────────────────────────────────
    def _refresh(self):
        self._refresh_toolbar()
        self._refresh_grid()
        self._refresh_sidebar()
        self._refresh_status()

    def _refresh_toolbar(self):
        self._suffix.setText(f"· {self._active()['name']}")
        if self._edit_mode:
            # rgba() instead of #RRGGBBAA — Qt QSS does not support 8-digit hex alpha
            self._toolbar_bar.setStyleSheet(
                "QWidget#toolbar{"
                "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 rgba(124,106,247,45),stop:1 rgba(124,106,247,15));"
                "border-bottom:1px solid rgba(124,106,247,90);}"
            )
            self._pencil.setStyleSheet(
                f"background:rgba(124,106,247,60);border:none;"
                f"border-radius:8px;color:{ACCENT};"
            )
        else:
            self._toolbar_bar.setStyleSheet(
                "QWidget#toolbar{background:rgba(255,255,255,5);"
                "border-bottom:1px solid rgba(255,255,255,13);}"
            )
            self._pencil.setStyleSheet(
                "background:transparent;border:none;border-radius:8px;"
                "color:rgba(255,255,255,153);"
            )

    def _apply_cols(self, cols: int):
        """Resize window/grid to fit col count; update cached metrics."""
        grid_w, win_w, cell_x, cell_y = grid_metrics(cols)
        self._cols      = cols
        self._cell_size = CELL_SIZE
        self._cell_x    = cell_x
        self._cell_y    = cell_y
        if win_w != self.width():
            self.setFixedSize(win_w, WIN_H)
            self._canvas.setGeometry(0, 0, win_w, WIN_H)
            self._grid_host.setFixedWidth(grid_w)

    def _refresh_grid(self):
        table = self._active()
        self._apply_cols(table.get("cols", 4))

        for w in self._cell_widgets + self._ghost_widgets:
            w.setParent(None)
        self._cell_widgets  = []
        self._ghost_widgets = []

        cells = table["cells"]
        for i, cell in enumerate(cells):
            row, col = divmod(i, self._cols)
            x = self._cell_x[col]
            y = self._cell_y[0] + row * (CELL_SIZE + GRID_GAP)
            w = CellWidget(i, cell, self._edit_mode, self._grid_host,
                           cell_size=CELL_SIZE)
            w.move(x, y)
            w.show()
            w.clicked.connect(self._cell_clicked)
            w.drag_start.connect(self._drag_start)
            self._cell_widgets.append(w)

        # Ghost row: in edit mode, if any cell in the last row is filled,
        # show a dashed-plus row below to allow adding more cells.
        if self._edit_mode:
            actual_rows   = len(cells) // self._cols
            last_row_start = (actual_rows - 1) * self._cols
            if any(cells[last_row_start:]):
                ghost_y = self._cell_y[0] + actual_rows * (CELL_SIZE + GRID_GAP)
                if ghost_y + CELL_SIZE <= _GRID_HOST_H:
                    ghost_base = len(cells)
                    for col in range(self._cols):
                        ghost_idx = ghost_base + col
                        w = CellWidget(ghost_idx, None, True, self._grid_host,
                                       cell_size=CELL_SIZE)
                        w.move(self._cell_x[col], ghost_y)
                        w.show()
                        w.clicked.connect(self._expand_clicked)
                        self._ghost_widgets.append(w)

    def _refresh_sidebar(self):
        lo = self._sidebar_vbox
        while lo.count():
            item = lo.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for t in self._tables:
            si = SidebarItem(t, t["id"] == self._active_id, self._edit_mode)
            si.clicked.connect(self._switch_table)
            si.move_up.connect(self._table_move_up)
            si.move_down.connect(self._table_move_down)
            si.edit_table.connect(self._open_table_modal)
            lo.addWidget(si)

        lo.addStretch()

        if self._edit_mode:
            add = AddTableButton()
            add.clicked.connect(self._add_table)
            lo.addWidget(add)

    def _refresh_status(self, msg=None):
        cells = self._active()["cells"]
        if msg:
            self._status_lbl.setText(msg)
            self._status_lbl.setStyleSheet(
                f"color:{ACCENT};font-size:10px;font-weight:500;letter-spacing:.3px;"
            )
            return
        if self._edit_mode:
            self._status_lbl.setText("● EDIT MODE")
            self._status_lbl.setStyleSheet(
                f"color:{ACCENT};font-size:10px;font-weight:500;letter-spacing:.3px;"
            )
        else:
            n  = sum(1 for c in cells if c)
            fr = sum(1 for c in cells if not c)
            self._status_lbl.setText(f"● {n} ITEMS · {fr} FREE")
            self._status_lbl.setStyleSheet(
                f"color:{SUCCESS};font-size:10px;font-weight:500;letter-spacing:.3px;"
            )

    # ── actions ────────────────────────────────────────────────────────────────
    def _toggle_edit(self):
        self._edit_mode = not self._edit_mode
        self.hide_tooltip()
        self._close_modal()
        self._refresh()

    def _switch_table(self, tid):
        self._active_id = tid
        self.hide_tooltip()
        self._close_modal()
        self._refresh()
        save_state(self._tables, self._active_id)

    def _add_table(self):
        tid = str(uuid.uuid4())[:8]
        self._tables.append({
            "id": tid, "emoji": "📂", "name": "New", "cols": 4, "cells": [None]*12
        })
        self._active_id = tid
        self._refresh()
        save_state(self._tables, self._active_id)

    def _cell_clicked(self, idx):
        cell = self._active()["cells"][idx]
        if self._edit_mode:
            self._open_modal(idx, cell, "edit" if cell else "new")
        elif cell:
            self._copy(idx, cell)

    def _copy(self, idx, cell):
        QApplication.clipboard().setText(cell["text"])
        if idx < len(self._cell_widgets):
            self._cell_widgets[idx].flash_copy()
        self._refresh_status("● COPIED")
        QTimer.singleShot(1500, self._refresh_status)

    def _open_modal(self, idx, cell, mode):
        self._close_modal()
        m = EditModal(cell, mode, self._canvas)
        m.setGeometry(0, 0, self._canvas.width(), self._canvas.height())
        m.saved.connect(lambda c, i=idx: self._modal_save(i, c))
        m.deleted.connect(lambda i=idx: self._modal_delete(i))
        m.closed.connect(self._close_modal)
        m.show()
        self._modal = m

    def _close_modal(self):
        if self._modal:
            self._modal.hide()
            self._modal.deleteLater()
            self._modal = None

    def _modal_save(self, idx, cell):
        self._active()["cells"][idx] = cell
        self._close_modal()
        self._refresh()
        save_state(self._tables, self._active_id)

    def _modal_delete(self, idx):
        self._active()["cells"][idx] = None
        self._close_modal()
        self._refresh()
        save_state(self._tables, self._active_id)

    def _expand_clicked(self, ghost_idx):
        """Extend the cells array by one row and open a new-cell modal."""
        cells = self._active()["cells"]
        cells.extend([None] * self._cols)
        save_state(self._tables, self._active_id)
        self._refresh_grid()
        self._open_modal(ghost_idx, None, "new")

    # ── table edit / reorder ───────────────────────────────────────────────────
    def _table_move_up(self, tid):
        idx = next((i for i, t in enumerate(self._tables) if t["id"] == tid), -1)
        if idx > 0:
            self._tables[idx-1], self._tables[idx] = self._tables[idx], self._tables[idx-1]
            self._refresh()
            save_state(self._tables, self._active_id)

    def _table_move_down(self, tid):
        idx = next((i for i, t in enumerate(self._tables) if t["id"] == tid), -1)
        if idx >= 0 and idx < len(self._tables) - 1:
            self._tables[idx], self._tables[idx+1] = self._tables[idx+1], self._tables[idx]
            self._refresh()
            save_state(self._tables, self._active_id)

    def _open_table_modal(self, tid):
        table = next((t for t in self._tables if t["id"] == tid), None)
        if not table:
            return
        self._close_modal()
        can_delete = len(self._tables) > 1
        m = EditTableModal(table, can_delete, self._canvas)
        m.setGeometry(0, 0, self._canvas.width(), self._canvas.height())
        m.saved.connect(lambda d, t=table: self._table_save(t["id"], d))
        m.deleted.connect(lambda t=table: self._table_delete(t["id"]))
        m.closed.connect(self._close_modal)
        m.show()
        self._modal = m

    def _table_save(self, tid, data):
        for t in self._tables:
            if t["id"] == tid:
                t["emoji"] = data["emoji"]
                t["name"]  = data["name"]
                new_cols   = data.get("cols", t.get("cols", 4))
                if new_cols != t.get("cols", 4):
                    new_slots = new_cols * GRID_ROWS
                    old_cells = t["cells"]
                    # resize: keep existing cells, pad or trim
                    t["cells"] = (old_cells + [None] * new_slots)[:new_slots]
                t["cols"] = new_cols
                break
        self._close_modal()
        self._refresh()
        save_state(self._tables, self._active_id)

    def _table_delete(self, tid):
        self._tables = [t for t in self._tables if t["id"] != tid]
        if self._active_id == tid:
            self._active_id = self._tables[0]["id"]
        self._close_modal()
        self._refresh()
        save_state(self._tables, self._active_id)

    # ── internal drag-to-reorder (edit mode) ───────────────────────────────────
    def _drag_start(self, from_idx):
        cell = self._active()["cells"][from_idx]
        if cell is None:
            return
        self._drag_idx  = from_idx
        self._drag_over = None

        if from_idx < len(self._cell_widgets):
            self._cell_widgets[from_idx].set_placeholder(True)

        if self._lifted:
            self._lifted.hide()
            self._lifted.deleteLater()
        self._lifted = LiftedCell(cell, self._canvas)
        cp   = self._canvas.mapFromGlobal(QCursor.pos())
        half = self._lifted.width() // 2
        self._lifted.move(cp.x() - half, cp.y() - half)
        self._lifted.show()
        self._lifted.raise_()

        # Grab all mouse events — prevents child CellWidget from keeping
        # the implicit grab after mousePress, which would block MainWindow
        # from receiving mouseMoveEvent during the drag.
        self.grabMouse()

    def mouseMoveEvent(self, e):
        if self._drag_idx is None:
            return
        pos  = e.pos()
        half = self._lifted.width() // 2 if self._lifted else 46
        if self._lifted:
            self._lifted.move(pos.x() - half, pos.y() - half)

        # Detect drop target by mapping cursor into grid_host coordinates
        gp       = self._grid_host.mapFrom(self, pos)
        new_over = None
        for i, w in enumerate(self._cell_widgets):
            if i == self._drag_idx:
                continue
            row_i = i // self._cols
            local = QPoint(gp.x() - self._cell_x[i % self._cols],
                           gp.y() - (self._cell_y[0] + row_i * (CELL_SIZE + GRID_GAP)))
            if 0 <= local.x() < self._cell_size and 0 <= local.y() < self._cell_size:
                new_over = i
                break

        if new_over != self._drag_over:
            if self._drag_over is not None and self._drag_over < len(self._cell_widgets):
                self._cell_widgets[self._drag_over].set_drop_target(False)
            self._drag_over = new_over
            if new_over is not None and new_over < len(self._cell_widgets):
                self._cell_widgets[new_over].set_drop_target(True)

    def mouseReleaseEvent(self, e):
        if self._drag_idx is None:
            return
        self.releaseMouse()

        if self._drag_over is not None:
            cells = self._active()["cells"]
            cells[self._drag_idx], cells[self._drag_over] = (
                cells[self._drag_over], cells[self._drag_idx]
            )
            save_state(self._tables, self._active_id)

        if self._lifted:
            self._lifted.hide()
            self._lifted.deleteLater()
            self._lifted = None

        self._drag_idx  = None
        self._drag_over = None
        self._refresh()

    # ── tooltip ────────────────────────────────────────────────────────────────
    def show_tooltip(self, idx, cell_widget):
        self.hide_tooltip()
        cell = self._active()["cells"][idx]
        if not cell:
            return
        t   = TooltipWidget(cell, self._canvas)
        pos = cell_widget.mapTo(self._canvas, QPoint(cell_widget.width() // 2, cell_widget.height() + 10))
        x   = min(max(pos.x(), 8), self.width() - t.width() - 8)
        y   = min(pos.y(), self.height() - t.height() - 8)
        t.move(x, y)
        t.raise_()
        t.show()
        self._tooltip = t

    def hide_tooltip(self):
        if self._tooltip:
            self._tooltip.setParent(None)
            self._tooltip = None

    # ── toolbar drag-to-move window ────────────────────────────────────────────
    def _tb_press(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._toolbar_drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _tb_move(self, e):
        if self._toolbar_drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._toolbar_drag_pos)

    def _tb_release(self, _):
        self._toolbar_drag_pos = None

    # ── window background ──────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.fillPath(path, QColor(BG))

    # ── keyboard shortcuts ─────────────────────────────────────────────────────
    def keyPressEvent(self, e):
        ctrl = Qt.KeyboardModifier.ControlModifier
        if e.modifiers() & ctrl and e.key() == Qt.Key.Key_E:
            self._toggle_edit()
        elif e.key() == Qt.Key.Key_Escape:
            self._close_modal()
        elif e.modifiers() & ctrl:
            for i, t in enumerate(self._tables):
                if e.key() == Qt.Key.Key_1 + i:
                    self._switch_table(t["id"])
                    break
        else:
            super().keyPressEvent(e)
