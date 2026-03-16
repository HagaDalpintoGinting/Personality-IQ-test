"""
ui/base.py
────────────────────────────────────────────────────────────
Shared constants, theme, language utilities, dan reusable
widgets yang dipakai di seluruh UI layer.
────────────────────────────────────────────────────────────
"""

import json
import random
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

# ══════════════════════════════════════════════════════════════
# PALETTE
# ══════════════════════════════════════════════════════════════
D_BG      = '#1e2130'
D_BG2     = '#262b3d'
D_BORDER  = '#353a52'
D_TEXT    = '#e8eaf2'
D_MUTED   = '#7b82a0'
L_BG      = '#f5f6fa'
L_SURFACE = '#ffffff'
L_BORDER  = '#e2e4ee'
L_TEXT    = '#1e2130'
L_MUTED   = '#8890aa'

GOLD       = '#f5a623'
GOLD_LIGHT = '#fff3dc'
GREEN      = '#27ae60'
RED        = '#e74c3c'
BLUE       = '#3b82f6'
PURPLE     = '#8b5cf6'
ORANGE     = '#f97316'

TRAIT_COLORS = {'O': ORANGE, 'C': BLUE, 'E': PURPLE, 'A': GREEN, 'N': RED}
COG_COLORS   = {
    'fluid':        ORANGE,
    'crystallized': PURPLE,
    'abstract':     BLUE,
    'quantitative': GREEN,
    'spatial':      GOLD,
}

# ══════════════════════════════════════════════════════════════
# LANGUAGE BUS
# ══════════════════════════════════════════════════════════════
class LangBus(QObject):
    changed = pyqtSignal(str)

LANG_BUS: LangBus | None = None
_CURRENT_LANG = ['id']
_I18N_CACHE: dict = {}

def init_lang_bus():
    global LANG_BUS
    LANG_BUS = LangBus()

def get_lang() -> str:
    return _CURRENT_LANG[0]

def set_lang(lang: str):
    _CURRENT_LANG[0] = lang
    if LANG_BUS:
        LANG_BUS.changed.emit(lang)

def _load_i18n(lang: str) -> dict:
    if lang not in _I18N_CACHE:
        path = Path(f'i18n/{lang}.json')
        if path.exists():
            with open(path, encoding='utf-8') as f:
                _I18N_CACHE[lang] = json.load(f)
        else:
            _I18N_CACHE[lang] = {}
    return _I18N_CACHE[lang]

def T(key: str, lang: str = None) -> str:
    """Lookup teks via dot-notation. e.g. T('home.title')"""
    l = lang or get_lang()
    data = _load_i18n(l)
    parts = key.split('.')
    node = data
    for p in parts:
        if isinstance(node, dict):
            node = node.get(p, '')
        else:
            return key
    return node if isinstance(node, str) else key


# ══════════════════════════════════════════════════════════════
# FONTS
# ══════════════════════════════════════════════════════════════
def font(size: int, bold: bool = False, family: str = 'Segoe UI') -> QFont:
    f = QFont(family, size)
    f.setBold(bold)
    return f


# ══════════════════════════════════════════════════════════════
# SHADOW EFFECT
# ══════════════════════════════════════════════════════════════
def card_shadow(blur: int = 18, opacity: int = 60) -> QGraphicsDropShadowEffect:
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, 4)
    s.setColor(QColor(0, 0, 0, opacity))
    return s


# ══════════════════════════════════════════════════════════════
# BASE PAGE (DualTone: dark sidebar + light content)
# ══════════════════════════════════════════════════════════════
class DualPage(QWidget):
    """
    Base halaman dengan layout sidebar (gelap) + konten (terang).
    Subclass override build_sidebar() dan build_content().
    """
    def __init__(self, parent=None, sidebar_width: int = 240):
        super().__init__(parent)
        self._sidebar_width = sidebar_width
        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        # Sidebar
        self._sidebar = QFrame()
        self._sidebar.setFixedWidth(sidebar_width)
        self._sidebar.setStyleSheet(f'background:{D_BG2}; border-right:1px solid {D_BORDER};')
        self._sidebar_lay = QVBoxLayout(self._sidebar)
        self._sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self._sidebar_lay.setSpacing(0)

        # Content area
        self._content_wrap = QFrame()
        self._content_wrap.setStyleSheet(f'background:{L_BG};')
        self._content_lay = QVBoxLayout(self._content_wrap)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        self._content_lay.setSpacing(0)

        self._root.addWidget(self._sidebar)
        self._root.addWidget(self._content_wrap, 1)

        self.build_sidebar(self._sidebar_lay)
        self.build_content(self._content_lay)

    def build_sidebar(self, layout: QVBoxLayout):
        """Override di subclass."""
        pass

    def build_content(self, layout: QVBoxLayout):
        """Override di subclass."""
        pass

    def sidebar_label(self, text: str, size: int = 11, bold: bool = False,
                      color: str = D_TEXT, align=Qt.AlignLeft) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font(size, bold))
        lbl.setStyleSheet(f'color:{color}; background:transparent;')
        lbl.setAlignment(align)
        lbl.setWordWrap(True)
        return lbl


# ══════════════════════════════════════════════════════════════
# ANIMATED PROGRESS BAR
# ══════════════════════════════════════════════════════════════
class AnimatedBar(QWidget):
    """Static progress bar — tanpa animasi untuk performa scroll."""
    def __init__(self, value: float = 0, color: str = BLUE,
                 height: int = 12, bg: str = '#e8eaef', parent=None):
        super().__init__(parent)
        self._value  = max(0.0, min(100.0, value))
        self._color  = color
        self._bg     = bg
        self._radius = height // 2
        self.setFixedHeight(height)

    def set_value(self, v: float):
        self._value = max(0.0, min(100.0, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self._radius
        w, h = self.width(), self.height()
        p.setBrush(QColor(self._bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, w, h, r, r)
        fw = int(w * self._value / 100)
        if fw > 0:
            p.setBrush(QColor(self._color))
            p.drawRoundedRect(0, 0, max(fw, h), h, r, r)
        p.end()


# ══════════════════════════════════════════════════════════════
# RADAR CHART
# ══════════════════════════════════════════════════════════════
class RadarWidget(QWidget):
    def __init__(self, scores: dict = None, parent=None, size: int = 220):
        super().__init__(parent)
        self._scores = scores or {}
        self.setFixedSize(size, size)
        self._traits = list('OCEAN')
        self._labels = {
            'id': {'O':'Terbuka','C':'Cermat','E':'Ekstrovert','A':'Ramah','N':'Neurotik'},
            'en': {'O':'Open','C':'Conscient.','E':'Extravert','A':'Agreeable','N':'Neurotic'},
        }

    def set_scores(self, scores: dict):
        self._scores = scores
        self.update()

    def paintEvent(self, _):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 30
        n = len(self._traits)
        step = 2 * math.pi / n
        offset = -math.pi / 2

        # Grid rings
        for ring in [0.25, 0.5, 0.75, 1.0]:
            p.setPen(QPen(QColor(D_BORDER), 1))
            p.setBrush(Qt.NoBrush)
            pts = []
            for i in range(n):
                angle = offset + i * step
                pts.append((cx + r * ring * math.cos(angle),
                             cy + r * ring * math.sin(angle)))
            for i in range(n):
                x1,y1 = pts[i]
                x2,y2 = pts[(i+1)%n]
                p.drawLine(int(x1),int(y1),int(x2),int(y2))

        # Spokes
        p.setPen(QPen(QColor(D_BORDER), 1))
        for i in range(n):
            angle = offset + i * step
            p.drawLine(cx, cy,
                       int(cx + r * math.cos(angle)),
                       int(cy + r * math.sin(angle)))

        # Fill polygon
        if self._scores:
            pts_fill = []
            for i, t in enumerate(self._traits):
                v = self._scores.get(t, 50) / 100
                angle = offset + i * step
                pts_fill.append((cx + r * v * math.cos(angle),
                                  cy + r * v * math.sin(angle)))
            path = QPainterPath()
            path.moveTo(pts_fill[0][0], pts_fill[0][1])
            for x, y in pts_fill[1:]:
                path.lineTo(x, y)
            path.closeSubpath()
            p.setBrush(QColor(BLUE + '55'))
            p.setPen(QPen(QColor(BLUE), 2))
            p.drawPath(path)

            # Dots
            p.setBrush(QColor(BLUE))
            p.setPen(Qt.NoPen)
            for x, y in pts_fill:
                p.drawEllipse(int(x)-4, int(y)-4, 8, 8)

        # Labels
        lang = get_lang()
        label_map = self._labels[lang]
        p.setFont(font(8, True))
        for i, t in enumerate(self._traits):
            angle = offset + i * step
            lx = cx + (r + 18) * math.cos(angle)
            ly = cy + (r + 18) * math.sin(angle)
            p.setPen(QColor(TRAIT_COLORS[t]))
            p.drawText(int(lx)-22, int(ly)-8, 44, 16,
                       Qt.AlignCenter, label_map[t])
        p.end()


# ══════════════════════════════════════════════════════════════
# CARD WIDGET
# ══════════════════════════════════════════════════════════════
class Card(QFrame):
    def __init__(self, parent=None, bg: str = L_SURFACE,
                 border: str = L_BORDER, radius: int = 12,
                 padding: int = 16):
        super().__init__(parent)
        self.setStyleSheet(
            f'QFrame{{background:{bg};border:1px solid {border};'
            f'border-radius:{radius}px;}}'
        )
        # Shadow dihapus - terlalu berat saat scroll banyak widget
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(padding, padding, padding, padding)
        self._lay.setSpacing(8)

    def layout(self) -> QVBoxLayout:
        return self._lay


# ══════════════════════════════════════════════════════════════
# SCROLLABLE PAGE (content area dengan scroll)
# ══════════════════════════════════════════════════════════════
class ScrollPage(QWidget):
    """Wrap content dalam QScrollArea dengan background L_BG."""
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(f'background:{L_BG};border:none;')
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.verticalScrollBar().setSingleStep(12)
        self._scroll.verticalScrollBar().setStyleSheet(
            'QScrollBar:vertical{width:6px;background:#e2e4ee;}'
            'QScrollBar::handle:vertical{background:#b0b8d0;border-radius:3px;min-height:30px;}'
            'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}'
        )

        self._inner = QWidget()
        self._inner.setStyleSheet(f'background:{L_BG};')
        self._inner_lay = QVBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(28, 24, 28, 24)
        self._inner_lay.setSpacing(16)

        self._scroll.setWidget(self._inner)
        lay.addWidget(self._scroll)

    def inner_layout(self) -> QVBoxLayout:
        return self._inner_lay

    def scroll_to_top(self):
        self._scroll.verticalScrollBar().setValue(0)


# ══════════════════════════════════════════════════════════════
# PRIMARY BUTTON
# ══════════════════════════════════════════════════════════════
def primary_btn(text: str, color: str = BLUE, text_color: str = '#fff',
                height: int = 44, font_size: int = 13) -> QPushButton:
    btn = QPushButton(text)
    btn.setFont(font(font_size, True))
    btn.setFixedHeight(height)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{color}; color:{text_color};
            border:none; border-radius:{height//2}px;
            padding:0 24px;
        }}
        QPushButton:hover {{ background:{_darken(color)}; }}
        QPushButton:pressed {{ background:{_darken(color, 30)}; }}
        QPushButton:disabled {{ background:#c0c4d0; color:#888; }}
    """)
    return btn


def ghost_btn(text: str, color: str = BLUE, height: int = 38) -> QPushButton:
    btn = QPushButton(text)
    btn.setFont(font(11))
    btn.setFixedHeight(height)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:transparent; color:{color};
            border:1.5px solid {color}; border-radius:{height//2}px;
            padding:0 20px;
        }}
        QPushButton:hover {{ background:{color}18; }}
    """)
    return btn


def _darken(hex_color: str, amount: int = 15) -> str:
    c = QColor(hex_color)
    return QColor(max(0, c.red()-amount),
                  max(0, c.green()-amount),
                  max(0, c.blue()-amount)).name()


# ══════════════════════════════════════════════════════════════
# SECTION HEADER
# ══════════════════════════════════════════════════════════════
def section_header(title: str, subtitle: str = '',
                   title_color: str = L_TEXT) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setFont(font(15, True))
    t.setStyleSheet(f'color:{title_color};')
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setFont(font(11))
        s.setStyleSheet(f'color:{L_MUTED};')
        lay.addWidget(s)
    return w


# ══════════════════════════════════════════════════════════════
# SCORE BADGE
# ══════════════════════════════════════════════════════════════
def score_badge(value: str, label: str, color: str = BLUE) -> QWidget:
    w = QFrame()
    w.setStyleSheet(
        f'QFrame{{background:{color}18;border:1.5px solid {color}44;'
        f'border-radius:10px;padding:8px 14px;}}'
    )
    lay = QVBoxLayout(w)
    lay.setContentsMargins(12, 8, 12, 8)
    lay.setSpacing(2)

    val = QLabel(value)
    val.setFont(font(22, True))
    val.setStyleSheet(f'color:{color};')
    val.setAlignment(Qt.AlignCenter)

    lbl = QLabel(label)
    lbl.setFont(font(10))
    lbl.setStyleSheet(f'color:{L_MUTED};')
    lbl.setAlignment(Qt.AlignCenter)

    lay.addWidget(val)
    lay.addWidget(lbl)
    return w


# ══════════════════════════════════════════════════════════════
# DIVIDER
# ══════════════════════════════════════════════════════════════
def divider(color: str = L_BORDER) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f'background:{color};border:none;')
    return line


# ══════════════════════════════════════════════════════════════
# LANG TOGGLE BUTTON
# ══════════════════════════════════════════════════════════════
class LangToggle(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(72, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_text()
        self.clicked.connect(self._toggle)
        self.setStyleSheet(f"""
            QPushButton {{
                background:{D_BG};color:{D_TEXT};
                border:1px solid {D_BORDER};border-radius:14px;
                font-weight:bold;font-size:11px;
            }}
            QPushButton:hover{{background:{D_BORDER};}}
        """)

    def _toggle(self):
        set_lang('en' if get_lang() == 'id' else 'id')
        self._update_text()

    def _update_text(self):
        self.setText('🇮🇩 ID' if get_lang() == 'id' else '🇺🇸 EN')


# ══════════════════════════════════════════════════════════════
# AI EXPLANATION BOX
# ══════════════════════════════════════════════════════════════
class AIExplanationBox(QFrame):
    """Kotak narasi AI — teks penuh dengan scroll."""
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QTextEdit
        self.setStyleSheet(
            f'QFrame{{background:#f0f4ff;border:1.5px solid {BLUE}33;border-radius:12px;}}'
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Header
        header = QHBoxLayout()
        icon  = QLabel('✨')
        icon.setFont(font(14))
        title = QLabel('AI Interpretation')
        title.setFont(font(11, True))
        title.setStyleSheet(f'color:{BLUE};')
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        self._spinner = QLabel('')
        self._spinner.setFont(font(10))
        self._spinner.setStyleSheet(f'color:{L_MUTED};')
        header.addWidget(self._spinner)
        lay.addLayout(header)

        # Text area — QTextEdit read-only supaya teks panjang tampil penuh
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(font(11))
        self._text.setFrameShape(QFrame.NoFrame)
        self._text.setStyleSheet(
            f'background:transparent;color:{L_TEXT};border:none;padding:4px 0;'
        )
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self._text.setMinimumHeight(60)
        self._text.document().contentsChanged.connect(self._adjust_height)
        lay.addWidget(self._text)

    def _adjust_height(self):
        """Auto-resize height sesuai konten teks."""
        self._text.document().setTextWidth(self._text.viewport().width())
        doc_height = int(self._text.document().size().height())
        self._text.setMinimumHeight(doc_height + 16)
        self._text.setMaximumHeight(doc_height + 16)

    def set_loading(self):
        self._spinner.setText('⟳ loading')
        self._text.setStyleSheet(
            f'background:transparent;color:{L_MUTED};border:none;font-style:italic;'
        )
        self._text.setPlainText('Generating personalized interpretation...')

    def set_text(self, text: str):
        self._spinner.setText('✓')
        self._text.setStyleSheet(
            f'background:transparent;color:{L_TEXT};border:none;'
        )
        self._text.setPlainText(text)

    def set_error(self, msg: str):
        self._spinner.setText('⚠')
        self._text.setStyleSheet(
            f'background:transparent;color:{RED};border:none;font-style:italic;'
        )
        self._text.setPlainText(msg)


# ══════════════════════════════════════════════════════════════
# COUNTDOWN TIMER WIDGET
# ══════════════════════════════════════════════════════════════
class CountdownTimer(QWidget):
    timeout = pyqtSignal()

    def __init__(self, total_seconds: int = 1200, parent=None):
        super().__init__(parent)
        self._total   = total_seconds
        self._remaining = total_seconds
        self._running = False
        self.setFixedSize(80, 80)

        self._qtimer = QTimer(self)
        self._qtimer.setInterval(1000)
        self._qtimer.timeout.connect(self._tick)

    def start(self):
        self._running = True
        self._qtimer.start()

    def stop(self):
        self._running = False
        self._qtimer.stop()

    def reset(self, total_seconds: int = None):
        self.stop()
        if total_seconds:
            self._total = total_seconds
        self._remaining = self._total
        self.update()

    def _tick(self):
        if self._remaining > 0:
            self._remaining -= 1
            self.update()
        else:
            self.stop()
            self.timeout.emit()

    def remaining(self) -> int:
        return self._remaining

    def paintEvent(self, _):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w//2, h//2, min(w,h)//2 - 4

        # Background circle
        p.setPen(QPen(QColor(D_BORDER), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

        # Progress arc
        ratio   = self._remaining / self._total if self._total else 0
        color   = GREEN if ratio > 0.5 else (GOLD if ratio > 0.2 else RED)
        p.setPen(QPen(QColor(color), 4, Qt.SolidLine, Qt.RoundCap))
        span    = int(ratio * 360 * 16)
        p.drawArc(cx-r+3, cy-r+3, (r-3)*2, (r-3)*2, 90*16, span)

        # Time text
        m, s    = divmod(self._remaining, 60)
        p.setFont(font(11, True))
        p.setPen(QColor(D_TEXT))
        p.drawText(0, 0, w, h, Qt.AlignCenter, f'{m:02d}:{s:02d}')
        p.end()