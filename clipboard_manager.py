"""
Clipboard Manager — Indigo Dusk
Requirements: pip install PyQt6

Run: python clipboard_manager.py
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui     import QFont
from cm_window       import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clipboard Manager")
    app.setFont(QFont("Inter", 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
