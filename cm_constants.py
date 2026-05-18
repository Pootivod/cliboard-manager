"""
Clipboard Manager — constants, defaults, state I/O
"""
import copy
import json
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
SAVE_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_manager_v2.json")

# ── Window dimensions ──────────────────────────────────────────────────────────
WIN_W       = 480
WIN_H       = 580
SIDEBAR_W   = 76
TOOLBAR_H   = 48
STATUSBAR_H = 28

# ── Grid geometry (all derived, never hard-coded elsewhere) ────────────────────
GRID_W      = WIN_W - SIDEBAR_W          # 404 px
GRID_PAD_H  = 12                         # left / right padding
GRID_PAD_T  = 14
GRID_PAD_B  = 10
GRID_GAP    = 9
GRID_COLS   = 4
GRID_SLOTS  = 12
# exact square cell size that fills the grid evenly
CELL_SIZE   = (GRID_W - 2*GRID_PAD_H - (GRID_COLS-1)*GRID_GAP) // GRID_COLS  # 88 px

# ── Design tokens (Indigo Dusk) ────────────────────────────────────────────────
BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
CARD    = "#313147"
ACCENT  = "#7c6af7"
SUCCESS = "#5fbf85"
DANGER  = "#ff7a7a"

# ── Emoji picker ───────────────────────────────────────────────────────────────
PICKER_EMOJI = ["📧","🏢","📞","📍","🔗","🔑","💳","📝","⚡","🌐","📁","⭐"]

# ── Default data ───────────────────────────────────────────────────────────────
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


def load_state():
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
        tables   = data.get("tables", copy.deepcopy(DEFAULT_TABLES))
        active   = data.get("activeTableId", tables[0]["id"])
        return tables, active
    except Exception:
        tables = copy.deepcopy(DEFAULT_TABLES)
        return tables, tables[0]["id"]


def save_state(tables, active_id):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"tables": tables, "activeTableId": active_id}, f, ensure_ascii=False)
    except Exception:
        pass
