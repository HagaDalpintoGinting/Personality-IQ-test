"""
report/pdf_generator.py — Professional PDF Templates
IQ Test Summary + Big Five Personality Summary
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Wedge, Circle, Line, String
from reportlab.graphics import renderPDF
from datetime import datetime
import math

# ── Palette ────────────────────────────────────────────────────────────────
C_DARK    = colors.HexColor('#1e2130')
C_DARK2   = colors.HexColor('#262b3d')
C_LIGHT   = colors.HexColor('#f5f6fa')
C_WHITE   = colors.white
C_GOLD    = colors.HexColor('#f5a623')
C_BLUE    = colors.HexColor('#3b82f6')
C_GREEN   = colors.HexColor('#27ae60')
C_RED     = colors.HexColor('#e74c3c')
C_PURPLE  = colors.HexColor('#8b5cf6')
C_ORANGE  = colors.HexColor('#f97316')
C_MUTED   = colors.HexColor('#8890aa')
C_BORDER  = colors.HexColor('#e2e4ee')
C_BG      = colors.HexColor('#f8f9fc')

TRAIT_HEX  = {'O':'#f97316','C':'#3b82f6','E':'#8b5cf6','A':'#27ae60','N':'#e74c3c'}
TRAIT_ID   = {'O':'Keterbukaan','C':'Ketelitian','E':'Ekstraversi','A':'Keramahan','N':'Neurotisisme'}
TRAIT_EN   = {'O':'Openness','C':'Conscientiousness','E':'Extraversion','A':'Agreeableness','N':'Neuroticism'}
TRAIT_DESC_ID = {
    'O': 'Imajinasi, kreativitas, dan keterbukaan terhadap pengalaman baru.',
    'C': 'Keteraturan, disiplin, dan kemampuan menyelesaikan tugas.',
    'E': 'Sosiabilitas, antusiasme, dan energi dalam interaksi sosial.',
    'A': 'Empati, kerja sama, dan kepercayaan terhadap orang lain.',
    'N': 'Kecenderungan merasakan emosi negatif dan stres.',
}
TRAIT_DESC_EN = {
    'O': 'Imagination, creativity, and openness to new experiences.',
    'C': 'Organization, discipline, and ability to complete tasks.',
    'E': 'Sociability, enthusiasm, and energy in social interactions.',
    'A': 'Empathy, cooperation, and trust in others.',
    'N': 'Tendency to experience negative emotions and stress.',
}
COG_HEX   = {'fluid':'#f97316','crystallized':'#8b5cf6','abstract':'#3b82f6','quantitative':'#27ae60','spatial':'#f5a623'}
COG_ID    = {'fluid':'Penalaran Cair','crystallized':'Kecerdasan Verbal','abstract':'Penalaran Abstrak','quantitative':'Penalaran Kuantitatif','spatial':'Kecerdasan Spasial'}
COG_EN    = {'fluid':'Fluid Reasoning','crystallized':'Verbal Intelligence','abstract':'Abstract Reasoning','quantitative':'Quantitative Reasoning','spatial':'Spatial Intelligence'}
LVL_ID    = {'excellent':'Sangat Unggul','high':'Tinggi','above_average':'Di Atas Rata-rata','average':'Rata-rata','below_average':'Di Bawah Rata-rata','developing':'Berkembang','needs_work':'Perlu Latihan'}
LVL_EN    = {'excellent':'Excellent','high':'High','above_average':'Above Average','average':'Average','below_average':'Below Average','developing':'Developing','needs_work':'Needs Work'}
IQ_COLORS = {'Very Superior':('#f5a623','#1e2130'),'Superior':('#27ae60','#ffffff'),'High Average':('#3b82f6','#ffffff'),'Average':('#8b5cf6','#ffffff'),'Low Average':('#f97316','#ffffff'),'Below Average':('#e74c3c','#ffffff'),'Well Below Avg':('#e74c3c','#ffffff')}

W  = A4[0] - 40*mm
PW = A4[0]
PH = A4[1]


# ══════════════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════════════
def _styles():
    b = getSampleStyleSheet()
    def ms(n, **kw): return ParagraphStyle(n, parent=b['Normal'], **kw)
    return {
        'h1':       ms('h1', fontSize=20, fontName='Helvetica-Bold', textColor=C_DARK, spaceBefore=10, spaceAfter=6, leading=26),
        'h2':       ms('h2', fontSize=14, fontName='Helvetica-Bold', textColor=C_DARK, spaceBefore=8,  spaceAfter=4, leading=20),
        'h3':       ms('h3', fontSize=11, fontName='Helvetica-Bold', textColor=C_DARK, spaceBefore=6,  spaceAfter=3),
        'body':     ms('bd', fontSize=10, textColor=C_DARK,   leading=17, spaceAfter=6,  alignment=TA_JUSTIFY),
        'muted':    ms('mt', fontSize=9,  textColor=C_MUTED,  leading=14, spaceAfter=4),
        'small':    ms('sm', fontSize=8,  textColor=C_MUTED,  leading=12),
        'disc':     ms('di', fontSize=8,  textColor=C_MUTED,  leading=12, alignment=TA_CENTER),
        'correct':  ms('ok', fontSize=9,  textColor=C_GREEN,  leading=14),
        'wrong':    ms('wr', fontSize=9,  textColor=C_RED,    leading=14),
        'tip':      ms('tp', fontSize=9,  textColor=colors.HexColor('#7a5200'), leading=14, backColor=colors.HexColor('#fff8e6'), borderPadding=6, spaceAfter=4),
        'white':    ms('wh', fontSize=10, textColor=C_WHITE,  leading=15),
        'white_b':  ms('wb', fontSize=13, fontName='Helvetica-Bold', textColor=C_WHITE, leading=18),
        'tag':      ms('tg', fontSize=8,  fontName='Helvetica-Bold', textColor=C_GOLD, letterSpacing=2),
        'center':   ms('c',  fontSize=10, textColor=C_DARK,   alignment=TA_CENTER),
        'action':   ms('ac', fontSize=9,  textColor=C_DARK,   leading=14, leftIndent=10, spaceAfter=2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DRAWING HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _bar(pct: float, hex_color: str, w=None, h=10) -> Drawing:
    """Progress bar dengan rounded corners dan label %."""
    bw = w or W
    d  = Drawing(bw, h + 2)
    # Track
    d.add(Rect(0, 1, bw, h, fillColor=C_BORDER, strokeColor=None, rx=h//2, ry=h//2))
    # Fill
    fw = max(h, int(bw * min(pct,100) / 100))
    d.add(Rect(0, 1, fw, h, fillColor=colors.HexColor(hex_color), strokeColor=None, rx=h//2, ry=h//2))
    return d

def _donut(pct: float, hex_color: str, size=60) -> Drawing:
    """Mini donut chart untuk skor."""
    d   = Drawing(size, size)
    cx  = cy = size / 2
    r   = size * 0.38
    t   = size * 0.22
    # Background circle
    d.add(Wedge(cx, cy, r, 0, 360, fillColor=C_BORDER, strokeColor=None, strokeWidth=0))
    d.add(Wedge(cx, cy, r-t, 0, 360, fillColor=C_WHITE, strokeColor=None, strokeWidth=0))
    # Fill arc
    deg = pct * 3.6
    if deg > 0:
        d.add(Wedge(cx, cy, r, 90, 90-deg, fillColor=colors.HexColor(hex_color), strokeColor=None, strokeWidth=0))
        d.add(Wedge(cx, cy, r-t, 90, 90-deg, fillColor=C_WHITE, strokeColor=None, strokeWidth=0))
    # Center text
    d.add(String(cx, cy-4, f'{pct:.0f}', fontSize=int(size*0.22),
                 fontName='Helvetica-Bold', fillColor=colors.HexColor(hex_color),
                 textAnchor='middle'))
    return d

def _section_bar(story, title: str, hex_color: str):
    """Section header — accent color bar."""
    t = Table([[Paragraph(f'<b>{title}</b>',
        ParagraphStyle('sh', fontSize=12, fontName='Helvetica-Bold',
                       textColor=colors.HexColor(hex_color)))]],
        colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('LINEBELOW',     (0,0), (-1,-1), 2, colors.HexColor(hex_color)),
    ]))
    story.append(Spacer(1, 5*mm))
    story.append(t)
    story.append(Spacer(1, 3*mm))

def _divider(story):
    story.append(HRFlowable(width=W, thickness=0.5, color=C_BORDER, spaceBefore=4, spaceAfter=6))

def _info_chip(label: str, value: str, hex_color: str) -> Table:
    """Chip kecil untuk stats."""
    t = Table([[
        Paragraph(value, ParagraphStyle('cv', fontSize=18, fontName='Helvetica-Bold',
                                        textColor=colors.HexColor(hex_color), alignment=TA_CENTER)),
        Paragraph(label, ParagraphStyle('cl', fontSize=8, textColor=C_MUTED,
                                        alignment=TA_CENTER)),
    ]], colWidths=[W/4])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor(hex_color+'15')),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor(hex_color+'44')),
        ('ROUNDEDCORNERS',[8]),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('ROWSPAN',       (0,0), (0,1)),
    ]))
    return t


# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
def _cover(story, title: str, subtitle: str, hero_text: str,
           hero_sub: str, meta: str, accent: str, bg: str):
    """Universal cover page."""
    rows = [
        # Top accent stripe
        [Table([['']], colWidths=[W], rowHeights=[6],
               style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor(accent)),
                      ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)])],
        [Spacer(1, 12*mm)],
        [Paragraph(title.upper(),
                   ParagraphStyle('cvt', fontSize=9, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor(accent), letterSpacing=3,
                                  alignment=TA_CENTER))],
        [Spacer(1, 2*mm)],
        [Paragraph(subtitle,
                   ParagraphStyle('cvs', fontSize=22, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor(bg), alignment=TA_CENTER,
                                  leading=28))],
        [Spacer(1, 16*mm)],
        # Hero number/text
        [Paragraph(hero_text,
                   ParagraphStyle('cvh', fontSize=88, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor(accent),
                                  alignment=TA_CENTER, leading=92))],
        [Paragraph(hero_sub,
                   ParagraphStyle('cvhs', fontSize=16, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor(bg), alignment=TA_CENTER,
                                  leading=22))],
        [Spacer(1, 4*mm)],
        [Paragraph(meta,
                   ParagraphStyle('cvm', fontSize=10,
                                  textColor=colors.HexColor(bg+'aa' if len(bg)==7 else bg),
                                  alignment=TA_CENTER))],
        [Spacer(1, 20*mm)],
        # Bottom bar
        [Table([['']], colWidths=[W], rowHeights=[3],
               style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor(accent+'66')),
                      ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)])],
        [Spacer(1, 4*mm)],
        [Paragraph('Assessment IQ & Kepribadian v5.0',
                   ParagraphStyle('cvf', fontSize=8, textColor=C_MUTED,
                                  alignment=TA_CENTER))],
        [Paragraph(datetime.now().strftime('%d %B %Y'),
                   ParagraphStyle('cvd', fontSize=8, textColor=C_MUTED,
                                  alignment=TA_CENTER))],
        [Spacer(1, 6*mm)],
    ]
    tbl = Table(rows, colWidths=[W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg)),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
# IQ PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate_iq_pdf(path: str, data: dict, txt: dict):
    s       = _styles()
    lang    = data.get('lang', 'id')
    user    = data.get('user') or {}
    name    = user.get('name', 'Peserta')
    iq      = data.get('iq', 0)
    label   = data.get('label', 'Average')
    pctile  = data.get('percentile', 0)
    correct = data.get('correct', 0)
    total   = data.get('total', 40)
    accent, bg_hint = IQ_COLORS.get(label, ('#8b5cf6', '#ffffff'))
    bg = '#1e2130'  # always dark cover

    doc = SimpleDocTemplate(path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f'IQ Test Summary — {name}')
    story = []

    # ── Cover ──────────────────────────────────────────────────────────────
    meta_str = (
        f'Persentil ke-{pctile}  ·  {correct}/{total} soal benar' if lang=='id'
        else f'Percentile {pctile}th  ·  {correct}/{total} correct'
    )
    _cover(story,
        title='IQ Test Summary',
        subtitle=name,
        hero_text=str(iq),
        hero_sub=label,
        meta=meta_str,
        accent=accent,
        bg=bg,
    )

    # ── Stats row ──────────────────────────────────────────────────────────
    stats_label = ['IQ Score', 'Percentile', 'Correct', 'Total']
    stats_val   = [str(iq), f'{pctile}th', str(correct), str(total)]
    stats_col   = [accent, '#3b82f6', '#27ae60', '#8890aa']
    stats_rows  = [
        [Paragraph(v, ParagraphStyle('sv', fontSize=22, fontName='Helvetica-Bold',
            textColor=colors.HexColor(c), alignment=TA_CENTER)) for v,c in zip(stats_val, stats_col)],
        [Paragraph(l, ParagraphStyle('sl', fontSize=8, textColor=C_MUTED,
            alignment=TA_CENTER)) for l in stats_label],
    ]
    stats_tbl = Table(stats_rows, colWidths=[W/4]*4)
    stats_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), C_BG),
        ('BOX',           (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID',     (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(stats_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Cognitive Profile ──────────────────────────────────────────────────
    cog_title = 'Profil Kognitif' if lang=='id' else 'Cognitive Profile'
    cog_sub   = 'Skor per domain berdasarkan soal yang dijawab (berbobot difficulty)' if lang=='id' else 'Score per domain based on answered questions (difficulty weighted)'
    _section_bar(story, cog_title, accent)
    story.append(Paragraph(cog_sub, s['muted']))
    story.append(Spacer(1, 3*mm))

    cog   = data.get('cognitive', {})
    names = COG_ID if lang=='id' else COG_EN
    lvls  = LVL_ID if lang=='id' else LVL_EN

    cog_rows = []
    for dom, d in sorted(cog.items(), key=lambda x: x[1].get('rank', 99)):
        col  = COG_HEX.get(dom, '#3b82f6')
        name_d = names.get(dom, dom)
        pct  = d.get('score_pct', 0)
        lvl  = lvls.get(d.get('level','average'), d.get('level_id',''))
        cog_rows.append([
            Paragraph(f'<b>{name_d}</b>', ParagraphStyle('cn', fontSize=10,
                textColor=colors.HexColor(col), fontName='Helvetica-Bold')),
            _bar(pct, col, w=W*0.45, h=8),
            Paragraph(f'<b>{pct:.0f}%</b>', ParagraphStyle('cp', fontSize=10,
                textColor=colors.HexColor(col), fontName='Helvetica-Bold',
                alignment=TA_CENTER)),
            Paragraph(lvl, ParagraphStyle('cl', fontSize=9,
                textColor=colors.HexColor(col), alignment=TA_RIGHT)),
        ])

    if cog_rows:
        ct = Table(cog_rows, colWidths=[W*0.28, W*0.45, W*0.1, W*0.17])
        ct.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (0,-1), 6),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS',(0,0), (-1,-1), [C_WHITE, C_BG]),
            ('BOX',           (0,0), (-1,-1), 0.5, C_BORDER),
            ('LINEBELOW',     (0,0), (-1,-2), 0.3, C_BORDER),
        ]))
        story.append(ct)

    # ── AI Interpretation ──────────────────────────────────────────────────
    ai_text = data.get('ai_text', '')
    if ai_text:
        story.append(Spacer(1, 6*mm))
        ai_title = '✨  Interpretasi AI' if lang=='id' else '✨  AI Interpretation'
        _section_bar(story, ai_title, '#6366f1')
        # AI text dalam box dengan background subtle
        ai_tbl = Table([[Paragraph(ai_text, s['body'])]],
                       colWidths=[W])
        ai_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#f0f0ff')),
            ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#c7d2fe')),
            ('TOPPADDING',    (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING',   (0,0), (-1,-1), 14),
            ('RIGHTPADDING',  (0,0), (-1,-1), 14),
        ]))
        story.append(ai_tbl)

    # ── Answer Review ──────────────────────────────────────────────────────
    iq_session = data.get('iq_session', [])
    iq_answers = data.get('iq_answers', [])
    if iq_session and iq_answers:
        story.append(PageBreak())
        rev_title = 'Review Jawaban' if lang=='id' else 'Answer Review'
        _section_bar(story, rev_title, accent)

        correct_count = sum(1 for i,q in enumerate(iq_session)
                           if i < len(iq_answers) and iq_answers[i] == q.get('ans'))
        summary = (f'{correct_count} dari {len(iq_session)} soal dijawab benar' if lang=='id'
                   else f'{correct_count} of {len(iq_session)} questions answered correctly')
        story.append(Paragraph(summary, s['muted']))
        story.append(Spacer(1, 3*mm))

        for i, q in enumerate(iq_session):
            if i >= len(iq_answers): break
            ua = iq_answers[i]
            ca = q.get('ans', 0)
            ok = (ua == ca)

            hdr = Table([[
                Paragraph(f'<b>{"✓" if ok else "✗"}  Q{i+1}</b>  {q.get("category","")}',
                    ParagraphStyle('qh', fontSize=9, fontName='Helvetica-Bold',
                        textColor=C_GREEN if ok else C_RED)),
            ]], colWidths=[W])
            hdr.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1),
                 colors.HexColor('#f0fff4' if ok else '#fff4f4')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('BOX', (0,0), (-1,-1), 0.3,
                 colors.HexColor('#27ae6044' if ok else '#e74c3c44')),
            ]))
            story.append(hdr)

            q_tbl = Table([[Paragraph(q.get('q',''), s['body'])]],
                          colWidths=[W])
            q_tbl.setStyle(TableStyle([
                ('TOPPADDING',   (0,0),(-1,-1),6),
                ('BOTTOMPADDING',(0,0),(-1,-1),4),
                ('LEFTPADDING',  (0,0),(-1,-1),8),
            ]))
            story.append(q_tbl)

            opts = q.get('opts', [])
            for j, opt in enumerate(opts):
                letter = chr(65+j)
                if j == ca and j == ua:
                    story.append(Paragraph(f'  {letter}.  {opt}  ✓  (Jawaban kamu & benar)', s['correct']))
                elif j == ca:
                    story.append(Paragraph(f'  {letter}.  {opt}  ← Jawaban benar', s['correct']))
                elif j == ua:
                    story.append(Paragraph(f'  {letter}.  {opt}  ← Jawaban kamu', s['wrong']))
                else:
                    story.append(Paragraph(f'  {letter}.  {opt}', s['muted']))

            exp = q.get('explanation','')
            if exp:
                story.append(Paragraph(f'💡  {exp}', s['tip']))
            story.append(Spacer(1, 3*mm))

    # ── Footer ─────────────────────────────────────────────────────────────
    _divider(story)
    story.append(Paragraph(
        'Dokumen ini dibuat otomatis. Hasil bersifat indikatif dan tidak menggantikan asesmen profesional.' if lang=='id'
        else 'Auto-generated document. Results are indicative and do not replace professional assessment.',
        s['disc']))

    doc.build(story)


# ══════════════════════════════════════════════════════════════════════════════
# BIG FIVE PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate_bf_pdf(path: str, data: dict, txt: dict):
    s      = _styles()
    lang   = data.get('lang', 'id')
    user   = data.get('user') or {}
    name   = user.get('name', 'Peserta')
    bf     = data.get('bf_scores', {})
    bf_pct = data.get('bf_pcts', {})
    arch   = data.get('archetype') or {}
    dominant = max(bf, key=lambda t: bf.get(t,0)) if bf else 'O'
    accent   = TRAIT_HEX.get(dominant, '#8b5cf6')

    doc = SimpleDocTemplate(path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f'Big Five Test Summary — {name}')
    story = []

    # ── Cover ──────────────────────────────────────────────────────────────
    arch_name = arch.get('name', 'Personality Profile')
    arch_tag  = arch.get('tag', 'BIG FIVE')
    _cover(story,
        title='Big Five Personality Summary',
        subtitle=name,
        hero_text=arch_tag,
        hero_sub=arch_name,
        meta='OCEAN · Big Five Personality Assessment',
        accent=accent,
        bg='#1e2130',
    )

    # ── OCEAN donut row ────────────────────────────────────────────────────
    tnames = TRAIT_ID if lang=='id' else TRAIT_EN
    donut_cells = []
    label_cells = []
    for t in 'OCEAN':
        col = TRAIT_HEX[t]
        sc  = bf.get(t, 50)
        donut_cells.append(_donut(sc, col, size=65))
        label_cells.append(Paragraph(f'<b>{tnames[t]}</b>',
            ParagraphStyle('dl', fontSize=8, fontName='Helvetica-Bold',
                textColor=colors.HexColor(col), alignment=TA_CENTER)))

    donut_tbl = Table([donut_cells, label_cells], colWidths=[W/5]*5)
    donut_tbl.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND',    (0,0), (-1,-1), C_BG),
        ('BOX',           (0,0), (-1,-1), 0.5, C_BORDER),
    ]))
    story.append(donut_tbl)
    story.append(Spacer(1, 6*mm))

    # ── OCEAN Detail bars ──────────────────────────────────────────────────
    ocean_title = 'Profil Kepribadian OCEAN' if lang=='id' else 'OCEAN Personality Profile'
    _section_bar(story, ocean_title, accent)

    tdesc = TRAIT_DESC_ID if lang=='id' else TRAIT_DESC_EN
    for t in 'OCEAN':
        col  = TRAIT_HEX[t]
        sc   = bf.get(t, 50)
        pct  = round(bf_pct.get(t, 50))
        name_t = tnames[t]
        desc   = tdesc.get(t, '')

        row = Table([[
            Paragraph(f'<b>{name_t}  ({t})</b>', ParagraphStyle('tn', fontSize=10,
                fontName='Helvetica-Bold', textColor=colors.HexColor(col))),
            Paragraph(f'<b>{sc:.0f}</b>/100  ·  {pct}th %ile',
                ParagraphStyle('tv', fontSize=9, textColor=colors.HexColor(col),
                    alignment=TA_RIGHT)),
        ]], colWidths=[W*0.55, W*0.45])
        row.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(col+'12')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (0,-1), 8),
            ('RIGHTPADDING', (-1,0), (-1,-1), 8),
        ]))
        story.append(row)
        story.append(_bar(sc, col))
        if desc:
            story.append(Paragraph(desc, s['muted']))
        story.append(Spacer(1, 2*mm))

    # ── Archetype ──────────────────────────────────────────────────────────
    if arch:
        story.append(Spacer(1, 4*mm))
        arch_title = 'Arketipe Kepribadian' if lang=='id' else 'Personality Archetype'
        _section_bar(story, arch_title, accent)

        arch_inner = [
            Paragraph(arch.get('tag',''),
                ParagraphStyle('at', fontSize=8, fontName='Helvetica-Bold',
                    textColor=C_GOLD, letterSpacing=2, spaceAfter=3)),
            Paragraph(f'<b>{arch.get("name","")}</b>',
                ParagraphStyle('an', fontSize=15, fontName='Helvetica-Bold',
                    textColor=C_DARK, spaceAfter=6)),
            Paragraph(arch.get('desc',''), s['body']),
        ]
        arch_box = Table(
            [[item] for item in arch_inner],
            colWidths=[W]
        )
        arch_box.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor(accent+'10')),
            ('BOX',           (0,0), (-1,-1), 1.5, colors.HexColor(accent+'44')),
            ('TOPPADDING',    (0,0), (0,0), 14),
            ('TOPPADDING',    (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-2), 4),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 14),
            ('LEFTPADDING',   (0,0), (-1,-1), 16),
            ('RIGHTPADDING',  (0,0), (-1,-1), 16),
        ]))
        story.append(arch_box)

    # ── Careers ────────────────────────────────────────────────────────────
    careers = data.get('careers', [])
    if careers:
        story.append(Spacer(1, 6*mm))
        car_title = 'Rekomendasi Karir' if lang=='id' else 'Career Recommendations'
        _section_bar(story, car_title, accent)

        medals = ['🥇','🥈','🥉','4','5','6','7','8']
        car_data = [[
            Paragraph('<b>Karir</b>' if lang=='id' else '<b>Career</b>',
                ParagraphStyle('ch', fontSize=9, fontName='Helvetica-Bold', textColor=C_MUTED)),
            Paragraph('<b>Kesesuaian</b>' if lang=='id' else '<b>Match</b>',
                ParagraphStyle('ch2', fontSize=9, fontName='Helvetica-Bold',
                    textColor=C_MUTED, alignment=TA_CENTER)),
            Paragraph('<b>Bar</b>',
                ParagraphStyle('ch3', fontSize=9, fontName='Helvetica-Bold',
                    textColor=C_WHITE, alignment=TA_CENTER)),
        ]]
        for i, c in enumerate(careers[:8]):
            conf = c.get('confidence', 0)
            col  = '#27ae60' if conf>=75 else ('#3b82f6' if conf>=60 else '#8890aa')
            car_data.append([
                Paragraph(f'{medals[i]}  <b>{c["name"]}</b>',
                    ParagraphStyle('cn', fontSize=10, textColor=C_DARK)),
                Paragraph(f'<b>{conf}%</b>',
                    ParagraphStyle('cc', fontSize=10, fontName='Helvetica-Bold',
                        textColor=colors.HexColor(col), alignment=TA_CENTER)),
                _bar(conf, col, w=W*0.38, h=8),
            ])

        car_tbl = Table(car_data, colWidths=[W*0.4, W*0.12, W*0.38+W*0.1])
        car_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  C_DARK2),
            ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_WHITE, C_BG]),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('BOX',           (0,0), (-1,-1), 0.5, C_BORDER),
            ('LINEBELOW',     (0,0), (-1,-2), 0.3, C_BORDER),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(car_tbl)

    # ── Roadmap ────────────────────────────────────────────────────────────
    roadmap = data.get('roadmap', [])
    if roadmap:
        story.append(PageBreak())
        road_title = 'Roadmap Pengembangan 3 Bulan' if lang=='id' else '3-Month Development Roadmap'
        _section_bar(story, road_title, accent)

        road_sub = 'Rencana aksi konkret berdasarkan profil kepribadian kamu.' if lang=='id' else 'Concrete action plan based on your personality profile.'
        story.append(Paragraph(road_sub, s['muted']))
        story.append(Spacer(1, 3*mm))

        month_accents = [accent, '#3b82f6', '#27ae60']
        month_lbl = 'Bulan' if lang=='id' else 'Month'
        for i, month in enumerate(roadmap):
            mc = month_accents[i % 3]
            # Month header
            mhdr = Table([[
                Paragraph(f'<b>{month_lbl} {month["month"]}</b>',
                    ParagraphStyle('mh', fontSize=10, fontName='Helvetica-Bold',
                        textColor=C_WHITE)),
                Paragraph(f'<b>{month.get("focus","")}</b>',
                    ParagraphStyle('mf', fontSize=10, fontName='Helvetica-Bold',
                        textColor=colors.HexColor(mc+'dd' if len(mc)==7 else mc))),
            ]], colWidths=[W*0.2, W*0.8])
            mhdr.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_DARK),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBELOW', (0,0), (0,-1), 3, colors.HexColor(mc)),
            ]))
            story.append(mhdr)

            for act in month.get('actions', []):
                act_row = Table([[
                    Paragraph(f'☐  {act}', ParagraphStyle('ar', fontSize=9, textColor=C_DARK,
                        leading=14, leftIndent=4))
                ]], colWidths=[W])
                act_row.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0), (-1,-1), C_WHITE),
                    ('TOPPADDING',    (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING',   (0,0), (-1,-1), 14),
                    ('LINEBELOW',     (0,0), (-1,-1), 0.3, C_BORDER),
                    ('LINEBEFORE',    (0,0), (0,-1), 3, colors.HexColor(mc)),
                ]))
                story.append(act_row)
            story.append(Spacer(1, 5*mm))

    # ── AI Interpretation ──────────────────────────────────────────────────
    ai_text = data.get('ai_text', '')
    if ai_text:
        if roadmap:
            pass  # sudah di page baru
        else:
            story.append(Spacer(1, 6*mm))
        ai_title = '✨  Interpretasi AI — Analisis Personal' if lang=='id' else '✨  AI Interpretation — Personal Analysis'
        _section_bar(story, ai_title, '#6366f1')
        ai_tbl = Table([[Paragraph(ai_text, s['body'])]], colWidths=[W])
        ai_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), colors.HexColor('#f0f0ff')),
            ('BOX',          (0,0), (-1,-1), 0.5, colors.HexColor('#c7d2fe')),
            ('TOPPADDING',   (0,0), (-1,-1), 14),
            ('BOTTOMPADDING',(0,0), (-1,-1), 14),
            ('LEFTPADDING',  (0,0), (-1,-1), 14),
            ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(ai_tbl)

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    _divider(story)
    story.append(Paragraph(
        'Dokumen ini dibuat otomatis. Hasil bersifat indikatif dan tidak menggantikan asesmen profesional.' if lang=='id'
        else 'Auto-generated document. Results are indicative and do not replace professional assessment.',
        s['disc']))

    doc.build(story)


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-DETECT
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(path: str, data: dict, txt: dict):
    test_type = data.get('test_type', '')
    if test_type == 'iq':
        generate_iq_pdf(path, data, txt)
    elif test_type in ('bigfive', 'bf'):
        generate_bf_pdf(path, data, txt)
    else:
        if 'iq' in data:
            generate_iq_pdf(path, data, txt)
        else:
            generate_bf_pdf(path, data, txt)