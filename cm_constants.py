"""
Clipboard Manager — constants, defaults, state I/O
"""
import copy
import json
import os
import sys

# ── Data directory — AppData on Windows, ~/.config elsewhere ──────────────────
def _data_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    path = os.path.join(base, "ClipboardManager")
    os.makedirs(path, exist_ok=True)
    return path

DATA_DIR  = _data_dir()
SAVE_FILE = os.path.join(DATA_DIR, "state.json")

# ── Window dimensions ──────────────────────────────────────────────────────────
WIN_W       = 480
WIN_H       = 580
SIDEBAR_W   = 76
TOOLBAR_H   = 48
STATUSBAR_H = 28

# ── Grid geometry (all derived, never hard-coded elsewhere) ────────────────────
GRID_W      = WIN_W - SIDEBAR_W          # 404 px
GRID_PAD_H  = 10                         # left / right padding
GRID_PAD_T  = 10                         # top padding (= GRID_PAD_H for uniform spacing)
GRID_PAD_B  = 10
GRID_GAP    = 9
GRID_ROWS   = 3
GRID_COLS   = 4                          # default; each table stores its own cols
GRID_SLOTS  = 12                         # default (GRID_COLS * GRID_ROWS)
# exact square cell size that fills the grid evenly
CELL_SIZE   = (GRID_W - 2*GRID_PAD_H - (GRID_COLS-1)*GRID_GAP) // GRID_COLS  # 88 px


def grid_metrics(cols: int, cell_size: int = CELL_SIZE) -> tuple:
    """Return (grid_w, win_w, cell_x_list, cell_y_list).
    Window width grows/shrinks with column count and cell size."""
    grid_w = 2*GRID_PAD_H + cols*cell_size + (cols - 1)*GRID_GAP
    win_w  = SIDEBAR_W + grid_w
    cell_x = [GRID_PAD_H + c * (cell_size + GRID_GAP) for c in range(cols)]
    cell_y = [GRID_PAD_T + r * (cell_size + GRID_GAP) for r in range(GRID_ROWS)]
    return grid_w, win_w, cell_x, cell_y

# ── Design tokens (Indigo Dusk) ────────────────────────────────────────────────
BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
CARD    = "#313147"
ACCENT  = "#7c6af7"
SUCCESS = "#5fbf85"
DANGER  = "#ff7a7a"

# ── Emoji picker ───────────────────────────────────────────────────────────────
PICKER_EMOJI = ["📧","🏢","📞","📍","🔗","🔑","💳","📝","⚡","🌐","📁","⭐"]

# ── First-launch default — one table, one example cell ────────────────────────
DEFAULT_TABLES = [
    {
        "id": "main", "emoji": "📋", "name": "Главная", "cols": 4, "cell_size": 88,
        "cells": [
            {
                "emoji": "📖",
                "label": "Пример",
                "text": (
                    "Кликни — скопирует текст.\n"
                    "Перетащи в поле ввода — вставит текст.\n"
                    "✎ (карандаш) — режим редактирования:\n"
                    "  + добавить клетку\n"
                    "  перетащить — переставить\n"
                    "Ctrl+E — вкл/выкл редактирование."
                ),
            },
            None, None, None,
            None, None, None, None,
            None, None, None, None,
        ],
    },
]


def load_state():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        tables = data.get("tables") or copy.deepcopy(DEFAULT_TABLES)
        active = data.get("activeTableId") or tables[0]["id"]
        return tables, active
    except FileNotFoundError:
        # First launch — return defaults, do NOT save yet (save on first change)
        tables = copy.deepcopy(DEFAULT_TABLES)
        return tables, tables[0]["id"]
    except Exception:
        tables = copy.deepcopy(DEFAULT_TABLES)
        return tables, tables[0]["id"]


def save_state(tables, active_id):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"tables": tables, "activeTableId": active_id}, f,
                      ensure_ascii=False, indent=2)
    except Exception:
        pass
