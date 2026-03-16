"""
ui/iq_result.py — Clean Professional
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.base import (
    D_BG2, D_BORDER, D_TEXT, D_MUTED,
    L_BG, L_SURFACE, L_BORDER, L_TEXT, L_MUTED,
    BLUE, GREEN, RED, GOLD, PURPLE, ORANGE, COG_COLORS,
    font, ghost_btn, card_shadow,
    section_header, ScrollPage, Card, AnimatedBar,
    AIExplanationBox, LangToggle,
    get_lang, LANG_BUS,
)
from core.knowledge_base import IQ_COGNITIVE_DOMAINS
from core.inference import score_iq, build_cognitive_profile

ACCENT = '#2563eb'

IQ_LEVEL_COLOR = {
    'Very Superior':  '#f59e0b',
    'Superior':       '#10b981',
    'High Average':   '#3b82f6',
    'Average':        '#6366f1',
    'Low Average':    '#f97316',
    'Below Average':  '#ef4444',
    'Well Below Avg': '#ef4444',
}


class IQResultPage(QWidget):
    go_home    = pyqtSignal()
    go_history = pyqtSignal()
    export_pdf = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._analysis = {}
        self._answers  = []
        self._session  = []
        self.setStyleSheet('background:#f8fafc;')
        self._build()
        if LANG_BUS:
            LANG_BUS.changed.connect(self._on_lang)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet('background:#fff;border-bottom:1px solid #e2e8f0;')
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(24, 0, 24, 0)

        home_btn = QPushButton('← Home')
        home_btn.setFont(font(10))
        home_btn.setFixedHeight(32)
        home_btn.setCursor(Qt.PointingHandCursor)
        home_btn.setStyleSheet(
            f'QPushButton{{background:#fff;color:{ACCENT};'
            f'border:1px solid #e2e8f0;border-radius:6px;padding:0 12px;}}'
            f'QPushButton:hover{{border-color:{ACCENT};}}'
        )
        home_btn.clicked.connect(self.go_home.emit)

        hist_btn = QPushButton('Riwayat')
        hist_btn.setFont(font(10))
        hist_btn.setFixedHeight(32)
        hist_btn.setCursor(Qt.PointingHandCursor)
        hist_btn.setStyleSheet(
            'QPushButton{background:#fff;color:#64748b;'
            'border:1px solid #e2e8f0;border-radius:6px;padding:0 12px;}'
            'QPushButton:hover{border-color:#94a3b8;}'
        )
        hist_btn.clicked.connect(self.go_history.emit)

        self._title_lbl = QLabel('IQ Assessment Results')
        self._title_lbl.setFont(font(13, True))
        self._title_lbl.setStyleSheet('color:#0f172a;')

        self._pdf_btn = QPushButton('Export PDF')
        self._pdf_btn.setFont(font(10, True))
        self._pdf_btn.setFixedHeight(32)
        self._pdf_btn.setCursor(Qt.PointingHandCursor)
        self._pdf_btn.setStyleSheet(
            f'QPushButton{{background:{ACCENT};color:#fff;'
            f'border:none;border-radius:6px;padding:0 14px;}}'
            f'QPushButton:hover{{background:#1d4ed8;}}'
            f'QPushButton:disabled{{background:#e2e8f0;color:#94a3b8;}}'
        )
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.setText('⏳ Generating...')
        self._pdf_btn.clicked.connect(lambda: self.export_pdf.emit(self._analysis))

        tlay.addWidget(home_btn)
        tlay.addSpacing(8)
        tlay.addWidget(hist_btn)
        tlay.addStretch()
        tlay.addWidget(self._title_lbl)
        tlay.addStretch()
        tlay.addWidget(self._pdf_btn)
        tlay.addSpacing(8)
        tlay.addWidget(LangToggle())
        root.addWidget(topbar)

        # Hero strip — compact, light
        self._hero = QFrame()
        self._hero.setFixedHeight(100)
        self._hero.setStyleSheet('background:#fff;border-bottom:1px solid #e2e8f0;')
        hlay = QHBoxLayout(self._hero)
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setAlignment(Qt.AlignCenter)

        center = QVBoxLayout()
        center.setSpacing(2)
        center.setAlignment(Qt.AlignCenter)

        self._iq_num = QLabel('—')
        self._iq_num.setFont(font(48, True))
        self._iq_num.setStyleSheet(f'color:{ACCENT};')
        self._iq_num.setAlignment(Qt.AlignCenter)

        self._iq_label_lbl = QLabel('')
        self._iq_label_lbl.setFont(font(12))
        self._iq_label_lbl.setStyleSheet('color:#64748b;')
        self._iq_label_lbl.setAlignment(Qt.AlignCenter)

        center.addWidget(self._iq_num)
        center.addWidget(self._iq_label_lbl)

        # Stats chips
        self._pct_chip   = self._make_stat('—', 'Persentil')
        self._correct_chip = self._make_stat('—', 'Benar')

        left_pad  = QWidget(); left_pad.setFixedWidth(160)
        right_pad = QWidget(); right_pad.setFixedWidth(160)

        rlay = QHBoxLayout(right_pad)
        rlay.setAlignment(Qt.AlignCenter)
        rlay.setSpacing(12)
        rlay.addWidget(self._pct_chip)
        rlay.addWidget(self._correct_chip)

        # Chips di bawah label, bukan di kanan
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        chips_row.setAlignment(Qt.AlignCenter)
        chips_row.addWidget(self._pct_chip)
        chips_row.addWidget(self._correct_chip)
        center.addLayout(chips_row)

        hlay.addStretch()
        hlay.addLayout(center)
        hlay.addStretch()
        root.addWidget(self._hero)

        # Scroll
        self._scroll = ScrollPage()
        root.addWidget(self._scroll, 1)

    def _make_stat(self, value: str, label: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignCenter)
        val = QLabel(value)
        val.setFont(font(16, True))
        val.setStyleSheet('color:#0f172a;')
        val.setAlignment(Qt.AlignRight)
        lbl = QLabel(label)
        lbl.setFont(font(8))
        lbl.setStyleSheet('color:#94a3b8;')
        lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(val)
        lay.addWidget(lbl)
        w._val = val
        return w

    def load_results(self, answers, session, user=None):
        self._answers = answers
        self._session = session
        iq_result = score_iq(answers, session)
        cognitive = build_cognitive_profile(answers, session)
        self._analysis = {
            **iq_result, 'cognitive': cognitive, 'user': user,
            'lang': get_lang(), 'iq_answers': answers,
            'iq_session': session, 'test_type': 'iq'
        }
        self._render()

    def _render(self):
        a = self._analysis
        l = get_lang()

        # Hero
        iq_val = a.get('iq', 0)
        label  = a.get('label', '')
        color  = IQ_LEVEL_COLOR.get(label, ACCENT)
        self._iq_num.setText(str(iq_val))
        self._iq_num.setStyleSheet(f'color:{color};')
        self._iq_label_lbl.setText(label)

        pct = a.get('percentile', 0)
        self._pct_chip._val.setText(f'{pct}th')
        correct = a.get('correct', 0)
        total   = a.get('total', 40)
        self._correct_chip._val.setText(f'{correct}/{total}')

        # Scroll content
        inner = self._scroll.inner_layout()
        while inner.count():
            item = inner.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Cognitive profile
        cog_title = 'Profil Kognitif' if l=='id' else 'Cognitive Profile'
        cog_sub   = 'Skor per domain kognitif (berbobot difficulty)' if l=='id' else 'Score per cognitive domain (difficulty weighted)'

        title_lbl = QLabel(cog_title)
        title_lbl.setFont(font(13, True))
        title_lbl.setStyleSheet('color:#0f172a;')
        inner.addWidget(title_lbl)

        sub_lbl = QLabel(cog_sub)
        sub_lbl.setFont(font(10))
        sub_lbl.setStyleSheet('color:#94a3b8;')
        inner.addWidget(sub_lbl)

        # Cognitive bars in clean table
        cog_frame = QFrame()
        cog_frame.setStyleSheet('background:#fff;border:1px solid #e2e8f0;border-radius:8px;')
        cog_lay = QVBoxLayout(cog_frame)
        cog_lay.setContentsMargins(20, 16, 20, 16)
        cog_lay.setSpacing(12)

        LVL_ID = {'excellent':'Sangat Unggul','high':'Tinggi','above_average':'Di Atas Rata-rata',
                  'average':'Rata-rata','below_average':'Di Bawah Rata-rata',
                  'developing':'Berkembang','needs_work':'Perlu Latihan'}
        LVL_EN = {'excellent':'Excellent','high':'High','above_average':'Above Average',
                  'average':'Average','below_average':'Below Average',
                  'developing':'Developing','needs_work':'Needs Work'}
        COG_ID = {'fluid':'Penalaran Cair','crystallized':'Kecerdasan Verbal',
                  'abstract':'Penalaran Abstrak','quantitative':'Penalaran Kuantitatif',
                  'spatial':'Kecerdasan Spasial'}
        COG_EN = {'fluid':'Fluid Reasoning','crystallized':'Verbal Intelligence',
                  'abstract':'Abstract Reasoning','quantitative':'Quantitative Reasoning',
                  'spatial':'Spatial Intelligence'}
        names = COG_ID if l=='id' else COG_EN
        lvls  = LVL_ID if l=='id' else LVL_EN

        for dom, d in sorted(a.get('cognitive',{}).items(), key=lambda x: x[1].get('rank',99)):
            col  = COG_COLORS.get(dom, ACCENT)
            name = names.get(dom, dom)
            pct  = d.get('score_pct', 0)
            lvl  = lvls.get(d.get('level','average'), '')

            row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setFont(font(10))
            name_lbl.setStyleSheet('color:#374151;')
            name_lbl.setFixedWidth(160)

            bar = AnimatedBar(pct, col, 8)

            pct_lbl = QLabel(f'{pct:.0f}%')
            pct_lbl.setFont(font(10, True))
            pct_lbl.setStyleSheet(f'color:{col};')
            pct_lbl.setFixedWidth(40)

            lvl_lbl = QLabel(lvl)
            lvl_lbl.setFont(font(9))
            lvl_lbl.setStyleSheet('color:#94a3b8;')
            lvl_lbl.setFixedWidth(120)

            row.addWidget(name_lbl)
            row.addWidget(bar, 1)
            row.addSpacing(8)
            row.addWidget(pct_lbl)
            row.addWidget(lvl_lbl)
            cog_lay.addLayout(row)

        inner.addWidget(cog_frame)

        # AI Box
        self._ai_box = AIExplanationBox()
        inner.addWidget(self._ai_box)
        self._load_ai_explanation()

        # Answer review
        rev_title = QLabel('Review Jawaban' if l=='id' else 'Answer Review')
        rev_title.setFont(font(13, True))
        rev_title.setStyleSheet('color:#0f172a;')
        inner.addWidget(rev_title)

        rev_frame = QFrame()
        rev_frame.setStyleSheet('background:#fff;border:1px solid #e2e8f0;border-radius:8px;')
        rev_lay = QVBoxLayout(rev_frame)
        rev_lay.setContentsMargins(0, 0, 0, 0)
        rev_lay.setSpacing(0)

        for i, q in enumerate(self._session):
            ans     = self._answers[i]
            correct = q['ans']
            is_ok   = ans is not None and ans == correct
            self._add_review_row(rev_lay, i, q, ans, correct, is_ok, l, i == len(self._session)-1)

        inner.addWidget(rev_frame)
        inner.addStretch()
        self._scroll.scroll_to_top()
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.setText('⏳ Generating...')

    def _add_review_row(self, lay, i, q, ans, correct, is_ok, lang, is_last):
        row = QFrame()
        border_bottom = '' if is_last else 'border-bottom:1px solid #f1f5f9;'
        row.setStyleSheet(
            f'QFrame{{background:{"#f0fdf4" if is_ok else "#fff7f7"};{border_bottom}}}'
        )
        rlay = QVBoxLayout(row)
        rlay.setContentsMargins(16, 10, 16, 10)
        rlay.setSpacing(4)

        q_lbl = QLabel(
            f'{"✓" if is_ok else "✗"}  Q{i+1}: {q["q"][:90]}{"..." if len(q["q"])>90 else ""}'
        )
        q_lbl.setFont(font(10))
        q_lbl.setStyleSheet(f'color:{"#15803d" if is_ok else "#dc2626"};')
        q_lbl.setWordWrap(True)
        rlay.addWidget(q_lbl)

        if not is_ok and ans is not None and ans != -1:
            opts = q.get('opts', [])
            your = opts[ans] if ans < len(opts) else '?'
            corr = opts[correct] if correct < len(opts) else '?'
            detail = QLabel(
                f'Kamu: {your}  ·  Benar: {corr}' if lang=='id'
                else f'You: {your}  ·  Correct: {corr}'
            )
            detail.setFont(font(9))
            detail.setStyleSheet('color:#94a3b8;')
            rlay.addWidget(detail)

        exp = q.get('explanation','')
        if exp:
            exp_lbl = QLabel(f'💡 {exp}')
            exp_lbl.setFont(font(9))
            exp_lbl.setStyleSheet('color:#78716c;font-style:italic;')
            exp_lbl.setWordWrap(True)
            rlay.addWidget(exp_lbl)

        lay.addWidget(row)

    def _load_ai_explanation(self):
        from core.ai_explainer import explain_iq_async, has_api_key
        self._ai_box.show()
        if not has_api_key():
            self._ai_box.set_error(
                'Tambahkan API key Gemini di sidebar untuk melihat interpretasi AI.'
                if get_lang()=='id' else
                'Add your Gemini API key in the sidebar to enable AI interpretation.'
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
        explain_iq_async(self._analysis, get_lang(), on_done=_on_done, on_error=_on_error)

    def _on_lang(self, _):
        if self._analysis: self._render()