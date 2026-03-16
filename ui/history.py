"""
ui/history.py
────────────────────────────────────────────────────────────
Halaman riwayat tes:
  • Daftar sesi sebelumnya (BF + IQ)
  • Trend chart per dimensi (skor dari waktu ke waktu)
  • Statistik populasi vs skor user
────────────────────────────────────────────────────────────
"""

import math
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QTabWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

from ui.base import (
    D_BG, D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, PURPLE, ORANGE,
    TRAIT_COLORS, COG_COLORS,
    font, primary_btn, ghost_btn, card_shadow, divider,
    section_header, score_badge, ScrollPage, Card,
    get_lang, LANG_BUS, T,
)
from core.database import (
    get_sessions, get_scores, get_score_history,
    get_all_population_stats, get_total_users, get_total_sessions,
)


# ══════════════════════════════════════════════════════════════
# MINI TREND LINE WIDGET
# ══════════════════════════════════════════════════════════════
class TrendLine(QWidget):
    """Simple sparkline untuk satu dimensi."""
    def __init__(self, points: list[float], color: str = BLUE,
                 width: int = 180, height: int = 48, parent=None):
        super().__init__(parent)
        self._pts   = points
        self._color = color
        self.setFixedSize(width, height)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pad = 6

        if len(self._pts) < 2:
            # Single dot
            if self._pts:
                p.setBrush(QColor(self._color))
                p.setPen(Qt.NoPen)
                p.drawEllipse(w//2-4, h//2-4, 8, 8)
            p.end()
            return

        mn, mx = min(self._pts), max(self._pts)
        rng = max(mx - mn, 10)

        def px(i): return pad + int((w - 2*pad) * i / (len(self._pts)-1))
        def py(v): return h - pad - int((h - 2*pad) * (v - mn) / rng)

        # Line
        pen = QPen(QColor(self._color), 2)
        p.setPen(pen)
        for i in range(len(self._pts)-1):
            p.drawLine(px(i), py(self._pts[i]), px(i+1), py(self._pts[i+1]))

        # Dots
        p.setBrush(QColor(self._color))
        p.setPen(Qt.NoPen)
        for i, v in enumerate(self._pts):
            p.drawEllipse(px(i)-3, py(v)-3, 6, 6)

        # Latest value label
        p.setFont(font(8, True))
        p.setPen(QColor(self._color))
        last_v = self._pts[-1]
        p.drawText(w-28, py(last_v)-8, 28, 16, Qt.AlignRight, f'{last_v:.0f}')
        p.end()


# ══════════════════════════════════════════════════════════════
# SESSION ROW CARD
# ══════════════════════════════════════════════════════════════
class SessionRow(QFrame):
    clicked = pyqtSignal(int)  # session_id

    def __init__(self, session: dict, scores: dict, parent=None):
        super().__init__(parent)
        self._sid = session['id']
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f'QFrame{{background:{L_SURFACE};border:1px solid {L_BORDER};'
            f'border-radius:10px;padding:12px;}}'
            f'QFrame:hover{{border-color:{BLUE};background:#f0f4ff;}}'
        )
        self.setGraphicsEffect(card_shadow(10, 30))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)

        # Type badge
        test_type = session.get('test_type', '')
        badge_color = BLUE if 'iq' in test_type else PURPLE
        badge_text  = 'IQ' if test_type == 'iq' else ('BF' if test_type == 'bigfive' else '⚡')
        badge = QLabel(badge_text)
        badge.setFont(font(10, True))
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f'background:{badge_color}22;color:{badge_color};'
            f'border-radius:18px;border:1.5px solid {badge_color}44;'
        )
        lay.addWidget(badge)
        lay.addSpacing(10)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)
        date_str = session.get('taken_at', '')[:16].replace('T', ' ')
        dt_lbl = QLabel(date_str)
        dt_lbl.setFont(font(11, True))
        dt_lbl.setStyleSheet(f'color:{L_TEXT};')

        lang_lbl = QLabel(session.get('lang', 'id').upper())
        lang_lbl.setFont(font(9))
        lang_lbl.setStyleSheet(f'color:{L_MUTED};')

        info.addWidget(dt_lbl)
        info.addWidget(lang_lbl)
        lay.addLayout(info)
        lay.addStretch()

        # Score preview
        score_row = QHBoxLayout()
        score_row.setSpacing(8)
        if 'IQ' in scores:
            iq_val = scores['IQ']
            iq_lbl = QLabel(f"IQ {iq_val['normalized']:.0f}")
            iq_lbl.setFont(font(12, True))
            iq_lbl.setStyleSheet(f'color:{BLUE};')
            score_row.addWidget(iq_lbl)

        for t in 'OCEAN':
            if t in scores:
                lbl = QLabel(f"{t}:{scores[t]['normalized']:.0f}")
                lbl.setFont(font(9))
                lbl.setStyleSheet(f'color:{TRAIT_COLORS[t]};')
                score_row.addWidget(lbl)

        lay.addLayout(score_row)

        # Arrow
        arr = QLabel('›')
        arr.setFont(font(18))
        arr.setStyleSheet(f'color:{L_MUTED};')
        lay.addWidget(arr)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._sid)


# ══════════════════════════════════════════════════════════════
# TREND SECTION
# ══════════════════════════════════════════════════════════════
class TrendSection(QWidget):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # BF trend
        self._bf_card = self._make_bf_trend()
        lay.addWidget(self._bf_card)

        # IQ trend
        self._iq_card = self._make_iq_trend()
        lay.addWidget(self._iq_card)

    def _make_bf_trend(self) -> QFrame:
        card = Card()
        l = get_lang()
        title = QLabel('Tren Big Five' if l=='id' else 'Big Five Trend')
        title.setFont(font(13, True))
        title.setStyleSheet(f'color:{L_TEXT};')
        card.layout().addWidget(title)
        card.layout().addWidget(divider())

        grid = QHBoxLayout()
        grid.setSpacing(16)

        for t in 'OCEAN':
            history = get_score_history(self._user_id, t, 'bigfive', limit=10)
            pts     = [h['normalized'] for h in history]
            col     = TRAIT_COLORS[t]

            col_w = QVBoxLayout()
            col_w.setSpacing(4)
            col_w.setAlignment(Qt.AlignTop)

            trait_lbl = QLabel(t)
            trait_lbl.setFont(font(10, True))
            trait_lbl.setStyleSheet(f'color:{col};')
            trait_lbl.setAlignment(Qt.AlignCenter)

            if pts:
                trend = TrendLine(pts, col, 120, 40)
                last_lbl = QLabel(f'{pts[-1]:.0f}')
            else:
                trend = QLabel('–')
                trend.setAlignment(Qt.AlignCenter)
                trend.setStyleSheet(f'color:{L_MUTED};')
                last_lbl = QLabel('no data')

            last_lbl.setFont(font(9))
            last_lbl.setStyleSheet(f'color:{L_MUTED};')
            last_lbl.setAlignment(Qt.AlignCenter)

            col_w.addWidget(trait_lbl)
            col_w.addWidget(trend)
            col_w.addWidget(last_lbl)

            col_frame = QFrame()
            col_frame.setLayout(col_w)
            grid.addWidget(col_frame)

        w = QWidget()
        w.setLayout(grid)
        card.layout().addWidget(w)
        return card

    def _make_iq_trend(self) -> QFrame:
        card = Card()
        l = get_lang()
        title = QLabel('Tren IQ' if l=='id' else 'IQ Trend')
        title.setFont(font(13, True))
        title.setStyleSheet(f'color:{L_TEXT};')
        card.layout().addWidget(title)
        card.layout().addWidget(divider())

        history = get_score_history(self._user_id, 'IQ', 'iq', limit=10)
        pts     = [h['normalized'] for h in history]

        if pts:
            trend = TrendLine(pts, BLUE, 400, 60)
            last_lbl = QLabel(f'Latest: {pts[-1]:.0f} (weighted %)')
        else:
            trend = QLabel('No IQ history yet.' if l=='id' else 'No IQ history yet.')
            trend.setStyleSheet(f'color:{L_MUTED};font-style:italic;')
            last_lbl = QLabel('')

        last_lbl.setFont(font(10))
        last_lbl.setStyleSheet(f'color:{L_MUTED};')

        card.layout().addWidget(trend)
        card.layout().addWidget(last_lbl)
        return card


# ══════════════════════════════════════════════════════════════
# STATS SECTION (vs populasi)
# ══════════════════════════════════════════════════════════════
class StatsSection(QWidget):
    def __init__(self, user_id: int, latest_scores: dict, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._latest  = latest_scores
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        l = get_lang()

        # Global stats
        n_users    = get_total_users()
        n_sessions = get_total_sessions()
        pop_stats  = get_all_population_stats('bigfive')

        global_card = Card()
        g_title = QLabel('Statistik Populasi Aplikasi' if l=='id' else 'App Population Stats')
        g_title.setFont(font(13, True))
        g_title.setStyleSheet(f'color:{L_TEXT};')
        global_card.layout().addWidget(g_title)
        global_card.layout().addWidget(divider())

        stats_row = QHBoxLayout()
        for val, lbl in [
            (str(n_users), 'Total Pengguna' if l=='id' else 'Total Users'),
            (str(n_sessions), 'Total Sesi' if l=='id' else 'Total Sessions'),
        ]:
            badge_w = score_badge(val, lbl, BLUE)
            stats_row.addWidget(badge_w)
        stats_row.addStretch()
        global_card.layout().addLayout(stats_row)
        lay.addWidget(global_card)

        # Per-trait comparison
        if self._latest and pop_stats:
            cmp_card = Card()
            cmp_title = QLabel('Kamu vs Rata-rata Pengguna' if l=='id' else 'You vs App Average')
            cmp_title.setFont(font(13, True))
            cmp_title.setStyleSheet(f'color:{L_TEXT};')
            cmp_card.layout().addWidget(cmp_title)
            cmp_card.layout().addWidget(divider())

            from ui.base import AnimatedBar
            for t in 'OCEAN':
                if t not in self._latest or t not in pop_stats:
                    continue
                user_score = self._latest[t]['normalized']
                avg_score  = pop_stats[t]['mean']
                col        = TRAIT_COLORS[t]

                row = QHBoxLayout()
                t_lbl = QLabel(t)
                t_lbl.setFont(font(10, True))
                t_lbl.setStyleSheet(f'color:{col};')
                t_lbl.setFixedWidth(20)

                bar_you = AnimatedBar(user_score, col, 10)
                bar_avg = AnimatedBar(avg_score, L_MUTED, 6, '#e0e2ea')

                you_lbl = QLabel(f'{user_score:.0f}')
                you_lbl.setFont(font(10, True))
                you_lbl.setStyleSheet(f'color:{col};')
                you_lbl.setFixedWidth(30)

                diff = user_score - avg_score
                diff_lbl = QLabel(f'{"+" if diff>=0 else ""}{diff:.0f}')
                diff_lbl.setFont(font(9))
                diff_lbl.setStyleSheet(f'color:{GREEN if diff>=0 else RED};')
                diff_lbl.setFixedWidth(32)

                bars = QVBoxLayout()
                bars.setSpacing(2)
                bars.addWidget(bar_you)
                bars.addWidget(bar_avg)

                row.addWidget(t_lbl)
                row.addLayout(bars, 1)
                row.addWidget(you_lbl)
                row.addWidget(diff_lbl)
                cmp_card.layout().addLayout(row)

            lay.addWidget(cmp_card)


# ══════════════════════════════════════════════════════════════
# HISTORY PAGE
# ══════════════════════════════════════════════════════════════
class HistoryPage(QWidget):
    open_session = pyqtSignal(int, str)  # session_id, test_type
    back         = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user: dict | None = None
        self.setStyleSheet(f'background:{L_BG};')
        self._build()
        if LANG_BUS:
            LANG_BUS.changed.connect(self._on_lang)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self._topbar = self._make_topbar()
        root.addWidget(self._topbar)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:none;background:{L_BG};}}
            QTabBar::tab {{
                background:{L_SURFACE};color:{L_MUTED};
                padding:10px 24px;border:none;
                border-bottom:2px solid transparent;
                font-size:12px;font-weight:bold;
            }}
            QTabBar::tab:selected {{color:{BLUE};border-bottom-color:{BLUE};}}
            QTabBar::tab:hover {{color:{L_TEXT};}}
        """)
        root.addWidget(self._tabs, 1)

    def _make_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f'background:{L_SURFACE};border-bottom:1px solid {L_BORDER};')
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        back_btn = ghost_btn('← Back', BLUE, 34)
        back_btn.clicked.connect(self.back.emit)

        self._page_title = QLabel()
        self._page_title.setFont(font(14, True))
        self._page_title.setStyleSheet(f'color:{L_TEXT};')

        lay.addWidget(back_btn)
        lay.addSpacing(12)
        lay.addWidget(self._page_title)
        lay.addStretch()
        return bar

    def load_user(self, user: dict):
        self._user = user
        self._refresh()

    def _refresh(self):
        if not self._user:
            return
        l = get_lang()
        uid = self._user['id']
        name = self._user['name']

        self._page_title.setText(
            f'Riwayat — {name}' if l=='id' else f'History — {name}'
        )

        # Clear tabs
        while self._tabs.count() > 0:
            self._tabs.removeTab(0)

        # Tab 1: Sessions list
        sessions_tab = self._make_sessions_tab(uid, l)
        self._tabs.addTab(sessions_tab, '📋 Sesi' if l=='id' else '📋 Sessions')

        # Tab 2: Trends
        trend_scroll = ScrollPage()
        trend_sec    = TrendSection(uid)
        trend_scroll.inner_layout().addWidget(trend_sec)
        trend_scroll.inner_layout().addStretch()
        self._tabs.addTab(trend_scroll, '📈 Tren' if l=='id' else '📈 Trends')

        # Tab 3: Stats
        latest_bf_sessions = get_sessions(uid, 'bigfive', 1)
        latest_scores = {}
        if latest_bf_sessions:
            latest_scores = get_scores(latest_bf_sessions[0]['id'])

        stats_scroll = ScrollPage()
        stats_sec    = StatsSection(uid, latest_scores)
        stats_scroll.inner_layout().addWidget(stats_sec)
        stats_scroll.inner_layout().addStretch()
        self._tabs.addTab(stats_scroll, '📊 Statistik' if l=='id' else '📊 Stats')

    def _make_sessions_tab(self, user_id: int, lang: str) -> QWidget:
        scroll = ScrollPage()
        sessions = get_sessions(user_id, limit=30)

        if not sessions:
            empty = QLabel('Belum ada riwayat tes.' if lang=='id' else 'No test history yet.')
            empty.setFont(font(13))
            empty.setStyleSheet(f'color:{L_MUTED};font-style:italic;')
            empty.setAlignment(Qt.AlignCenter)
            scroll.inner_layout().addWidget(empty)
        else:
            for s in sessions:
                scores = get_scores(s['id'])
                row = SessionRow(s, scores)
                row.clicked.connect(
                    lambda sid=s['id'], tt=s['test_type']:
                    self.open_session.emit(sid, tt)
                )
                scroll.inner_layout().addWidget(row)

        scroll.inner_layout().addStretch()
        return scroll

    def _on_lang(self, _):
        self._refresh()