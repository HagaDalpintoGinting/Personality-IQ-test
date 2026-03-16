"""
ui/bf_test.py — Redesigned: Refined Utilitarian
"""

import random
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy, QGridLayout,
    QButtonGroup,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.base import (
    D_BG, D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, PURPLE, ORANGE,
    TRAIT_COLORS, AnimatedBar,
    font, primary_btn, ghost_btn,
    LangToggle, get_lang, LANG_BUS,
)
from core.knowledge_base import BF_BY_TRAIT, BF_DIMENSIONS
from core.inference import (
    score_bigfive, bf_answers_to_db_rows, bf_scores_to_db_rows,
)
from core.database import create_session, finish_session, save_answers, save_scores

ACCENT = '#2563eb'

LIKERT_DATA = [
    ('#ef4444', '1', 'Sangat\nTidak Setuju', 'Strongly\nDisagree'),
    ('#f97316', '2', 'Tidak\nSetuju',        'Disagree'),
    ('#eab308', '3', 'Netral',               'Neutral'),
    ('#22c55e', '4', 'Setuju',               'Agree'),
    ('#16a34a', '5', 'Sangat\nSetuju',       'Strongly\nAgree'),
]


def make_bf_session(lang: str = 'id') -> list:
    session = []
    for t in 'OCEAN':
        pool = BF_BY_TRAIT[t][:]
        random.shuffle(pool)
        session.extend(pool[:10])
    random.shuffle(session)
    return session


class NumBtn(QPushButton):
    def __init__(self, n: int, trait: str = '', parent=None):
        super().__init__(str(n), parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(font(9))
        self._trait = trait
        self._state = 'empty'
        self._apply()

    def set_state(self, s: str):
        self._state = s
        self._apply()

    def _apply(self):
        col = TRAIT_COLORS.get(self._trait, ACCENT)
        if self._state == 'current':
            self.setStyleSheet(
                f'QPushButton{{background:{ACCENT};color:#fff;'
                f'border:none;border-radius:4px;font-weight:600;}}'
            )
        elif self._state == 'answered':
            self.setStyleSheet(
                f'QPushButton{{background:#dcfce7;color:#16a34a;'
                f'border:1px solid #16a34a;border-radius:4px;}}'
                f'QPushButton:hover{{background:#bbf7d0;}}'
            )
        else:
            self.setStyleSheet(
                f'QPushButton{{background:#f8fafc;color:#94a3b8;'
                f'border:1px solid #e2e8f0;border-radius:4px;}}'
                f'QPushButton:hover{{border-color:{col};color:{col};}}'
            )


class BFTestPage(QWidget):
    finished = pyqtSignal(list, list)
    go_home  = pyqtSignal()

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

    def _make_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet('background:#1e293b;border-left:1px solid #0f172a;')
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.setSpacing(10)

        title = QLabel('Big Five')
        title.setFont(font(12, True))
        title.setStyleSheet('color:#f1f5f9;')
        lay.addWidget(title)

        self._prog_lbl = QLabel('0/50')
        self._prog_lbl.setFont(font(9))
        self._prog_lbl.setStyleSheet('color:#94a3b8;')
        self._prog_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._prog_lbl)

        # Trait bars
        self._trait_bars = {}
        for t in 'OCEAN':
            col = TRAIT_COLORS[t]
            row = QHBoxLayout()
            lbl = QLabel(t)
            lbl.setFont(font(9, True))
            lbl.setStyleSheet(f'color:{col};')
            lbl.setFixedWidth(14)
            bar = AnimatedBar(0, col, 6)
            self._trait_bars[t] = bar
            row.addWidget(lbl)
            row.addWidget(bar, 1)
            lay.addLayout(row)

        # Legend
        leg = QHBoxLayout()
        for col, lbl in [('#16a34a', 'Dijawab'), ('#94a3b8', 'Belum')]:
            dot = QLabel('●')
            dot.setFont(font(8))
            dot.setStyleSheet(f'color:{col};')
            t2 = QLabel(lbl)
            t2.setFont(font(8))
            t2.setStyleSheet('color:#64748b;')
            leg.addWidget(dot)
            leg.addWidget(t2)
            leg.addSpacing(6)
        leg.addStretch()
        lay.addLayout(leg)

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

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet('background:#334155;border:none;')
        lay.addWidget(div2)

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

    def _make_content(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet('background:#f8fafc;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet('background:#fff;border-bottom:1px solid #e2e8f0;')
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(24, 0, 24, 0)

        self._title_lbl = QLabel('Personality Assessment')
        self._title_lbl.setFont(font(12, True))
        self._title_lbl.setStyleSheet('color:#0f172a;')
        tlay.addWidget(self._title_lbl)
        tlay.addStretch()

        self._trait_badge = QLabel('')
        self._trait_badge.setFont(font(9))
        tlay.addWidget(self._trait_badge)
        tlay.addSpacing(12)
        tlay.addWidget(LangToggle())
        lay.addWidget(topbar)

        self._q_scroll = QScrollArea()
        self._q_scroll.setWidgetResizable(True)
        self._q_scroll.setFrameShape(QFrame.NoFrame)
        self._q_scroll.setStyleSheet('background:#f8fafc;border:none;')
        self._q_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self._q_scroll, 1)

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

    def _build_grid(self):
        for b in self._num_btns: b.deleteLater()
        self._num_btns.clear()
        cols = 5
        for i, q in enumerate(self._session):
            trait = q[1]
            btn = NumBtn(i + 1, trait)
            btn.clicked.connect(lambda _, idx=i: self._show_question(idx))
            self._grid_lay.addWidget(btn, i // cols, i % cols)
            self._num_btns.append(btn)

    def _update_grid(self):
        for i, btn in enumerate(self._num_btns):
            if i == self._current:             btn.set_state('current')
            elif self._answers[i] is not None: btn.set_state('answered')
            else:                              btn.set_state('empty')

        answered = sum(1 for a in self._answers if a is not None)
        self._prog_lbl.setText(f'{answered}/50')

        for t in 'OCEAN':
            filled  = sum(1 for i,q in enumerate(self._session) if q[1]==t and self._answers[i] is not None)
            total_t = sum(1 for q in self._session if q[1]==t)
            self._trait_bars[t].set_value((filled/total_t*100) if total_t else 0)

    def start_test(self, user: dict):
        self._user     = user
        self._session  = make_bf_session(get_lang())
        self._answers  = [None] * len(self._session)
        self._current  = 0
        self._start_ts = time.time()
        self._build_grid()
        self._show_question(0)

    def _show_question(self, idx: int):
        self._current = idx
        q, total = self._session[idx], len(self._session)
        l = get_lang()
        qid, trait, text_id, text_en, reversed_ = q
        col = TRAIT_COLORS.get(trait, ACCENT)
        dim_name = BF_DIMENSIONS[trait][f'short_{l}']

        self._trait_badge.setText(f'● {dim_name}')
        self._trait_badge.setStyleSheet(
            f'color:{col};background:{col}15;'
            f'border:1px solid {col}44;border-radius:4px;padding:2px 8px;font-size:9px;'
        )
        self._q_counter.setText(f'{idx + 1} / {total}')
        self._prev_btn.setEnabled(idx > 0)
        self._next_btn.setEnabled(idx < total - 1)
        self._update_grid()
        self._q_scroll.setWidget(self._build_q_widget(idx, q, l))

    def _build_q_widget(self, idx: int, q: tuple, lang: str) -> QWidget:
        qid, trait, text_id, text_en, reversed_ = q
        text     = text_en if lang == 'en' else text_id
        col      = TRAIT_COLORS.get(trait, ACCENT)
        selected = self._answers[idx]

        w = QWidget()
        w.setStyleSheet('background:#f8fafc;')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(16)

        # Meta
        meta = QHBoxLayout()
        num_lbl = QLabel(f'Pernyataan {idx+1}' if lang=='id' else f'Statement {idx+1}')
        num_lbl.setFont(font(9))
        num_lbl.setStyleSheet(
            f'color:{col};background:{col}12;border:1px solid {col}33;'
            f'border-radius:4px;padding:3px 10px;'
        )
        num_lbl.setFixedHeight(24)
        num_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        meta.addWidget(num_lbl)
        if reversed_:
            rev = QLabel('dibalik' if lang=='id' else 'reversed')
            rev.setFont(font(8))
            rev.setStyleSheet('color:#f59e0b;background:#fef3c7;border:1px solid #fcd34d;border-radius:4px;padding:2px 7px;')
            rev.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            meta.addSpacing(6)
            meta.addWidget(rev)
        meta.addStretch()
        lay.addLayout(meta)

        # Statement
        instr = QLabel(
            'Seberapa akurat pernyataan ini menggambarkan dirimu?' if lang=='id'
            else 'How accurately does this statement describe you?'
        )
        instr.setFont(font(9))
        instr.setStyleSheet('color:#94a3b8;font-style:italic;')
        lay.addWidget(instr)

        stmt = QLabel(text)
        stmt.setFont(font(15))
        stmt.setStyleSheet('color:#0f172a;line-height:1.6;background:transparent;')
        stmt.setWordWrap(True)
        stmt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(stmt)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet('background:#e2e8f0;border:none;')
        lay.addWidget(div)

        # Likert — horizontal row of labeled buttons
        likert_frame = QFrame()
        likert_frame.setStyleSheet('background:#fff;border:1px solid #e2e8f0;border-radius:8px;')
        lklay = QHBoxLayout(likert_frame)
        lklay.setContentsMargins(20, 14, 20, 14)
        lklay.setSpacing(0)

        for i, (color, num, label_id, label_en) in enumerate(LIKERT_DATA):
            label = label_id if lang == 'id' else label_en
            is_sel = (selected == i + 1)

            col_lay = QVBoxLayout()
            col_lay.setSpacing(6)
            col_lay.setAlignment(Qt.AlignCenter)

            btn = QPushButton(num)
            btn.setFixedSize(44, 44)
            btn.setFont(font(13, True))
            btn.setCursor(Qt.PointingHandCursor)
            if is_sel:
                btn.setStyleSheet(
                    f'QPushButton{{background:{color};color:#fff;'
                    f'border:none;border-radius:6px;font-weight:700;}}'
                )
            else:
                btn.setStyleSheet(
                    f'QPushButton{{background:#f8fafc;color:{color};'
                    f'border:2px solid #e2e8f0;border-radius:6px;}}'
                    f'QPushButton:hover{{border-color:{color};background:{color}12;}}'
                )
            btn.clicked.connect(lambda _, v=i+1: self._select_likert(v))

            lbl = QLabel(label)
            lbl.setFont(font(8))
            lbl.setStyleSheet(f'color:{"#374151" if is_sel else "#9ca3af"};background:transparent;')
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setFixedWidth(72)

            col_lay.addWidget(btn, 0, Qt.AlignCenter)
            col_lay.addWidget(lbl, 0, Qt.AlignCenter)

            lklay.addLayout(col_lay)
            if i < 4:
                # Separator line between options
                sep = QFrame()
                sep.setFixedWidth(1)
                sep.setFixedHeight(40)
                sep.setStyleSheet('background:#e2e8f0;border:none;')
                lklay.addWidget(sep, 0, Qt.AlignCenter)

        lay.addWidget(likert_frame)
        lay.addStretch()
        return w

    def _select_likert(self, val: int):
        self._answers[self._current] = val
        self._update_grid()
        q = self._session[self._current]
        self._q_scroll.setWidget(self._build_q_widget(self._current, q, get_lang()))

    def _go_prev(self):
        if self._current > 0: self._show_question(self._current - 1)

    def _go_next(self):
        if self._current < len(self._session) - 1:
            self._show_question(self._current + 1)

    def _submit(self):
        from PyQt5.QtWidgets import QMessageBox
        unanswered = sum(1 for a in self._answers if a is None)
        if unanswered > 0:
            l = get_lang()
            msg = QMessageBox(self)
            msg.setWindowTitle('Belum Selesai' if l=='id' else 'Not Finished')
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                f'Masih ada {unanswered} pernyataan yang belum dijawab.\n'
                f'Selesaikan semua pernyataan sebelum submit!' if l=='id'
                else f'{unanswered} statements still unanswered.\n'
                f'Please answer all statements before submitting!'
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        duration = int(time.time() - self._start_ts)
        lang     = get_lang()
        uid      = self._user['id']
        answers  = [a if a is not None else 3 for a in self._answers]
        sid      = create_session(uid, 'bigfive', lang)
        finish_session(sid, duration)
        save_answers(sid, bf_answers_to_db_rows(self._session, answers))
        bf_result = score_bigfive(answers, self._session)
        save_scores(sid, bf_scores_to_db_rows(sid, bf_result))
        self.finished.emit(answers, self._session)

    def _on_lang(self, lang: str):
        self._submit_btn.setText('Submit Tes' if lang=='id' else 'Submit Test')
        self._prev_btn.setText('← Sebelumnya' if lang=='id' else '← Previous')
        self._next_btn.setText('Selanjutnya →' if lang=='id' else 'Next →')
        if self._session: self._show_question(self._current)