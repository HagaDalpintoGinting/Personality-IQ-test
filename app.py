"""
app.py — Entry point v5.0
────────────────────────────────────────────────────────────
Expert System + AI Assessment App
Jalankan: python app.py
────────────────────────────────────────────────────────────
"""

import sys
import os

# ── Pastikan folder BigFive/ masuk sys.path ──────────────────
# Ini yang membuat 'import ui.xxx' dan 'import core.xxx' bisa bekerja
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Pastikan working directory = folder BigFive/
os.chdir(BASE_DIR)

# ── HiDPI HARUS sebelum QApplication ─────────────────────────
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from PyQt5.QtGui import QFont


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Assessment IQ & Kepribadian')
    app.setOrganizationName('Hagz')

    app.setFont(QFont('Segoe UI', 11))

    # Import SETELAH QApplication dibuat
    from ui.home import MainWindow
    win = MainWindow()
    win.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()