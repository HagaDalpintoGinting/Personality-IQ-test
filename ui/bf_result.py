"""
ui/bf_result.py
────────────────────────────────────────────────────────────
Big Five Result page — OCEAN scores, radar, career, roadmap, AI
────────────────────────────────────────────────────────────
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from ui.base import (
    D_BG, D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, GOLD_LIGHT, PURPLE, ORANGE,
    TRAIT_COLORS, COG_COLORS,
    font, primary_btn, ghost_btn, card_shadow, divider,
    section_header, score_badge, ScrollPage, Card, AnimatedBar,
    RadarWidget, AIExplanationBox, LangToggle,
    get_lang, LANG_BUS, T,
)
from core.knowledge_base import BF_DIMENSIONS
from core.inference import run_full_analysis
class BFResultPage(QWidget):
    go_home    = pyqtSignal()
    go_history = pyqtSignal()
    export_pdf = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._analysis: dict = {}
        self._iq_data_fn     = None  # callback → (iq_answers, iq_session) or None
        self.setStyleSheet(f'background:{L_BG};')
        self._build()
        if LANG_BUS:
            LANG_BUS.changed.connect(self._on_lang)

    def set_iq_data_fn(self, fn):
        self._iq_data_fn = fn

    # ── Build ────────────────────────────────────────────────
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_sidebar())
        root.addWidget(self._make_content(), 1)

    def _make_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet(f'background:{D_BG2};border-right:1px solid {D_BORDER};')
        self._sb_lay = QVBoxLayout(sb)
        self._sb_lay.setContentsMargins(16, 24, 16, 24)
        self._sb_lay.setSpacing(10)

        # Radar chart
        self._radar = RadarWidget(size=180)
        self._sb_lay.addWidget(self._radar, 0, Qt.AlignCenter)
        self._sb_lay.addWidget(self._make_separator())

        # OCEAN scores mini
        self._trait_lbls: dict[str, QLabel] = {}
        for t in 'OCEAN':
            row = QHBoxLayout()
            name = QLabel(t)
            name.setFont(font(10, True))
            name.setStyleSheet(f'color:{TRAIT_COLORS[t]};')
            name.setFixedWidth(20)
            self._trait_lbls[t] = QLabel('–')
            self._trait_lbls[t].setFont(font(10))
            self._trait_lbls[t].setStyleSheet(f'color:{D_MUTED};')
            row.addWidget(name)
            row.addStretch()
            row.addWidget(self._trait_lbls[t])
            self._sb_lay.addLayout(row)

        self._sb_lay.addStretch()

        home_btn = ghost_btn('← Home', D_MUTED, 34)
        home_btn.clicked.connect(self.go_home.emit)
        hist_btn = ghost_btn('📋 History', GOLD, 34)
        hist_btn.clicked.connect(self.go_history.emit)
        self._pdf_btn = primary_btn('Export PDF', GREEN)
        self._pdf_btn.clicked.connect(lambda: self.export_pdf.emit(self._analysis))
        for w in [home_btn, hist_btn, self._pdf_btn]:
            self._sb_lay.addWidget(w)

        return sb

    def _make_separator(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet(f'background:{D_BORDER};border:none;')
        f.setFixedHeight(1)
        return f

    def _make_content(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background:{L_BG};')
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet(f'background:{L_SURFACE};border-bottom:1px solid {L_BORDER};')
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(24, 0, 24, 0)
        self._result_title = QLabel('Personality Results')
        self._result_title.setFont(font(13, True))
        self._result_title.setStyleSheet(f'color:{L_TEXT};')
        tlay.addWidget(self._result_title)
        tlay.addStretch()
        tlay.addWidget(LangToggle())
        lay.addWidget(topbar)

        self._scroll = ScrollPage()
        lay.addWidget(self._scroll, 1)
        return w

    # ── Load ─────────────────────────────────────────────────
    def load_results(self, answers: list, session: list, user: dict = None):
        self._bf_answers = answers
        self._bf_session = session

        iq_answers, iq_session = None, None
        if self._iq_data_fn:
            result = self._iq_data_fn()
            if result:
                iq_answers, iq_session = result

        self._analysis = run_full_analysis(
            answers, session, iq_answers, iq_session, get_lang()
        )
        self._analysis['user'] = user
        self._analysis['lang'] = get_lang()
        self._analysis['test_type'] = 'bigfive'
        self._render()

    def _render(self):
        a = self._analysis
        l = get_lang()
        bf  = a['bf_scores']
        pct = a['bf_pcts']

        # Update sidebar
        self._radar.set_scores(bf)
        for t in 'OCEAN':
            self._trait_lbls[t].setText(f'{bf[t]:.0f} ({pct[t]:.0f}th)')

        # Clear scroll
        inner = self._scroll.inner_layout()
        while inner.count():
            item = inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── Archetype hero card ──────────────────────────────
        arch = a.get('archetype', {})
        hero = QFrame()
        hero.setStyleSheet(
            f'QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,'
            f'stop:0 {BLUE},stop:1 {PURPLE});'
            f'border-radius:16px;padding:0;}}'
        )
        hero.setGraphicsEffect(card_shadow(20, 80))
        hlay = QVBoxLayout(hero)
        hlay.setContentsMargins(24, 20, 24, 20)
        hlay.setSpacing(6)

        tag_lbl = QLabel(arch.get('tag', ''))
        tag_lbl.setFont(font(10, True))
        tag_lbl.setStyleSheet('color:rgba(255,255,255,0.65);letter-spacing:2px;')

        name_lbl = QLabel(arch.get('name', ''))
        name_lbl.setFont(font(22, True))
        name_lbl.setStyleSheet('color:#fff;')

        desc_lbl = QLabel(arch.get('desc', ''))
        desc_lbl.setFont(font(11))
        desc_lbl.setStyleSheet('color:rgba(255,255,255,0.85);')
        desc_lbl.setWordWrap(True)

        for w in [tag_lbl, name_lbl, desc_lbl]:
            hlay.addWidget(w)
        inner.addWidget(hero)

        # ── OCEAN Scores ────────────────────────────────────
        inner.addWidget(section_header(
            'Profil Kepribadian OCEAN' if l=='id' else 'OCEAN Personality Profile',
        ))
        ocean_card = Card()
        for t in 'OCEAN':
            dim  = BF_DIMENSIONS[t]
            col  = TRAIT_COLORS[t]
            name = dim[f'short_{l}']
            s    = bf[t]
            p    = pct[t]
            lvl  = a['bf_result'][t][f'level_{l}']

            row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setFont(font(11, True))
            name_lbl.setStyleSheet(f'color:{col};')
            name_lbl.setFixedWidth(130)

            bar = AnimatedBar(s, col, 12)

            lvl_lbl = QLabel(lvl)
            lvl_lbl.setFont(font(9))
            lvl_lbl.setStyleSheet(f'color:{L_MUTED};')
            lvl_lbl.setFixedWidth(80)

            pct_lbl = QLabel(f'{p:.0f}th')
            pct_lbl.setFont(font(10, True))
            pct_lbl.setStyleSheet(f'color:{col};')
            pct_lbl.setFixedWidth(40)

            row.addWidget(name_lbl)
            row.addWidget(bar, 1)
            row.addSpacing(8)
            row.addWidget(lvl_lbl)
            row.addWidget(pct_lbl)
            ocean_card.layout().addLayout(row)

        inner.addWidget(ocean_card)

        # ── Combined Profile ─────────────────────────────────
        combined = a.get('combined', {})
        if combined.get('name'):
            comb_card = Card(bg='#f0f4ff', border=f'{BLUE}33')
            hl = QHBoxLayout()
            icon_lbl = QLabel('⚡')
            icon_lbl.setFont(font(20))
            title_block = QVBoxLayout()
            t1 = QLabel(combined['name'])
            t1.setFont(font(13, True))
            t1.setStyleSheet(f'color:{BLUE};')
            t2 = QLabel(combined.get('desc', ''))
            t2.setFont(font(11))
            t2.setStyleSheet(f'color:{L_TEXT};')
            t2.setWordWrap(True)
            t3 = QLabel(f'💡 {combined.get("action","")}')
            t3.setFont(font(10))
            t3.setStyleSheet(f'color:{L_MUTED};font-style:italic;')
            t3.setWordWrap(True)
            title_block.addWidget(t1)
            title_block.addWidget(t2)
            title_block.addWidget(t3)
            hl.addWidget(icon_lbl)
            hl.addSpacing(12)
            hl.addLayout(title_block, 1)
            comb_card.layout().addLayout(hl)
            inner.addWidget(comb_card)

        # ── Career Recommendations ────────────────────────────
        inner.addWidget(section_header(
            'Rekomendasi Karir' if l=='id' else 'Career Recommendations',
        ))
        career_card = Card()
        for c in a.get('careers', []):
            crow = QHBoxLayout()
            c_name = QLabel(c['name'])
            c_name.setFont(font(11))
            c_name.setStyleSheet(f'color:{L_TEXT};')
            c_name.setFixedWidth(200)
            bar = AnimatedBar(c['confidence'], GREEN, 10)
            conf_lbl = QLabel(f'{c["confidence"]}%')
            conf_lbl.setFont(font(10, True))
            conf_lbl.setStyleSheet(f'color:{GREEN};')
            conf_lbl.setFixedWidth(40)
            crow.addWidget(c_name)
            crow.addWidget(bar, 1)
            crow.addSpacing(8)
            crow.addWidget(conf_lbl)
            career_card.layout().addLayout(crow)
        inner.addWidget(career_card)

        # ── Learning Style ────────────────────────────────────
        ls_name   = a.get('learning_style_name', '')
        ls_detail = a.get('learning_style_detail', {})
        if ls_name:
            inner.addWidget(section_header(
                'Gaya Belajar' if l=='id' else 'Learning Style',
            ))
            ls_card = Card()
            ls_title = QLabel(f'📚 {ls_name}')
            ls_title.setFont(font(13, True))
            ls_title.setStyleSheet(f'color:{BLUE};')
            ls_card.layout().addWidget(ls_title)
            ls_desc = QLabel(ls_detail.get('desc', ''))
            ls_desc.setFont(font(11))
            ls_desc.setStyleSheet(f'color:{L_TEXT};')
            ls_desc.setWordWrap(True)
            ls_card.layout().addWidget(ls_desc)
            for tip in ls_detail.get('tips', []):
                tip_lbl = QLabel(f'• {tip}')
                tip_lbl.setFont(font(10))
                tip_lbl.setStyleSheet(f'color:{L_MUTED};')
                tip_lbl.setWordWrap(True)
                ls_card.layout().addWidget(tip_lbl)
            env = ls_detail.get('environment', '')
            if env:
                env_lbl = QLabel(f'🏢 {env}')
                env_lbl.setFont(font(10))
                env_lbl.setStyleSheet(f'color:{BLUE};font-style:italic;')
                ls_card.layout().addWidget(env_lbl)
            inner.addWidget(ls_card)

        # ── Blind Spots ───────────────────────────────────────
        blind = a.get('blind_spots', [])
        if blind:
            inner.addWidget(section_header(
                'Blind Spots & Area Perhatian' if l=='id' else 'Blind Spots & Areas of Attention',
            ))
            for b in blind:
                bs_card = Card(bg='#fff8f0', border=f'{ORANGE}33')
                bt = QLabel(f'⚠ {b["title"]}')
                bt.setFont(font(12, True))
                bt.setStyleSheet(f'color:{ORANGE};')
                bd = QLabel(b['desc'])
                bd.setFont(font(11))
                bd.setStyleSheet(f'color:{L_TEXT};')
                bd.setWordWrap(True)
                bm = QLabel(f'💡 {b["mitigation"]}')
                bm.setFont(font(10))
                bm.setStyleSheet(f'color:{L_MUTED};font-style:italic;')
                bm.setWordWrap(True)
                for w in [bt, bd, bm]:
                    bs_card.layout().addWidget(w)
                inner.addWidget(bs_card)

        # ── Roadmap ───────────────────────────────────────────
        roadmap = a.get('roadmap', [])
        if roadmap:
            inner.addWidget(section_header(
                'Roadmap Pengembangan Diri 3 Bulan' if l=='id' else '3-Month Development Roadmap',
            ))
            rm_colors = [BLUE, GREEN, GOLD]
            for m in roadmap:
                rm_card = Card()
                mhdr = QHBoxLayout()
                mbadge = QLabel(f'Bulan {m["month"]}' if l=='id' else f'Month {m["month"]}')
                mbadge.setFont(font(10, True))
                col = rm_colors[m['month']-1]
                mbadge.setStyleSheet(
                    f'color:{col};background:{col}18;border-radius:4px;padding:2px 8px;'
                )
                mfocus = QLabel(m['focus'])
                mfocus.setFont(font(12, True))
                mfocus.setStyleSheet(f'color:{L_TEXT};')
                mhdr.addWidget(mbadge)
                mhdr.addSpacing(8)
                mhdr.addWidget(mfocus)
                mhdr.addStretch()
                rm_card.layout().addLayout(mhdr)
                for act in m['actions']:
                    a_lbl = QLabel(f'→ {act}')
                    a_lbl.setFont(font(10))
                    a_lbl.setStyleSheet(f'color:{L_MUTED};')
                    a_lbl.setWordWrap(True)
                    rm_card.layout().addWidget(a_lbl)
                inner.addWidget(rm_card)

        # ── AI Explanation ────────────────────────────────────
        self._ai_box = AIExplanationBox()
        inner.addWidget(self._ai_box)
        self._load_ai_explanation()

        inner.addStretch()
        self._scroll.scroll_to_top()
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.setText('⏳ Generating...')

    def _load_ai_explanation(self):
        from core.ai_explainer import explain_bigfive_async, has_api_key
        self._ai_box.show()
        if not has_api_key():
            self._ai_box.set_error(
                'Tambahkan API key Gemini di Settings (⚙ API Key) untuk melihat interpretasi AI.'
                if get_lang()=='id' else
                'Add your Gemini API key in Settings (⚙ API Key) to enable AI interpretation.'
            )
            self._pdf_btn.setEnabled(True)
            self._pdf_btn.setText('Export PDF')
            return
        self._ai_box.set_loading()
        def _on_done(text):
            self._analysis['ai_text'] = text
            self._ai_box.set_text(text)
            self._pdf_btn.setEnabled(True)
            self._pdf_btn.setText('Export PDF')
        def _on_error(e):
            self._ai_box.set_error(e)
            self._pdf_btn.setEnabled(True)
            self._pdf_btn.setText('Export PDF')
        explain_bigfive_async(
            self._analysis, get_lang(),
            on_done=_on_done,
            on_error=_on_error,
        )

    def _on_lang(self, _):
        if self._analysis:
            self._render()