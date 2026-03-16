"""
ui/iq_test.py — Redesigned: Refined Utilitarian
"""

import random
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy, QGridLayout,
    QProgressBar,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from ui.base import (
    D_BG, D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, PURPLE, ORANGE,
    font, primary_btn, ghost_btn,
    CountdownTimer, LangToggle,
    get_lang, LANG_BUS,
)
from core.knowledge_base import IQ_BY_CAT_ID, IQ_COGNITIVE_DOMAINS
from core.inference import (
    score_iq, build_cognitive_profile,
    iq_answers_to_db_rows, iq_scores_to_db_rows,
)
from core.database import create_session, finish_session, save_answers, save_scores

# ── Design tokens ──────────────────────────────────────────
ACCENT   = '#2563eb'   # single blue accent
ANSWERED = '#dcfce7'   # light green bg
ANS_BORDER = '#16a34a' # green border
CURRENT  = '#eff6ff'   # light blue bg
CUR_BORDER = '#2563eb' # blue border
EMPTY    = '#f8fafc'
EMP_BORDER = '#e2e8f0'


# ══════════════════════════════════════════════════════════════
# SESSION BUILDER
# ══════════════════════════════════════════════════════════════
def make_iq_session(lang: str = 'id') -> list:
    session = []
    for cat, questions in IQ_BY_CAT_ID.items():
        pool = questions[:]
        random.shuffle(pool)
        picked = sorted(pool[:8], key=lambda q: q['difficulty'])
        session.extend(picked)
    random.shuffle(session)
    out = []
    for q in session:
        opts_key = f'opts_{lang}' if f'opts_{lang}' in q else 'opts'
        out.append({
            **q,
            'q':           q[f'q_{lang}'],
            'opts':        q[opts_key],
            'explanation': q[f'exp_{lang}'],
            'category':    q['cat_id'] if lang == 'id' else q['cat_en'],
        })
    return out


# ══════════════════════════════════════════════════════════════
# NUMBER BUTTON
# ══════════════════════════════════════════════════════════════
class NumBtn(QPushButton):
    def __init__(self, n: int, parent=None):
        super().__init__(str(n), parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(font(9))
        self._state = 'empty'
        self._apply()

    def set_state(self, s: str):
        self._state = s
        self._apply()

    def _apply(self):
        if self._state == 'current':
            self.setStyleSheet(
                f'QPushButton{{background:{ACCENT};color:#fff;'
                f'border:none;border-radius:4px;font-weight:600;}}'
            )
        elif self._state == 'answered':
            self.setStyleSheet(
                f'QPushButton{{background:{ANSWERED};color:{ANS_BORDER};'
                f'border:1px solid {ANS_BORDER};border-radius:4px;}}'
                f'QPushButton:hover{{background:#bbf7d0;}}'
            )
        else:
            self.setStyleSheet(
                f'QPushButton{{background:{EMPTY};color:#94a3b8;'
                f'border:1px solid {EMP_BORDER};border-radius:4px;}}'
                f'QPushButton:hover{{border-color:{ACCENT};color:{ACCENT};}}'
            )


# ══════════════════════════════════════════════════════════════
# IQ TEST PAGE
# ══════════════════════════════════════════════════════════════
class IQTestPage(QWidget):
    finished = pyqtSignal(list, list)
    go_home  = pyqtSignal()
    TOTAL_SECONDS = 1200
    LETTERS = ['A', 'B', 'C', 'D']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session  = []
        self._answers  = []
        self._current  = 0
        self._start_ts = 0
        self._num_btns = []
        self.setStyleSheet('background:#f8fafc;')
        self._build()
        if LANG_BUS:
            LANG_BUS.changed.connect(self._on_lang)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_content(), 1)
        root.addWidget(self._make_sidebar())

    # ── SIDEBAR ──────────────────────────────────────────────
    def _make_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet(
            f'background:#1e293b;border-left:1px solid #0f172a;'
        )
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.setSpacing(10)

        # Title
        title = QLabel('IQ Test')
        title.setFont(font(12, True))
        title.setStyleSheet('color:#f1f5f9;')
        lay.addWidget(title)

        # Timer
        self._timer = CountdownTimer(self.TOTAL_SECONDS)
        self._timer.timeout.connect(self._on_timeout)
        lay.addWidget(self._timer, 0, Qt.AlignCenter)

        # Progress
        self._prog_lbl = QLabel('0/40')
        self._prog_lbl.setFont(font(9))
        self._prog_lbl.setStyleSheet('color:#94a3b8;')
        self._prog_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._prog_lbl)

        # Legend
        leg = QHBoxLayout()
        for col, lbl in [('#16a34a', 'Dijawab'), ('#94a3b8', 'Belum')]:
            dot = QLabel('●')
            dot.setFont(font(8))
            dot.setStyleSheet(f'color:{col};')
            t = QLabel(lbl)
            t.setFont(font(8))
            t.setStyleSheet('color:#64748b;')
            leg.addWidget(dot)
            leg.addWidget(t)
            leg.addSpacing(6)
        leg.addStretch()
        lay.addLayout(leg)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet('background:#334155;border:none;')
        lay.addWidget(div)

        # Grid
        self._grid_frame = QFrame()
        self._grid_frame.setStyleSheet('background:transparent;')
        self._grid_lay = QGridLayout(self._grid_frame)
        self._grid_lay.setSpacing(4)
        self._grid_lay.setContentsMargins(0, 0, 0, 0)

        grid_scroll = QScrollArea()
        grid_scroll.setWidget(self._grid_frame)
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setFrameShape(QFrame.NoFrame)
        grid_scroll.setStyleSheet('background:#1e293b;border:none;')
        grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(grid_scroll, 1)

        # Divider
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet('background:#334155;border:none;')
        lay.addWidget(div2)

        # Submit
        self._submit_btn = QPushButton('Submit Tes')
        self._submit_btn.setFont(font(11, True))
        self._submit_btn.setFixedHeight(40)
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.setStyleSheet(
            f'QPushButton{{background:{GREEN};color:#fff;border:none;border-radius:6px;}}'
            f'QPushButton:hover{{background:#15803d;}}'
            f'QPushButton:disabled{{background:#334155;color:#64748b;}}'
        )
        self._submit_btn.clicked.connect(self._submit)
        lay.addWidget(self._submit_btn)

        home_btn = QPushButton('← Home')
        home_btn.setFont(font(9))
        home_btn.setFixedHeight(32)
        home_btn.setCursor(Qt.PointingHandCursor)
        home_btn.setStyleSheet(
            'QPushButton{background:transparent;color:#64748b;border:none;}'
            'QPushButton:hover{color:#94a3b8;}'
        )
        home_btn.clicked.connect(self.go_home.emit)
        lay.addWidget(home_btn)

        return sb

    # ── CONTENT ──────────────────────────────────────────────
    def _make_content(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet('background:#f8fafc;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet('background:#fff;border-bottom:1px solid #e2e8f0;')
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(24, 0, 24, 0)

        self._title_lbl = QLabel('IQ Assessment')
        self._title_lbl.setFont(font(12, True))
        self._title_lbl.setStyleSheet('color:#0f172a;')
        tlay.addWidget(self._title_lbl)
        tlay.addStretch()

        self._cat_lbl = QLabel('')
        self._cat_lbl.setFont(font(9))
        self._cat_lbl.setStyleSheet(
            f'color:{ACCENT};background:#eff6ff;'
            f'border:1px solid #bfdbfe;border-radius:4px;padding:2px 8px;'
        )
        tlay.addWidget(self._cat_lbl)
        tlay.addSpacing(12)

        self._diff_lbl = QLabel('')
        self._diff_lbl.setFont(font(10))
        self._diff_lbl.setStyleSheet('color:#f59e0b;')
        tlay.addWidget(self._diff_lbl)
        tlay.addSpacing(12)

        tlay.addWidget(LangToggle())
        lay.addWidget(topbar)

        # Question area
        self._q_scroll = QScrollArea()
        self._q_scroll.setWidgetResizable(True)
        self._q_scroll.setFrameShape(QFrame.NoFrame)
        self._q_scroll.setStyleSheet('background:#f8fafc;border:none;')
        self._q_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self._q_scroll, 1)

        # Bottom nav
        nav = QFrame()
        nav.setFixedHeight(56)
        nav.setStyleSheet('background:#fff;border-top:1px solid #e2e8f0;')
        nlay = QHBoxLayout(nav)
        nlay.setContentsMargins(24, 0, 24, 0)

        self._prev_btn = QPushButton('← Sebelumnya')
        self._prev_btn.setFont(font(10))
        self._prev_btn.setFixedHeight(36)
        self._prev_btn.setFixedWidth(140)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.setStyleSheet(
            f'QPushButton{{background:#fff;color:{ACCENT};'
            f'border:1px solid #e2e8f0;border-radius:6px;}}'
            f'QPushButton:hover{{border-color:{ACCENT};}}'
            f'QPushButton:disabled{{color:#cbd5e1;border-color:#e2e8f0;}}'
        )
        self._prev_btn.clicked.connect(self._go_prev)

        self._q_counter = QLabel('')
        self._q_counter.setFont(font(10))
        self._q_counter.setStyleSheet('color:#64748b;')
        self._q_counter.setAlignment(Qt.AlignCenter)

        self._next_btn = QPushButton('Selanjutnya →')
        self._next_btn.setFont(font(10, True))
        self._next_btn.setFixedHeight(36)
        self._next_btn.setFixedWidth(140)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(
            f'QPushButton{{background:{ACCENT};color:#fff;'
            f'border:none;border-radius:6px;}}'
            f'QPushButton:hover{{background:#1d4ed8;}}'
            f'QPushButton:disabled{{background:#e2e8f0;color:#94a3b8;}}'
        )
        self._next_btn.clicked.connect(self._go_next)

        nlay.addWidget(self._prev_btn)
        nlay.addStretch()
        nlay.addWidget(self._q_counter)
        nlay.addStretch()
        nlay.addWidget(self._next_btn)
        lay.addWidget(nav)
        return w

    # ── Grid ─────────────────────────────────────────────────
    def _build_grid(self):
        for b in self._num_btns: b.deleteLater()
        self._num_btns.clear()
        cols = 5
        for i in range(len(self._session)):
            btn = NumBtn(i + 1)
            btn.clicked.connect(lambda _, idx=i: self._show_question(idx))
            self._grid_lay.addWidget(btn, i // cols, i % cols)
            self._num_btns.append(btn)

    def _update_grid(self):
        for i, btn in enumerate(self._num_btns):
            if i == self._current:      btn.set_state('current')
            elif self._answers[i] is not None: btn.set_state('answered')
            else:                       btn.set_state('empty')
        answered = sum(1 for a in self._answers if a is not None)
        self._prog_lbl.setText(f'{answered}/{len(self._answers)}')

    # ── Start ─────────────────────────────────────────────────
    def start_test(self, user: dict):
        self._user     = user
        lang           = get_lang()
        self._session  = make_iq_session(lang)
        self._answers  = [None] * len(self._session)
        self._current  = 0
        self._start_ts = time.time()
        self._build_grid()
        self._timer.reset(self.TOTAL_SECONDS)
        self._timer.start()
        self._show_question(0)

    # ── Show question ─────────────────────────────────────────
    def _show_question(self, idx: int):
        self._current = idx
        q     = self._session[idx]
        total = len(self._session)
        l     = get_lang()

        self._cat_lbl.setText(q.get('category', ''))
        diff = q.get('difficulty', 4)
        self._diff_lbl.setText('★' * diff + '☆' * (7 - diff))
        self._q_counter.setText(f'{idx + 1} / {total}')
        self._prev_btn.setEnabled(idx > 0)
        self._next_btn.setEnabled(idx < total - 1)
        self._update_grid()
        self._q_scroll.setWidget(self._build_q_widget(idx, q, l))

    def _build_q_widget(self, idx: int, q: dict, lang: str) -> QWidget:
        selected = self._answers[idx]
        w = QWidget()
        w.setStyleSheet('background:#f8fafc;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(16)

        # Question number + text
        num = QLabel(f'Soal {idx+1}' if lang=='id' else f'Question {idx+1}')
        num.setFont(font(9))
        num.setStyleSheet(
            f'color:{ACCENT};background:#eff6ff;border:1px solid #bfdbfe;'
            f'border-radius:4px;padding:3px 10px;'
        )
        num.setFixedHeight(24)
        num.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lay.addWidget(num)

        q_text = QLabel(q['q'])
        q_text.setFont(font(14))
        q_text.setStyleSheet('color:#0f172a;line-height:1.6;background:transparent;')
        q_text.setWordWrap(True)
        q_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(q_text)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet('background:#e2e8f0;border:none;')
        lay.addWidget(div)

        # Options
        opts_label = QLabel('Pilih jawaban:' if lang=='id' else 'Choose your answer:')
        opts_label.setFont(font(9))
        opts_label.setStyleSheet('color:#94a3b8;')
        lay.addWidget(opts_label)

        for i, opt in enumerate(q.get('opts', [])):
            is_sel = (selected == i)
            letter = self.LETTERS[i] if i < 4 else str(i+1)

            btn = QFrame()
            btn.setStyleSheet(
                f'QFrame{{background:{"#eff6ff" if is_sel else "#fff"};'
                f'border:{"2px" if is_sel else "1px"} solid '
                f'{"#2563eb" if is_sel else "#e2e8f0"};'
                f'border-radius:8px;}}'
            )
            btn.setCursor(Qt.PointingHandCursor)
            blay = QHBoxLayout(btn)
            blay.setContentsMargins(14, 10, 14, 10)
            blay.setSpacing(12)

            letter_lbl = QLabel(letter)
            letter_lbl.setFixedSize(28, 28)
            letter_lbl.setAlignment(Qt.AlignCenter)
            letter_lbl.setFont(font(10, True))
            letter_lbl.setStyleSheet(
                f'background:{"#2563eb" if is_sel else "#f1f5f9"};'
                f'color:{"#fff" if is_sel else "#64748b"};'
                f'border-radius:4px;'
            )

            text_lbl = QLabel(opt)
            text_lbl.setFont(font(11))
            text_lbl.setStyleSheet(
                f'color:{"#1e40af" if is_sel else "#1e293b"};background:transparent;'
            )
            text_lbl.setWordWrap(True)

            blay.addWidget(letter_lbl)
            blay.addWidget(text_lbl, 1)
            btn.mousePressEvent = lambda e, ii=i: self._select_option(ii)
            lay.addWidget(btn)

        lay.addStretch()
        return w

    def _select_option(self, opt_idx: int):
        self._answers[self._current] = opt_idx
        self._update_grid()
        q = self._session[self._current]
        self._q_scroll.setWidget(self._build_q_widget(self._current, q, get_lang()))

    def _go_prev(self):
        if self._current > 0: self._show_question(self._current - 1)

    def _go_next(self):
        if self._current < len(self._session) - 1:
            self._show_question(self._current + 1)

    def _on_timeout(self):
        from PyQt5.QtWidgets import QMessageBox
        self._timer.stop()
        l = get_lang()
        msg = QMessageBox(self)
        msg.setWindowTitle('Waktu Habis!' if l=='id' else "Time's Up!")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            'Waktu tes telah habis.\nHasil dihitung dari jawaban yang sudah kamu isi.' if l=='id'
            else "Time is up!\nResults calculated from answers you've filled in."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        self._do_submit()

    def _submit(self):
        from PyQt5.QtWidgets import QMessageBox
        unanswered = sum(1 for a in self._answers if a is None)
        if unanswered > 0:
            l = get_lang()
            msg = QMessageBox(self)
            msg.setWindowTitle('Belum Selesai' if l=='id' else 'Not Finished')
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                f'Masih ada {unanswered} soal yang belum dijawab.\n'
                f'Selesaikan semua soal sebelum submit!' if l=='id'
                else f'{unanswered} questions still unanswered.\n'
                f'Please answer all questions before submitting!'
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        self._timer.stop()
        self._do_submit()

    def _do_submit(self):
        duration = int(time.time() - self._start_ts)
        lang     = get_lang()
        uid      = self._user['id']
        answers  = [a if a is not None else -1 for a in self._answers]
        sid      = create_session(uid, 'iq', lang)
        finish_session(sid, duration)
        save_answers(sid, iq_answers_to_db_rows(self._session, answers))
        iq_result  = score_iq(answers, self._session)
        cognitive  = build_cognitive_profile(answers, self._session)
        save_scores(sid, iq_scores_to_db_rows(iq_result, cognitive))
        self.finished.emit(answers, self._session)

    def _on_lang(self, lang: str):
        self._submit_btn.setText('Submit Tes' if lang=='id' else 'Submit Test')
        self._prev_btn.setText('← Sebelumnya' if lang=='id' else '← Previous')
        self._next_btn.setText('Selanjutnya →' if lang=='id' else 'Next →')
        if self._session:
            self._session = make_iq_session(lang)
            self._show_question(self._current)