"""
ui/auth.py — Clean Professional
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.base import (
    L_TEXT, L_MUTED, RED, font, get_lang, LANG_BUS,
)
from core.database import login_user, register_user, user_exists, list_users

ACCENT = '#2563eb'


class AuthPage(QWidget):
    logged_in = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = 'login'
        self.setStyleSheet('background:#fff;')
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_left(), 1)
        root.addWidget(self._make_right(), 1)

    def _make_left(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet('background:#0f172a;')
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(56, 56, 56, 56)
        lay.setSpacing(0)

        # Logo
        logo = QFrame()
        logo.setFixedSize(44, 44)
        logo.setStyleSheet(f'background:{ACCENT};border-radius:10px;')
        ll = QVBoxLayout(logo)
        ll.setContentsMargins(0,0,0,0)
        li = QLabel('IQ')
        li.setFont(font(12, True))
        li.setStyleSheet('color:#fff;background:transparent;')
        li.setAlignment(Qt.AlignCenter)
        ll.addWidget(li)

        logo_row = QHBoxLayout()
        logo_row.addWidget(logo)
        logo_row.addSpacing(12)
        appname = QLabel('Assessment\nIQ & Kepribadian')
        appname.setFont(font(13, True))
        appname.setStyleSheet('color:#f1f5f9;background:transparent;')
        logo_row.addWidget(appname)
        logo_row.addStretch()
        lay.addLayout(logo_row)

        lay.addSpacing(64)

        headline = QLabel('Kenali dirimu\nlebih dalam.')
        headline.setFont(font(30, True))
        headline.setStyleSheet('color:#f8fafc;background:transparent;line-height:1.2;')
        headline.setWordWrap(True)
        lay.addWidget(headline)

        lay.addSpacing(16)

        sub = QLabel('Tes IQ dan kepribadian berbasis sistem\npakar, didukung kecerdasan buatan.')
        sub.setFont(font(11))
        sub.setStyleSheet('color:#64748b;background:transparent;line-height:1.6;')
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addStretch()

        quote = QLabel('"Know thyself is the\nbeginning of all wisdom."')
        quote.setFont(font(10))
        quote.setStyleSheet('color:#334155;background:transparent;font-style:italic;')
        quote.setWordWrap(True)
        lay.addWidget(quote)
        lay.addSpacing(8)

        ver = QLabel('v5.0 · Expert System + AI')
        ver.setFont(font(8))
        ver.setStyleSheet('color:#1e293b;background:transparent;')
        lay.addWidget(ver)

        return panel

    def _make_right(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet('background:#fff;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(64, 0, 64, 0)
        lay.setAlignment(Qt.AlignVCenter)
        lay.setSpacing(0)

        self._form_title = QLabel('Masuk')
        self._form_title.setFont(font(26, True))
        self._form_title.setStyleSheet('color:#0f172a;')
        lay.addWidget(self._form_title)
        lay.addSpacing(6)

        self._form_sub = QLabel('Pilih nama dan masukkan PIN untuk melanjutkan.')
        self._form_sub.setFont(font(10))
        self._form_sub.setStyleSheet('color:#94a3b8;')
        self._form_sub.setWordWrap(True)
        lay.addWidget(self._form_sub)
        lay.addSpacing(28)

        def field_label(text):
            l = QLabel(text)
            l.setFont(font(10, True))
            l.setStyleSheet('color:#374151;')
            return l

        def text_input(placeholder='', echo=False):
            inp = QLineEdit()
            if echo: inp.setEchoMode(QLineEdit.Password)
            inp.setFont(font(11))
            inp.setFixedHeight(42)
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(
                'QLineEdit{background:#fff;color:#0f172a;'
                'border:1.5px solid #e2e8f0;border-radius:8px;padding:0 14px;}'
                'QLineEdit:focus{border-color:#2563eb;outline:none;}'
            )
            return inp

        lay.addWidget(field_label('Nama'))
        lay.addSpacing(6)
        self._name_combo = QComboBox()
        self._name_combo.setEditable(True)
        self._name_combo.setFont(font(11))
        self._name_combo.setFixedHeight(42)
        self._name_combo.setStyleSheet(
            'QComboBox{background:#fff;color:#0f172a;'
            'border:1.5px solid #e2e8f0;border-radius:8px;padding:0 12px;}'
            'QComboBox:focus{border-color:#2563eb;}'
            'QComboBox::drop-down{border:none;width:24px;}'
            'QComboBox QAbstractItemView{background:#fff;border:1px solid #e2e8f0;'
            'selection-background-color:#eff6ff;}'
        )
        self._refresh_names()
        lay.addWidget(self._name_combo)
        lay.addSpacing(16)

        lay.addWidget(field_label('PIN (4 digit)'))
        lay.addSpacing(6)
        self._pin_input = text_input('••••', echo=True)
        self._pin_input.setMaxLength(4)
        self._pin_input.returnPressed.connect(self._submit)
        lay.addWidget(self._pin_input)

        self._confirm_wrap = QWidget()
        self._confirm_wrap.setVisible(False)
        cw_lay = QVBoxLayout(self._confirm_wrap)
        cw_lay.setContentsMargins(0,0,0,0)
        cw_lay.setSpacing(6)
        cw_lay.addSpacing(16)
        cw_lay.addWidget(field_label('Konfirmasi PIN'))
        self._confirm_input = text_input('••••', echo=True)
        self._confirm_input.setMaxLength(4)
        self._confirm_input.returnPressed.connect(self._submit)
        cw_lay.addWidget(self._confirm_input)
        lay.addWidget(self._confirm_wrap)

        lay.addSpacing(8)
        self._err_lbl = QLabel('')
        self._err_lbl.setFont(font(9))
        self._err_lbl.setStyleSheet('color:#ef4444;')
        self._err_lbl.setWordWrap(True)
        lay.addWidget(self._err_lbl)
        lay.addSpacing(20)

        self._submit_btn = QPushButton('Masuk')
        self._submit_btn.setFont(font(12, True))
        self._submit_btn.setFixedHeight(44)
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.setStyleSheet(
            f'QPushButton{{background:{ACCENT};color:#fff;border:none;border-radius:8px;}}'
            f'QPushButton:hover{{background:#1d4ed8;}}'
        )
        self._submit_btn.clicked.connect(self._submit)
        lay.addWidget(self._submit_btn)

        lay.addSpacing(12)

        self._toggle_btn = QPushButton('Belum punya akun? Daftar')
        self._toggle_btn.setFont(font(10))
        self._toggle_btn.setFixedHeight(36)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setStyleSheet(
            f'QPushButton{{background:transparent;color:{ACCENT};border:none;}}'
            f'QPushButton:hover{{color:#1d4ed8;}}'
        )
        self._toggle_btn.clicked.connect(self._toggle_mode)
        lay.addWidget(self._toggle_btn, 0, Qt.AlignCenter)

        return w

    def _refresh_names(self):
        self._name_combo.clear()
        for u in list_users():
            self._name_combo.addItem(u['name'])

    def _toggle_mode(self):
        self._mode = 'register' if self._mode == 'login' else 'login'
        is_reg = self._mode == 'register'
        self._form_title.setText('Daftar' if is_reg else 'Masuk')
        self._form_sub.setText(
            'Buat akun baru dengan nama dan PIN 4 digit.' if is_reg
            else 'Pilih nama dan masukkan PIN untuk melanjutkan.'
        )
        self._confirm_wrap.setVisible(is_reg)
        self._submit_btn.setText('Daftar' if is_reg else 'Masuk')
        self._toggle_btn.setText(
            'Sudah punya akun? Masuk' if is_reg
            else 'Belum punya akun? Daftar'
        )
        self._err_lbl.setText('')
        self._pin_input.clear()
        self._confirm_input.clear()

    def _submit(self):
        name = self._name_combo.currentText().strip()
        pin  = self._pin_input.text().strip()

        if not name:
            self._err_lbl.setText('Nama tidak boleh kosong.')
            return
        if len(pin) != 4 or not pin.isdigit():
            self._err_lbl.setText('PIN harus 4 digit angka.')
            return

        if self._mode == 'login':
            user = login_user(name, pin)
            if user:
                self._err_lbl.setText('')
                self.logged_in.emit(user)
            else:
                self._err_lbl.setText('Nama atau PIN salah.')
        else:
            confirm = self._confirm_input.text().strip()
            if pin != confirm:
                self._err_lbl.setText('Konfirmasi PIN tidak cocok.')
                return
            if user_exists(name):
                self._err_lbl.setText(f'Nama "{name}" sudah terdaftar.')
                return
            user = register_user(name, pin)
            if user:
                self._err_lbl.setText('')
                self.logged_in.emit(user)
            else:
                self._err_lbl.setText('Gagal mendaftar. Coba lagi.')

    def refresh(self):
        self._refresh_names()
        self._pin_input.clear()
        self._err_lbl.setText('')
        self._mode = 'login'
        self._form_title.setText('Masuk')
        self._submit_btn.setText('Masuk')
        self._toggle_btn.setText('Belum punya akun? Daftar')
        self._confirm_wrap.setVisible(False)