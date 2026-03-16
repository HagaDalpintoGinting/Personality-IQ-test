"""
ui/home.py — Clean Professional
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QStackedWidget, QSizePolicy, QDialog,
    QLineEdit, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.base import (
    D_BG, D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, PURPLE, ORANGE,
    font, get_lang, set_lang, LANG_BUS, init_lang_bus,
    LangToggle, TRAIT_COLORS,
)
from core.database import init_db, get_sessions, get_scores
from core.ai_explainer import set_api_key, get_api_key

ACCENT = '#2563eb'


class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Gemini API Key')
        self.setFixedWidth(420)
        self.setStyleSheet('background:#fff;')
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        title = QLabel('Gemini API Key')
        title.setFont(font(13, True))
        title.setStyleSheet('color:#0f172a;')
        lay.addWidget(title)

        desc = QLabel('Diperlukan untuk fitur interpretasi AI.\nDapatkan gratis di aistudio.google.com')
        desc.setFont(font(10))
        desc.setStyleSheet('color:#94a3b8;')
        desc.setWordWrap(True)
        lay.addWidget(desc)

        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.Password)
        self._key_input.setFont(font(11))
        self._key_input.setFixedHeight(40)
        self._key_input.setPlaceholderText('AIza...')
        self._key_input.setStyleSheet(
            'QLineEdit{background:#fff;color:#0f172a;'
            'border:1.5px solid #e2e8f0;border-radius:8px;padding:0 12px;}'
            'QLineEdit:focus{border-color:#2563eb;}'
        )
        current = get_api_key()
        if current:
            self._key_input.setText(current)
        lay.addWidget(self._key_input)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _save(self):
        set_api_key(self._key_input.text())
        self.accept()


class HomePage(QWidget):
    start_iq     = pyqtSignal()
    start_bf     = pyqtSignal()
    open_history = pyqtSignal()
    logout       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user = None
        self.setStyleSheet('background:#f8fafc;')
        self._build()
        if LANG_BUS:
            LANG_BUS.changed.connect(self._on_lang)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_sidebar())
        root.addWidget(self._make_content(), 1)

    def _make_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet('background:#0f172a;border-right:1px solid #1e293b;')
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(20, 24, 20, 20)
        lay.setSpacing(0)

        # Logo
        logo = QFrame()
        logo.setFixedSize(36, 36)
        logo.setStyleSheet(f'background:{ACCENT};border-radius:8px;')
        ll = QVBoxLayout(logo)
        ll.setContentsMargins(0,0,0,0)
        li = QLabel('IQ')
        li.setFont(font(10, True))
        li.setStyleSheet('color:#fff;background:transparent;')
        li.setAlignment(Qt.AlignCenter)
        ll.addWidget(li)

        logo_row = QHBoxLayout()
        logo_row.addWidget(logo)
        logo_row.addSpacing(10)
        app_lbl = QLabel('Assessment')
        app_lbl.setFont(font(11, True))
        app_lbl.setStyleSheet('color:#f1f5f9;background:transparent;')
        logo_row.addWidget(app_lbl)
        logo_row.addStretch()
        lay.addLayout(logo_row)

        lay.addSpacing(28)

        # Divider
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet('background:#1e293b;border:none;')
        lay.addWidget(div1)
        lay.addSpacing(16)

        # User
        self._user_lbl = QLabel('')
        self._user_lbl.setFont(font(11, True))
        self._user_lbl.setStyleSheet('color:#f1f5f9;background:transparent;')
        self._user_lbl.setWordWrap(True)
        lay.addWidget(self._user_lbl)

        self._stats_lbl = QLabel('')
        self._stats_lbl.setFont(font(9))
        self._stats_lbl.setStyleSheet('color:#475569;background:transparent;')
        lay.addWidget(self._stats_lbl)

        lay.addSpacing(16)
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet('background:#1e293b;border:none;')
        lay.addWidget(div2)

        lay.addStretch()

        lay.addWidget(LangToggle(), 0, Qt.AlignLeft)
        lay.addSpacing(8)

        settings_btn = QPushButton('API Key')
        settings_btn.setFont(font(9))
        settings_btn.setFixedHeight(32)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(
            'QPushButton{background:transparent;color:#475569;border:none;text-align:left;}'
            'QPushButton:hover{color:#94a3b8;}'
        )
        settings_btn.clicked.connect(lambda: APIKeyDialog(self).exec_())
        lay.addWidget(settings_btn)

        logout_btn = QPushButton('Keluar')
        logout_btn.setFont(font(9))
        logout_btn.setFixedHeight(32)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(
            'QPushButton{background:transparent;color:#ef4444;border:none;text-align:left;}'
            'QPushButton:hover{color:#f87171;}'
        )
        logout_btn.clicked.connect(self.logout.emit)
        lay.addWidget(logout_btn)

        return sb

    def _make_content(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet('background:#f8fafc;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet('background:#fff;border-bottom:1px solid #e2e8f0;')
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(28, 0, 28, 0)

        self._greeting = QLabel('')
        self._greeting.setFont(font(13, True))
        self._greeting.setStyleSheet('color:#0f172a;')
        tlay.addWidget(self._greeting)
        tlay.addStretch()

        hist_btn = QPushButton('Riwayat')
        hist_btn.setFont(font(10))
        hist_btn.setFixedHeight(34)
        hist_btn.setCursor(Qt.PointingHandCursor)
        hist_btn.setStyleSheet(
            f'QPushButton{{background:#eff6ff;color:{ACCENT};'
            f'border:1px solid #bfdbfe;border-radius:6px;padding:0 14px;}}'
            f'QPushButton:hover{{background:#dbeafe;}}'
        )
        hist_btn.clicked.connect(self.open_history.emit)
        tlay.addWidget(hist_btn)
        lay.addWidget(topbar)

        # Main scroll
        from ui.base import ScrollPage
        scroll = ScrollPage()
        inner  = scroll.inner_layout()
        inner.setSpacing(20)

        self._hero_sub = QLabel('')
        self._hero_sub.setFont(font(11))
        self._hero_sub.setStyleSheet('color:#64748b;')
        inner.addWidget(self._hero_sub)

        # Test cards — horizontal, compact
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self._iq_card = self._make_test_card('IQ', 'Tes IQ', '40 soal · 20 menit · Berbobot difficulty', ACCENT, self.start_iq.emit)
        self._bf_card = self._make_test_card('BF', 'Tes Kepribadian', '50 pernyataan · Likert 1–5 · OCEAN Profile', '#7c3aed', self.start_bf.emit)
        cards_row.addWidget(self._iq_card)
        cards_row.addWidget(self._bf_card)
        cw = QWidget()
        cw.setLayout(cards_row)
        inner.addWidget(cw)

        # Recent
        self._recent_section = QWidget()
        self._recent_lay = QVBoxLayout(self._recent_section)
        self._recent_lay.setContentsMargins(0,0,0,0)
        self._recent_lay.setSpacing(6)
        inner.addWidget(self._recent_section)

        inner.addStretch()
        lay.addWidget(scroll, 1)
        return w

    def _make_test_card(self, badge: str, title: str, desc: str, color: str, on_click) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f'QFrame{{background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;}}'
            f'QFrame:hover{{border-color:{color};}}'
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(16)

        # Badge
        badge_lbl = QLabel(badge)
        badge_lbl.setFixedSize(40, 40)
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_lbl.setFont(font(11, True))
        badge_lbl.setStyleSheet(
            f'background:{color}15;color:{color};'
            f'border:1.5px solid {color}33;border-radius:8px;'
        )
        lay.addWidget(badge_lbl)

        # Info
        info = QVBoxLayout()
        info.setSpacing(3)
        title_lbl = QLabel(title)
        title_lbl.setFont(font(12, True))
        title_lbl.setStyleSheet('color:#0f172a;')
        desc_lbl = QLabel(desc)
        desc_lbl.setFont(font(9))
        desc_lbl.setStyleSheet('color:#94a3b8;')
        info.addWidget(title_lbl)
        info.addWidget(desc_lbl)
        lay.addLayout(info, 1)

        # CTA
        btn = QPushButton('Mulai')
        btn.setFont(font(10, True))
        btn.setFixedSize(72, 34)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f'QPushButton{{background:{color};color:#fff;border:none;border-radius:6px;}}'
            f'QPushButton:hover{{opacity:0.9;}}'
        )
        btn.clicked.connect(on_click)
        lay.addWidget(btn)

        card._btn = btn
        card._title = title_lbl
        card._desc  = desc_lbl
        return card

    def set_user(self, user: dict):
        self._user = user
        self._refresh()

    def _refresh(self):
        if not self._user: return
        l    = get_lang()
        name = self._user['name']
        uid  = self._user['id']

        self._user_lbl.setText(name)
        self._greeting.setText(f'Halo, {name}' if l=='id' else f'Hello, {name}')
        self._hero_sub.setText(
            'Mulai tes untuk menganalisis kecerdasan dan kepribadianmu.' if l=='id'
            else 'Start a test to analyze your intelligence and personality.'
        )

        sessions = get_sessions(uid, limit=100)
        n = len(sessions)
        self._stats_lbl.setText(f'{n} sesi' if l=='id' else f'{n} sessions')

        while self._recent_lay.count():
            item = self._recent_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        recent = get_sessions(uid, limit=5)
        if recent:
            hdr = QLabel('Hasil Terbaru' if l=='id' else 'Recent Results')
            hdr.setFont(font(11, True))
            hdr.setStyleSheet('color:#0f172a;')
            self._recent_lay.addWidget(hdr)
            for s in recent:
                scores = get_scores(s['id'])
                self._recent_lay.addWidget(self._make_recent_row(s, scores, l))

    def _make_recent_row(self, session: dict, scores: dict, lang: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            'QFrame{background:#fff;border:1px solid #e2e8f0;border-radius:8px;}'
            'QFrame:hover{border-color:#93c5fd;}'
        )
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)

        test_type = session.get('test_type','')
        is_iq     = test_type == 'iq'
        badge_col = ACCENT if is_iq else '#7c3aed'
        badge_txt = 'IQ' if is_iq else 'BF'

        badge = QLabel(badge_txt)
        badge.setFixedSize(28, 28)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFont(font(8, True))
        badge.setStyleSheet(
            f'background:{badge_col}15;color:{badge_col};'
            f'border:1px solid {badge_col}33;border-radius:6px;'
        )
        lay.addWidget(badge)
        lay.addSpacing(10)

        date_lbl = QLabel(session.get('taken_at','')[:16].replace('T',' '))
        date_lbl.setFont(font(10))
        date_lbl.setStyleSheet('color:#64748b;')
        lay.addWidget(date_lbl)
        lay.addStretch()

        if 'IQ' in scores:
            iq_lbl = QLabel(f"IQ {scores['IQ']['normalized']:.0f}")
            iq_lbl.setFont(font(10, True))
            iq_lbl.setStyleSheet(f'color:{ACCENT};')
            lay.addWidget(iq_lbl)
            lay.addSpacing(10)

        for t in 'OCEAN':
            if t in scores:
                lbl = QLabel(f'{t} {scores[t]["normalized"]:.0f}')
                lbl.setFont(font(9))
                lbl.setStyleSheet(f'color:{TRAIT_COLORS[t]};')
                lay.addWidget(lbl)
                lay.addSpacing(6)

        arr = QLabel('›')
        arr.setFont(font(14))
        arr.setStyleSheet('color:#cbd5e1;')
        lay.addWidget(arr)
        return card

    def _on_lang(self, _):
        if self._user: self._refresh()


class MainWindow(QStackedWidget):
    PAGE_AUTH    = 0
    PAGE_HOME    = 1
    PAGE_IQ_TEST = 2
    PAGE_IQ_RES  = 3
    PAGE_BF_TEST = 4
    PAGE_BF_RES  = 5
    PAGE_HISTORY = 6

    def __init__(self):
        init_lang_bus()
        init_db()
        super().__init__()
        self.setMinimumSize(1100, 720)
        self.setWindowTitle('Assessment IQ & Kepribadian v5.0')
        self._user       = None
        self._iq_answers = None
        self._iq_session = None
        self._build_pages()

    def _build_pages(self):
        from ui.auth      import AuthPage
        from ui.iq_test   import IQTestPage
        from ui.iq_result import IQResultPage
        from ui.bf_test   import BFTestPage
        from ui.bf_result import BFResultPage
        from ui.history   import HistoryPage

        self._auth = AuthPage()
        self._auth.logged_in.connect(self._on_login)
        self.addWidget(self._auth)

        self._home = HomePage()
        self._home.start_iq.connect(self._go_iq_test)
        self._home.start_bf.connect(self._go_bf_test)
        self._home.open_history.connect(self._go_history)
        self._home.logout.connect(self._logout)
        self.addWidget(self._home)

        self._iq_test = IQTestPage()
        self._iq_test.finished.connect(self._on_iq_done)
        self._iq_test.go_home.connect(lambda: self.setCurrentIndex(self.PAGE_HOME))
        self.addWidget(self._iq_test)

        self._iq_result = IQResultPage()
        self._iq_result.go_home.connect(lambda: self.setCurrentIndex(self.PAGE_HOME))
        self._iq_result.go_history.connect(self._go_history)
        self._iq_result.export_pdf.connect(self._export_pdf)
        self.addWidget(self._iq_result)

        self._bf_test = BFTestPage()
        self._bf_test.finished.connect(self._on_bf_done)
        self._bf_test.go_home.connect(lambda: self.setCurrentIndex(self.PAGE_HOME))
        self.addWidget(self._bf_test)

        self._bf_result = BFResultPage()
        self._bf_result.set_iq_data_fn(self._get_iq_data)
        self._bf_result.go_home.connect(lambda: self.setCurrentIndex(self.PAGE_HOME))
        self._bf_result.go_history.connect(self._go_history)
        self._bf_result.export_pdf.connect(self._export_pdf)
        self.addWidget(self._bf_result)

        self._history = HistoryPage()
        self._history.back.connect(lambda: self.setCurrentIndex(self.PAGE_HOME))
        self._history.open_session.connect(self._open_session_detail)
        self.addWidget(self._history)

        self.setCurrentIndex(self.PAGE_AUTH)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12:
            self._open_admin()
        else:
            super().keyPressEvent(event)

    def _open_admin(self):
        from ui.admin import AdminLoginDialog, AdminPanel
        dlg = AdminLoginDialog(self)
        if dlg.exec_() == dlg.Accepted and dlg.success():
            self._admin_panel = AdminPanel()
            self._admin_panel.show()

    def _on_login(self, user: dict):
        self._user = user
        self._home.set_user(user)
        self.setCurrentIndex(self.PAGE_HOME)

    def _logout(self):
        self._user = self._iq_answers = self._iq_session = None
        self._auth.refresh()
        self.setCurrentIndex(self.PAGE_AUTH)

    def _go_iq_test(self):
        self._iq_test.start_test(self._user)
        self.setCurrentIndex(self.PAGE_IQ_TEST)

    def _go_bf_test(self):
        self._bf_test.start_test(self._user)
        self.setCurrentIndex(self.PAGE_BF_TEST)

    def _go_history(self):
        self._history.load_user(self._user)
        self.setCurrentIndex(self.PAGE_HISTORY)

    def _on_iq_done(self, answers, session):
        self._iq_answers = answers
        self._iq_session = session
        self._iq_result.load_results(answers, session, self._user)
        self.setCurrentIndex(self.PAGE_IQ_RES)

    def _on_bf_done(self, answers, session):
        self._bf_result.load_results(answers, session, self._user)
        self.setCurrentIndex(self.PAGE_BF_RES)
        if self._user: self._home.set_user(self._user)

    def _get_iq_data(self):
        if self._iq_answers and self._iq_session:
            return self._iq_answers, self._iq_session
        return None

    def _open_session_detail(self, session_id: int, test_type: str):
        from core.database import get_answers, get_session
        from core.knowledge_base import IQ_BY_CAT_ID, BF_BY_TRAIT
        try:
            session_meta = get_session(session_id)
            answers_raw  = get_answers(session_id)
            lang         = session_meta.get('lang','id') if session_meta else 'id'
            if test_type == 'iq':
                import random
                random.seed(session_id)
                session = []
                for cat, questions in IQ_BY_CAT_ID.items():
                    pool = questions[:]
                    random.shuffle(pool)
                    picked = sorted(pool[:8], key=lambda q: q['difficulty'])
                    session.extend(picked)
                random.shuffle(session)
                localized = []
                for q in session:
                    opts_key = f'opts_{lang}' if f'opts_{lang}' in q else 'opts'
                    localized.append({**q, 'q': q[f'q_{lang}'], 'opts': q[opts_key],
                        'explanation': q[f'exp_{lang}'], 'category': q['cat_id'] if lang=='id' else q['cat_en']})
                ans_map = {a['question_id']: a['value'] for a in answers_raw}
                answers = [ans_map.get(q['id'], -1) for q in localized]
                self._iq_result.load_results(answers, localized, self._user)
                self.setCurrentIndex(self.PAGE_IQ_RES)
            elif test_type == 'bigfive':
                import random
                random.seed(session_id)
                session = []
                for t in 'OCEAN':
                    pool = BF_BY_TRAIT[t][:]
                    random.shuffle(pool)
                    session.extend(pool[:10])
                random.shuffle(session)
                ans_map = {a['question_id']: a['value'] for a in answers_raw}
                answers = [ans_map.get(q[0], 3) for q in session]
                self._bf_result.load_results(answers, session, self._user)
                self.setCurrentIndex(self.PAGE_BF_RES)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Error', str(e))

    def _export_pdf(self, analysis: dict):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        name  = self._user["name"].replace(" ", "_")
        ttype = analysis.get("test_type", "")
        default_name = (
            f'IQ_Test_Summary_{name}.pdf' if ttype == 'iq'
            else f'BigFive_Test_Summary_{name}.pdf'
        )
        path, _ = QFileDialog.getSaveFileName(self, 'Save PDF', default_name, 'PDF (*.pdf)')
        if path:
            try:
                from report.pdf_generator import generate_pdf
                import json
                with open(f'i18n/{get_lang()}.json', encoding='utf-8') as f:
                    txt = json.load(f)
                generate_pdf(path, analysis, txt)
                QMessageBox.information(self, 'Export', f'PDF disimpan di:\n{path}')
            except Exception as e:
                QMessageBox.warning(self, 'Export Error', str(e))