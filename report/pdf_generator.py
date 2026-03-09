"""
report/pdf_generator.py
─────────────────────────────────────────────────────────────────
PDF Generator 2-in-1:
  Halaman 1-2 : EXECUTIVE SUMMARY  (ringkasan, siap dibagikan)
  Halaman 3+  : FULL REPORT        (7 section lengkap)

Library: ReportLab (Platypus)
─────────────────────────────────────────────────────────────────
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from datetime import datetime

# ── Warna brand ────────────────────────────────────────────────
C_DARK     = colors.HexColor('#1e2130')
C_DARK2    = colors.HexColor('#262b3d')
C_LIGHT    = colors.HexColor('#f5f6fa')
C_WHITE    = colors.white
C_GOLD     = colors.HexColor('#f5a623')
C_GOLD_LT  = colors.HexColor('#fff3dc')
C_BLUE     = colors.HexColor('#3b82f6')
C_GREEN    = colors.HexColor('#27ae60')
C_RED      = colors.HexColor('#e74c3c')
C_PURPLE   = colors.HexColor('#8b5cf6')
C_ORANGE   = colors.HexColor('#f97316')
C_MUTED    = colors.HexColor('#8890aa')
C_BORDER   = colors.HexColor('#e2e4ee')

TRAIT_COLORS_HEX = {
    'O': '#f97316', 'C': '#3b82f6',
    'E': '#8b5cf6', 'A': '#27ae60', 'N': '#e74c3c',
}
CAT_COLORS_HEX = {
    'fluid':        '#f97316',
    'crystallized': '#8b5cf6',
    'abstract':     '#3b82f6',
    'quantitative': '#27ae60',
    'spatial':      '#f5a623',
}
IQ_CAT_COLORS = {
    'Very Superior':  '#f5a623', 'Superior':       '#27ae60',
    'High Average':   '#3b82f6', 'Average':        '#8b5cf6',
    'Low Average':    '#f97316', 'Below Average':  '#e74c3c',
    'Well Below Avg': '#e74c3c',
}

W_PAGE = A4[0] - 40*mm  # usable width


# ══════════════════════════════════════════════════════════════
# STYLE FACTORY
# ══════════════════════════════════════════════════════════════
def _styles():
    base = getSampleStyleSheet()
    def ms(name, parent='Normal', **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        'cover_title': ms('ct', fontSize=28, textColor=C_WHITE,
                          fontName='Helvetica-Bold', alignment=TA_CENTER,
                          leading=34, spaceAfter=6),
        'cover_sub':   ms('cs', fontSize=12, textColor=colors.HexColor('#b0b8d0'),
                          alignment=TA_CENTER, spaceAfter=4),
        'cover_date':  ms('cd', fontSize=10, textColor=colors.HexColor('#7b82a0'),
                          alignment=TA_CENTER),
        'section_badge': ms('sb', fontSize=9, textColor=C_GOLD,
                            fontName='Helvetica-Bold', letterSpacing=2,
                            spaceAfter=4),
        'h1':          ms('h1', fontSize=16, textColor=C_DARK,
                          fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=8),
        'h2':          ms('h2', fontSize=12, textColor=C_BLUE,
                          fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4),
        'h3':          ms('h3', fontSize=10, textColor=C_DARK,
                          fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3),
        'body':        ms('bd', fontSize=10, textColor=C_DARK,
                          leading=16, spaceAfter=6),
        'body_muted':  ms('bm', fontSize=9, textColor=C_MUTED,
                          leading=14, spaceAfter=4),
        'correct':     ms('ok', fontSize=10, textColor=C_GREEN, leading=14),
        'wrong':       ms('wr', fontSize=10, textColor=C_RED,   leading=14),
        'gold_note':   ms('gn', fontSize=9,  textColor=colors.HexColor('#7a5200'),
                          leading=14, spaceAfter=6,
                          backColor=C_GOLD_LT, borderPadding=6),
        'disclaimer':  ms('di', fontSize=8,  textColor=C_MUTED,
                          leading=12, alignment=TA_CENTER),
        'exec_number': ms('en', fontSize=42, textColor=C_DARK,
                          fontName='Helvetica-Bold', alignment=TA_CENTER),
        'exec_label':  ms('el', fontSize=10, textColor=C_MUTED,
                          alignment=TA_CENTER),
        'exec_value':  ms('ev', fontSize=13, textColor=C_DARK,
                          fontName='Helvetica-Bold', alignment=TA_CENTER),
        'tag':         ms('tg', fontSize=8,  textColor=C_GOLD,
                          fontName='Helvetica-Bold', letterSpacing=1),
        'action':      ms('ac', fontSize=9,  textColor=C_DARK,
                          leading=14, leftIndent=12, spaceAfter=3),
        'mitigation':  ms('mt', fontSize=9,  textColor=colors.HexColor('#1a4731'),
                          leading=13, backColor=colors.HexColor('#e8f8f0'),
                          borderPadding=5, spaceAfter=4),
    }


# ══════════════════════════════════════════════════════════════
# MINI WIDGETS (drawn with ReportLab Drawing)
# ══════════════════════════════════════════════════════════════
def _bar_drawing(pct, color_hex, width=W_PAGE - 20*mm, height=8):
    """Horizontal progress bar."""
    d = Drawing(width, height + 4)
    # Background
    d.add(Rect(0, 2, width, height,
               fillColor=C_BORDER, strokeColor=None, rx=4, ry=4))
    # Fill
    fill_w = max(4, int(width * pct / 100))
    d.add(Rect(0, 2, fill_w, height,
               fillColor=colors.HexColor(color_hex),
               strokeColor=None, rx=4, ry=4))
    return d


def _confidence_bar(pct, color_hex, label, width=W_PAGE * 0.55):
    """Bar dengan label confidence % di kanan."""
    d = Drawing(width, 14)
    bg_w = width - 50
    d.add(Rect(0, 3, bg_w, 8,
               fillColor=C_BORDER, strokeColor=None, rx=4, ry=4))
    fill_w = max(4, int(bg_w * pct / 100))
    d.add(Rect(0, 3, fill_w, 8,
               fillColor=colors.HexColor(color_hex),
               strokeColor=None, rx=4, ry=4))
    d.add(String(bg_w + 6, 3, f'{pct}%',
                 fontSize=9, fillColor=colors.HexColor(color_hex),
                 fontName='Helvetica-Bold'))
    return d


def _cover_block():
    """Dark cover block (full-width table row)."""
    return None   # handled inline via Table background


# ══════════════════════════════════════════════════════════════
# SECTION BUILDERS
# ══════════════════════════════════════════════════════════════
def _divider(story, label='', color=C_BORDER):
    if label:
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width=W_PAGE, thickness=1,
                                color=color, spaceAfter=2))
    else:
        story.append(HRFlowable(width=W_PAGE, thickness=0.5,
                                color=color, spaceAfter=4))


def _section_header(story, number, title, styles):
    data = [[Paragraph(f'<b>{number}</b>', ParagraphStyle(
                'sn', fontSize=11, textColor=C_WHITE,
                fontName='Helvetica-Bold', alignment=TA_CENTER)),
             Paragraph(title, ParagraphStyle(
                'st', fontSize=12, textColor=C_WHITE,
                fontName='Helvetica-Bold', leftIndent=4))]]
    t = Table(data, colWidths=[8*mm, W_PAGE - 8*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_DARK),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (0,0), 6),
    ]))
    story.append(Spacer(1, 4*mm))
    story.append(t)
    story.append(Spacer(1, 3*mm))


def _kv_table(story, rows, col_widths=None):
    """Tabel key-value sederhana."""
    if not col_widths:
        col_widths = [W_PAGE * 0.38, W_PAGE * 0.62]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (0,-1), C_MUTED),
        ('TEXTCOLOR',     (1,0), (1,-1), C_DARK),
        ('FONTNAME',      (1,0), (1,-1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,0), (-1,-1),
         [C_LIGHT, C_WHITE]),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('GRID',          (0,0), (-1,-1), 0.3, C_BORDER),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 3*mm))


# ══════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════
def _build_cover(story, data, txt, styles):
    # Full-dark cover via large table
    iq      = data.get('iq', '—')
    label   = data.get('label', '—')
    lang    = data.get('lang', 'id')
    date_str = datetime.now().strftime('%d %B %Y  ·  %H:%M')

    label_localized = txt['iq_categories'].get(label, label)
    iq_color = IQ_CAT_COLORS.get(label, '#8b5cf6')

    cover_data = [[
        Paragraph(txt['pdf']['title'], styles['cover_title']),
    ],[
        Paragraph(date_str, styles['cover_date']),
    ],[
        Spacer(1, 8*mm),
    ],[
        Paragraph(str(iq), ParagraphStyle('ciq', fontSize=64,
            textColor=colors.HexColor(iq_color),
            fontName='Helvetica-Bold', alignment=TA_CENTER)),
    ],[
        Paragraph(label_localized, ParagraphStyle('clbl', fontSize=16,
            textColor=C_WHITE, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=2)),
    ],[
        Paragraph('IQ ESTIMATE', ParagraphStyle('cest', fontSize=9,
            textColor=colors.HexColor('#7b82a0'), letterSpacing=2,
            alignment=TA_CENTER)),
    ],[
        Spacer(1, 6*mm),
    ]]

    # Archetype row if available
    arch = data.get('archetype')
    if arch:
        cover_data.append([
            Paragraph(arch.get('tag', ''), ParagraphStyle('ctag', fontSize=9,
                textColor=C_GOLD, fontName='Helvetica-Bold',
                letterSpacing=2, alignment=TA_CENTER)),
        ])
        cover_data.append([
            Paragraph(arch.get('name', ''), ParagraphStyle('cname', fontSize=18,
                textColor=C_WHITE, fontName='Helvetica-Bold',
                alignment=TA_CENTER)),
        ])

    cover_data.append([Spacer(1, 10*mm)])
    cover_data.append([
        Paragraph(txt['pdf']['created_by'], styles['cover_date']),
    ])

    tbl = Table(cover_data, colWidths=[W_PAGE])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_DARK),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 10*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 10*mm),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY  (halaman 2)
# ══════════════════════════════════════════════════════════════
def _build_exec_summary(story, data, txt, styles):
    s = styles

    # Header badge
    story.append(Paragraph(txt['pdf']['exec_summary'],
                           ParagraphStyle('exh', fontSize=10, textColor=C_GOLD,
                               fontName='Helvetica-Bold', letterSpacing=3,
                               spaceAfter=6)))
    _divider(story, color=C_GOLD)

    # ── IQ Block ──
    iq     = data.get('iq', 0)
    label  = data.get('label', '—')
    pctile = data.get('percentile', 0)
    correct= data.get('correct', 0)
    total  = data.get('total', 0)
    label_loc = txt['iq_categories'].get(label, label)
    iq_col = IQ_CAT_COLORS.get(label, '#8b5cf6')

    iq_cells = [
        [Paragraph(str(iq),      ParagraphStyle('eiqn', fontSize=40,
            textColor=colors.HexColor(iq_col), fontName='Helvetica-Bold',
            alignment=TA_CENTER)),
         Paragraph(label_loc,    ParagraphStyle('eiql', fontSize=14,
            textColor=colors.HexColor(iq_col), fontName='Helvetica-Bold',
            alignment=TA_CENTER)),
         Paragraph(f'{pctile}th', ParagraphStyle('eiqp', fontSize=22,
            textColor=C_DARK, fontName='Helvetica-Bold', alignment=TA_CENTER)),
         Paragraph(f'{correct}/{total}', ParagraphStyle('eiqc', fontSize=18,
            textColor=C_BLUE, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        ],
        [Paragraph('IQ', s['exec_label']),
         Paragraph(txt['pdf']['section_cognitive'].split('.')[1].strip(), s['exec_label']),
         Paragraph(txt['pdf']['percentile'], s['exec_label']),
         Paragraph(txt['pdf']['your_score'], s['exec_label']),
        ],
    ]
    iq_tbl = Table(iq_cells, colWidths=[W_PAGE/4]*4)
    iq_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID',          (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(iq_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Cognitive top 2 ──
    cog = data.get('cognitive', {})
    if cog:
        cog_sorted = sorted(cog.items(), key=lambda x: x[1]['score_pct'], reverse=True)
        cog_names_id = {
            'fluid':'Penalaran Cair','crystallized':'Kecerdasan Verbal',
            'abstract':'Penalaran Abstrak','quantitative':'Penalaran Kuantitatif',
            'spatial':'Kecerdasan Spasial',
        }
        cog_names_en = {
            'fluid':'Fluid Reasoning','crystallized':'Verbal Intelligence',
            'abstract':'Abstract Reasoning','quantitative':'Quantitative Reasoning',
            'spatial':'Spatial Intelligence',
        }
        cog_names = cog_names_id if data.get('lang','id')=='id' else cog_names_en

        story.append(Paragraph(txt['expert']['cognitive_title'], s['h3']))
        cog_rows = [['Domain', txt['pdf']['your_score'], '%']]
        for dom, d in cog_sorted[:5]:
            col = CAT_COLORS_HEX.get(dom, '#3b82f6')
            cog_rows.append([
                cog_names.get(dom, dom),
                d['level'],
                f"{d['score_pct']:.0f}%",
            ])
        cog_tbl = Table(cog_rows, colWidths=[W_PAGE*0.5, W_PAGE*0.3, W_PAGE*0.2])
        cog_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), C_DARK2),
            ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_LIGHT, C_WHITE]),
            ('GRID',          (0,0), (-1,-1), 0.3, C_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(cog_tbl)
        story.append(Spacer(1, 4*mm))

    # ── Personality block ──
    arch = data.get('archetype')
    bf_scores = data.get('bf_scores', {})
    bf_pcts   = data.get('bf_pcts', {})
    if arch and bf_scores:
        story.append(Paragraph(txt['expert']['combined_title'], s['h3']))

        trait_names = txt['trait_names']
        trait_rows  = [['Trait', txt['pdf']['your_score'], txt['pdf']['percentile']]]
        for t in ['O','C','E','A','N']:
            trait_rows.append([
                trait_names.get(t, t),
                f"{bf_scores.get(t,50)}/100",
                f"{round(bf_pcts.get(t,50))}th",
            ])
        t_tbl = Table(trait_rows, colWidths=[W_PAGE*0.4, W_PAGE*0.3, W_PAGE*0.3])
        t_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), C_DARK2),
            ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_LIGHT, C_WHITE]),
            ('GRID',          (0,0), (-1,-1), 0.3, C_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_tbl)
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph(f'<b>{arch.get("tag","")}</b>  —  {arch.get("name","")}',
                               s['tag']))
        story.append(Paragraph(arch.get('desc',''), s['body_muted']))

    # ── Top careers ──
    careers = data.get('careers', [])
    if careers:
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(txt['expert']['career_title'], s['h3']))
        car_rows = [[txt['expert']['career_title'].split()[0],
                     txt['expert']['career_confidence']]]
        for c in careers[:5]:
            car_rows.append([c['name'], f"{c['confidence']}%"])
        c_tbl = Table(car_rows, colWidths=[W_PAGE*0.75, W_PAGE*0.25])
        c_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), C_DARK2),
            ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_LIGHT, C_WHITE]),
            ('GRID',          (0,0), (-1,-1), 0.3, C_BORDER),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(c_tbl)

    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 1: Cognitive
# ══════════════════════════════════════════════════════════════
def _build_section_cognitive(story, data, txt, styles):
    s = styles
    _section_header(story, '1', txt['pdf']['section_cognitive'], s)

    cog = data.get('cognitive', {})
    if not cog:
        story.append(Paragraph('—', s['body_muted'])); return

    cog_names_id = {
        'fluid':'Penalaran Cair (Fluid Reasoning)',
        'crystallized':'Kecerdasan Terkristalisasi (Crystallized Intelligence)',
        'abstract':'Penalaran Abstrak (Abstract Reasoning)',
        'quantitative':'Penalaran Kuantitatif (Quantitative Reasoning)',
        'spatial':'Kecerdasan Spasial (Spatial Intelligence)',
    }
    cog_names_en = {
        'fluid':'Fluid Reasoning',
        'crystallized':'Crystallized Intelligence',
        'abstract':'Abstract Reasoning',
        'quantitative':'Quantitative Reasoning',
        'spatial':'Spatial Intelligence',
    }
    lang = data.get('lang', 'id')
    cog_names = cog_names_id if lang == 'id' else cog_names_en

    from engine.scoring import (COGNITIVE_DESC_ID, COGNITIVE_DESC_EN,
                                COGNITIVE_LEVEL_COLORS, COGNITIVE_LEVEL_ID)
    cog_desc  = COGNITIVE_DESC_ID if lang == 'id' else COGNITIVE_DESC_EN
    level_lbl = COGNITIVE_LEVEL_ID if lang == 'id' else {k:k for k in COGNITIVE_LEVEL_ID}

    cog_sorted = sorted(cog.items(), key=lambda x: x[1]['rank'])

    for dom, d in cog_sorted:
        col  = CAT_COLORS_HEX.get(dom, '#3b82f6')
        lvl  = d['level']
        pct  = d['score_pct']
        name = cog_names.get(dom, dom)
        lbl  = level_lbl.get(lvl, lvl)

        hdr_row = [[
            Paragraph(f'<b>{name}</b>', ParagraphStyle('ch', fontSize=10,
                textColor=colors.HexColor(col), fontName='Helvetica-Bold')),
            Paragraph(f'<b>{lbl}</b>  ·  {pct:.0f}%',
                ParagraphStyle('cv', fontSize=10, textColor=colors.HexColor(col),
                    fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ]]
        hdr = Table(hdr_row, colWidths=[W_PAGE*0.6, W_PAGE*0.4])
        hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(col+'15')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (0,-1), 8),
            ('RIGHTPADDING', (-1,0), (-1,-1), 8),
        ]))
        story.append(hdr)
        story.append(_bar_drawing(pct, col, width=W_PAGE))
        desc = cog_desc.get(dom, {}).get(lvl, '')
        if desc:
            story.append(Paragraph(desc, s['body_muted']))
        story.append(Spacer(1, 3*mm))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 2: Personality
# ══════════════════════════════════════════════════════════════
def _build_section_personality(story, data, txt, styles):
    s = styles
    _section_header(story, '2', txt['pdf']['section_personality'], s)

    bf_scores = data.get('bf_scores', {})
    bf_pcts   = data.get('bf_pcts', {})
    arch      = data.get('archetype', {})
    lang      = data.get('lang', 'id')

    if not bf_scores:
        story.append(Paragraph('—', s['body_muted'])); return

    if arch:
        story.append(Paragraph(f'<b>{arch.get("tag","")}</b>', s['tag']))
        story.append(Paragraph(arch.get('name',''),
                               ParagraphStyle('an', fontSize=14, textColor=C_DARK,
                                   fontName='Helvetica-Bold', spaceAfter=4)))
        story.append(Paragraph(arch.get('desc',''), s['body']))
        _divider(story)

    trait_names = txt['trait_names']
    trait_low   = txt['trait_low']
    trait_high  = txt['trait_high']
    # pop_stat loaded from norms.json
    import json
    with open('processed/norms.json', encoding='utf-8') as _f:
        _pop = json.load(_f)['stats']

    for t in ['O','C','E','A','N']:
        col  = TRAIT_COLORS_HEX.get(t, '#3b82f6')
        sc   = bf_scores.get(t, 50)
        pct  = round(bf_pcts.get(t, 50))
        name = trait_names.get(t, t)

        row = [[
            Paragraph(f'<b>{name}</b>', ParagraphStyle('tn', fontSize=10,
                textColor=colors.HexColor(col), fontName='Helvetica-Bold')),
            Paragraph(f'<b>{sc}/100</b>  ·  {pct}th percentile',
                ParagraphStyle('tv', fontSize=10, textColor=colors.HexColor(col),
                    fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ]]
        hdr = Table(row, colWidths=[W_PAGE*0.55, W_PAGE*0.45])
        hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(col+'15')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING',  (0,0), (0,-1), 8),
            ('RIGHTPADDING', (-1,0), (-1,-1), 8),
        ]))
        story.append(hdr)
        story.append(_bar_drawing(sc, col, width=W_PAGE))
        story.append(Paragraph(
            f'{trait_low.get(t,"")} ↔ {trait_high.get(t,"")}',
            s['body_muted']))
        story.append(Spacer(1, 3*mm))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 3: Combined Profile
# ══════════════════════════════════════════════════════════════
def _build_section_combined(story, data, txt, styles):
    s = styles
    _section_header(story, '3', txt['pdf']['section_combined'], s)
    combined = data.get('combined', {})
    if not combined:
        story.append(Paragraph('—', s['body_muted'])); return

    story.append(Paragraph(f'<b>{combined.get("name","")}</b>',
                           ParagraphStyle('cpn', fontSize=13, textColor=C_DARK,
                               fontName='Helvetica-Bold', spaceAfter=4)))
    story.append(Paragraph(combined.get('desc', ''), s['body']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '→ ' + combined.get('action', ''),
        ParagraphStyle('cpa', fontSize=10, textColor=C_BLUE,
            fontName='Helvetica-Bold', leading=14, leftIndent=8)
    ))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 4: Career
# ══════════════════════════════════════════════════════════════
def _build_section_career(story, data, txt, styles):
    s = styles
    _section_header(story, '4', txt['pdf']['section_career'], s)
    careers = data.get('careers', [])
    if not careers:
        story.append(Paragraph('—', s['body_muted'])); return

    story.append(Paragraph(txt['expert']['career_subtitle'], s['body_muted']))
    story.append(Spacer(1, 3*mm))

    for i, c in enumerate(careers, 1):
        conf  = c['confidence']
        col   = C_GREEN if conf >= 75 else (C_BLUE if conf >= 60 else C_MUTED)
        rank_label = ['🥇','🥈','🥉','4.','5.'][i-1]
        story.append(Paragraph(
            f'<b>{rank_label}  {c["name"]}</b>',
            ParagraphStyle('crn', fontSize=11, textColor=C_DARK,
                fontName='Helvetica-Bold', spaceAfter=2)
        ))
        story.append(_confidence_bar(conf, TRAIT_COLORS_HEX.get('O','#f97316'),
                                     txt['pdf']['confidence']))
        story.append(Spacer(1, 3*mm))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 5: Learning Style
# ══════════════════════════════════════════════════════════════
def _build_section_learning(story, data, txt, styles):
    s = styles
    _section_header(story, '5', txt['pdf']['section_learning'], s)
    style_name   = data.get('learning_style_name', '')
    style_detail = data.get('learning_style_detail', {})
    if not style_name:
        story.append(Paragraph('—', s['body_muted'])); return

    story.append(Paragraph(f'<b>{style_name}</b>',
                           ParagraphStyle('lsn', fontSize=14, textColor=C_BLUE,
                               fontName='Helvetica-Bold', spaceAfter=4)))
    story.append(Paragraph(style_detail.get('desc', ''), s['body']))
    _divider(story)

    tips = style_detail.get('tips', [])
    if tips:
        lang = data.get('lang', 'id')
        story.append(Paragraph('<b>Tips:</b>' if lang == 'id' else '<b>Tips:</b>', s['h3']))
        for tip in tips:
            story.append(Paragraph(f'• {tip}', s['action']))

    env = style_detail.get('environment', '')
    if env:
        story.append(Spacer(1, 2*mm))
        lang = data.get('lang', 'id')
        lbl = 'Lingkungan ideal:' if lang == 'id' else 'Ideal environment:'
        story.append(Paragraph(f'<b>{lbl}</b> {env}', s['body_muted']))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 6: Blind Spots
# ══════════════════════════════════════════════════════════════
def _build_section_blindspots(story, data, txt, styles):
    s = styles
    _section_header(story, '6', txt['pdf']['section_blindspot'], s)
    blind_spots = data.get('blind_spots', [])
    if not blind_spots:
        story.append(Paragraph('—', s['body_muted'])); return

    lang = data.get('lang', 'id')
    mit_lbl = 'Mitigasi:' if lang == 'id' else 'Mitigation:'

    for bs in blind_spots:
        story.append(KeepTogether([
            Paragraph(f'⚠  <b>{bs["title"]}</b>',
                      ParagraphStyle('bst', fontSize=10, textColor=C_RED,
                          fontName='Helvetica-Bold', spaceAfter=3)),
            Paragraph(bs['desc'], s['body']),
            Paragraph(f'<b>{mit_lbl}</b> {bs["mitigation"]}', s['mitigation']),
            Spacer(1, 3*mm),
        ]))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — Section 7: Roadmap
# ══════════════════════════════════════════════════════════════
def _build_section_roadmap(story, data, txt, styles):
    s = styles
    _section_header(story, '7', txt['pdf']['section_roadmap'], s)
    roadmap = data.get('roadmap', [])
    if not roadmap:
        story.append(Paragraph('—', s['body_muted'])); return

    month_colors = [C_BLUE, C_GREEN, C_GOLD]
    lang = data.get('lang', 'id')
    month_lbl   = txt['pdf']['month']
    focus_lbl   = txt['pdf']['section_roadmap'].split('—')[0].strip()
    actions_lbl = 'Aksi' if lang == 'id' else 'Actions'

    for i, month in enumerate(roadmap):
        col = month_colors[i % len(month_colors)]
        header_row = [[
            Paragraph(f'<b>{month_lbl} {month["month"]}  —  {month["focus"]}</b>',
                      ParagraphStyle('rmh', fontSize=11, textColor=C_WHITE,
                          fontName='Helvetica-Bold'))
        ]]
        hdr = Table(header_row, colWidths=[W_PAGE])
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), col),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        story.append(hdr)

        actions = month.get('actions', [])
        act_items = [[
            Paragraph(f'☐  {act}',
                      ParagraphStyle('rma', fontSize=9, textColor=C_DARK,
                          leading=14, leftIndent=4))
        ] for act in actions]

        if act_items:
            act_tbl = Table(act_items, colWidths=[W_PAGE])
            act_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
                ('TOPPADDING',    (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING',   (0,0), (-1,-1), 12),
                ('LINEBELOW',     (0,0), (-1,-2), 0.3, C_BORDER),
            ]))
            story.append(act_tbl)
        story.append(Spacer(1, 4*mm))


# ══════════════════════════════════════════════════════════════
# FULL REPORT — IQ Answer Review
# ══════════════════════════════════════════════════════════════
def _build_iq_review(story, data, txt, styles):
    s = styles
    lang = data.get('lang', 'id')
    lbl  = 'Review Jawaban IQ' if lang == 'id' else 'IQ Answer Review'
    _section_header(story, '★', lbl, s)

    iq_answers = data.get('iq_answers', [])
    iq_session = data.get('iq_session', [])
    if not iq_answers or not iq_session:
        story.append(Paragraph('—', s['body_muted'])); return

    for i, q in enumerate(iq_session):
        ua = iq_answers[i]
        ca = q['ans']
        ok = (ua == ca)
        icon  = '✓' if ok else '✗'
        i_col = C_GREEN if ok else C_RED

        q_row = [[
            Paragraph(f'<b>{i+1}. {q["category"]}</b>',
                      ParagraphStyle('qcat', fontSize=8, textColor=C_MUTED)),
            Paragraph(f'<b>{icon}</b>',
                      ParagraphStyle('qic', fontSize=10, textColor=i_col,
                          fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ]]
        q_hdr = Table(q_row, colWidths=[W_PAGE*0.85, W_PAGE*0.15])
        q_hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), C_LIGHT),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING',   (0,0), (0,-1), 8),
        ]))
        story.append(q_hdr)
        story.append(Paragraph(q['q'].replace('\n', ' '), s['body']))

        for j, opt in enumerate(q['opts']):
            prefix = chr(65+j)
            if j == ca and j == ua:
                p = Paragraph(f'{prefix}. {opt}  [{txt["iq_result"]["review_your_and_correct"]}]', s['correct'])
            elif j == ca:
                p = Paragraph(f'{prefix}. {opt}  [← {txt["iq_result"]["review_correct_answer"]}]', s['correct'])
            elif j == ua:
                p = Paragraph(f'{prefix}. {opt}  [{txt["iq_result"]["review_your_answer"]}]', s['wrong'])
            else:
                p = Paragraph(f'{prefix}. {opt}', s['body_muted'])
            story.append(p)

        if 'explanation' in q:
            story.append(Paragraph(
                f'{txt["iq_result"]["explanation_label"]}: {q["explanation"]}',
                s['gold_note']
            ))
        story.append(HRFlowable(width=W_PAGE, thickness=0.3,
                                color=C_BORDER, spaceAfter=4))


# ══════════════════════════════════════════════════════════════
# APPENDIX
# ══════════════════════════════════════════════════════════════
def _build_appendix(story, data, txt, styles):
    s = styles
    _section_header(story, 'A', txt['pdf']['appendix'], s)

    iq = data.get('iq', 0)
    correct = data.get('correct', 0)
    total   = data.get('total', 0)
    pctile  = data.get('percentile', 0)
    w_pct   = data.get('weighted_pct', 0)
    n_pop   = data.get('n_population', 0)

    lang = data.get('lang', 'id')
    rows_id = [
        ['Estimasi IQ', str(iq)],
        ['Kategori', txt['iq_categories'].get(data.get('label',''), data.get('label',''))],
        ['Persentil Populasi', f'{pctile}th dari {n_pop:,} responden'],
        ['Jawaban Benar (mentah)', f'{correct}/{total}'],
        ['Weighted Score', f'{w_pct:.1f}%'],
        ['Metode Skoring', 'Weighted difficulty-based + Normal dist. normalization'],
        ['Dataset Norma IQ', 'Open Psychometrics IQ Alpha (N=2,051)'],
        ['Dataset Norma Big Five', f'IPIP Tunguz Kaggle (N={data.get("n_bf_pop", 874434):,})'],
    ]
    rows_en = [
        ['IQ Estimate', str(iq)],
        ['Category', txt['iq_categories'].get(data.get('label',''), data.get('label',''))],
        ['Population Percentile', f'{pctile}th of {n_pop:,} respondents'],
        ['Correct Answers (raw)', f'{correct}/{total}'],
        ['Weighted Score', f'{w_pct:.1f}%'],
        ['Scoring Method', 'Weighted difficulty-based + Normal dist. normalization'],
        ['IQ Norm Dataset', 'Open Psychometrics IQ Alpha (N=2,051)'],
        ['Big Five Norm Dataset', f'IPIP Tunguz Kaggle (N={data.get("n_bf_pop", 874434):,})'],
    ]
    rows = rows_id if lang == 'id' else rows_en
    _kv_table(story, rows)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(txt['pdf']['methodology_note'], s['body_muted']))
    story.append(Spacer(1, 6*mm))
    _divider(story)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(txt['pdf']['disclaimer'], s['disclaimer']))


# ══════════════════════════════════════════════════════════════
# MAIN EXPORT FUNCTION
# ══════════════════════════════════════════════════════════════
def generate_pdf(path, data, txt):
    """
    Generate PDF 2-in-1 ke `path`.

    data dict keys:
      iq, label, color, percentile, correct, total, weighted_pct, n_population
      cognitive, archetype, combined, careers,
      learning_style_name, learning_style_detail,
      blind_spots, roadmap,
      bf_scores, bf_pcts, n_bf_pop,
      iq_answers, iq_session,
      lang  ('id' atau 'en')

    txt  : dict dari i18n/id.json atau en.json
    """
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=txt['pdf']['title'],
        author='Assessment App',
    )

    styles = _styles()
    story  = []

    # 1. Cover
    _build_cover(story, data, txt, styles)

    # 2. Executive Summary
    _build_exec_summary(story, data, txt, styles)

    # ── Full Report starts here ──
    lang = data.get('lang', 'id')
    full_lbl = txt['pdf']['full_report']
    story.append(Paragraph(full_lbl,
                           ParagraphStyle('fr', fontSize=10, textColor=C_GOLD,
                               fontName='Helvetica-Bold', letterSpacing=3,
                               spaceAfter=6)))
    _divider(story, color=C_GOLD)

    # 3. Sections
    _build_section_cognitive(story,    data, txt, styles)
    _build_section_personality(story,  data, txt, styles)
    _build_section_combined(story,     data, txt, styles)
    _build_section_career(story,       data, txt, styles)
    _build_section_learning(story,     data, txt, styles)
    _build_section_blindspots(story,   data, txt, styles)
    _build_section_roadmap(story,      data, txt, styles)

    # 4. IQ Review
    story.append(PageBreak())
    _build_iq_review(story, data, txt, styles)

    # 5. Appendix
    story.append(PageBreak())
    _build_appendix(story, data, txt, styles)

    doc.build(story)