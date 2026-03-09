"""
engine/scoring.py
─────────────────────────────────────────────────────────────────
Weighted IRT-inspired IQ scoring dan Cognitive Profile breakdown.

Filosofi:
  - Soal difficulty 1–7 dipakai sebagai bobot (bukan % benar biasa)
  - Setiap kategori soal dipetakan ke kemampuan kognitif spesifik
  - Cognitive profile = kekuatan & kelemahan relatif per domain
─────────────────────────────────────────────────────────────────
"""

import json, math

# Load IQ norms
with open('processed/iq_norms.json', encoding='utf-8') as f:
    _IQ_DATA = json.load(f)

IQ_NORMS     = _IQ_DATA['norms']
IQ_SCORE_MAP = _IQ_DATA['iq_score_map']
IQ_STATS     = _IQ_DATA['stats']
N_POP        = _IQ_DATA['n_population']

# ── Mapping kategori soal → kemampuan kognitif ──────────────────
CATEGORY_TO_COGNITIVE = {
    'Deret Angka':    'fluid',        # Fluid/Sequential Reasoning
    'Analogi Verbal': 'crystallized', # Crystallized Intelligence
    'Logika':         'abstract',     # Abstract Reasoning
    'Numerik':        'quantitative', # Quantitative Reasoning
    'Pola Visual':    'spatial',      # Spatial Intelligence

    # English keys (same mapping)
    'Number Sequences': 'fluid',
    'Verbal Analogies':  'crystallized',
    'Logic':             'abstract',
    'Numerical':         'quantitative',
    'Visual Patterns':   'spatial',
}

# Bobot maksimum per difficulty level
DIFFICULTY_WEIGHTS = {1: 1.0, 2: 1.5, 3: 2.0, 4: 2.5,
                      5: 3.0, 6: 3.5, 7: 4.0}

IQ_CATEGORY_TABLE = [
    (130, 'Very Superior',  '#f5a623'),
    (120, 'Superior',       '#27ae60'),
    (110, 'High Average',   '#3b82f6'),
    (90,  'Average',        '#8b5cf6'),
    (80,  'Low Average',    '#f97316'),
    (70,  'Below Average',  '#e74c3c'),
    (0,   'Well Below Avg', '#e74c3c'),
]


def weighted_score(answers, session):
    """
    Hitung weighted score berbasis difficulty.
    Return: (weighted_pct, raw_correct, raw_total, max_possible)
    """
    earned = 0.0
    max_possible = 0.0
    correct = 0

    for i, q in enumerate(session):
        w = DIFFICULTY_WEIGHTS.get(q.get('difficulty', 1), 1.0)
        max_possible += w
        if answers[i] == q['ans']:
            earned += w
            correct += 1

    pct = (earned / max_possible * 100) if max_possible > 0 else 0
    return pct, correct, len(session), max_possible


def score_to_iq(answers, session):
    """
    Konversi weighted score → estimasi IQ via norm table.
    Return dict lengkap.
    """
    w_pct, correct, total, max_w = weighted_score(answers, session)

    key       = str(min(100, max(0, round(w_pct))))
    percentile = IQ_NORMS.get(key, 50.0)
    pct_idx   = min(100, max(0, round(percentile)))
    iq        = IQ_SCORE_MAP[pct_idx]

    label, color = 'Average', '#8b5cf6'
    for threshold, lbl, col in IQ_CATEGORY_TABLE:
        if iq >= threshold:
            label, color = lbl, col
            break

    desc_id = {
        'Very Superior':  'Kecerdasan sangat luar biasa — berada di 2% teratas populasi.',
        'Superior':       'Kecerdasan di atas rata-rata yang signifikan.',
        'High Average':   'Kecerdasan di atas rata-rata umum.',
        'Average':        'Kecerdasan rata-rata — mayoritas populasi berada di rentang ini.',
        'Low Average':    'Kecerdasan sedikit di bawah rata-rata.',
        'Below Average':  'Kecerdasan di bawah rata-rata.',
        'Well Below Avg': 'Kecerdasan jauh di bawah rata-rata.',
    }
    desc_en = {
        'Very Superior':  'Exceptional intelligence — in the top 2% of the population.',
        'Superior':       'Significantly above-average intelligence.',
        'High Average':   'Above-average intelligence.',
        'Average':        'Average intelligence — most people fall in this range.',
        'Low Average':    'Slightly below-average intelligence.',
        'Below Average':  'Below-average intelligence.',
        'Well Below Avg': 'Well below-average intelligence.',
    }

    return {
        'iq':         iq,
        'label':      label,
        'color':      color,
        'desc_id':    desc_id.get(label, ''),
        'desc_en':    desc_en.get(label, ''),
        'percentile': round(percentile),
        'correct':    correct,
        'total':      total,
        'weighted_pct': round(w_pct, 1),
        'n_population': N_POP,
    }


def build_cognitive_profile(answers, session):
    """
    Bangun profil kognitif per domain dari performa kategori soal.

    Return: dict per cognitive domain dengan:
      - score_pct : % weighted benar di domain ini
      - level     : 'Very High' / 'High' / 'Average' / 'Low' / 'Very Low'
      - rank      : ranking relatif dibanding domain lain (1=terbaik)
      - questions : total soal di domain ini
    """
    domains = {}  # domain_key → {earned, max, count}

    for i, q in enumerate(session):
        cat = q.get('category', '')
        dom = CATEGORY_TO_COGNITIVE.get(cat)
        if not dom:
            continue
        w = DIFFICULTY_WEIGHTS.get(q.get('difficulty', 1), 1.0)
        if dom not in domains:
            domains[dom] = {'earned': 0.0, 'max': 0.0, 'count': 0}
        domains[dom]['max']   += w
        domains[dom]['count'] += 1
        if answers[i] == q['ans']:
            domains[dom]['earned'] += w

    result = {}
    for dom, d in domains.items():
        pct = (d['earned'] / d['max'] * 100) if d['max'] > 0 else 0
        if pct >= 85:   level = 'Very High'
        elif pct >= 68: level = 'High'
        elif pct >= 45: level = 'Average'
        elif pct >= 28: level = 'Low'
        else:           level = 'Very Low'
        result[dom] = {
            'score_pct': round(pct, 1),
            'level':     level,
            'questions': d['count'],
        }

    # Ranking
    sorted_doms = sorted(result.keys(), key=lambda k: result[k]['score_pct'], reverse=True)
    for rank, dom in enumerate(sorted_doms, 1):
        result[dom]['rank'] = rank

    return result


COGNITIVE_LEVEL_COLORS = {
    'Very High': '#27ae60',
    'High':      '#3b82f6',
    'Average':   '#8b5cf6',
    'Low':       '#f97316',
    'Very Low':  '#e74c3c',
}

COGNITIVE_LEVEL_ID = {
    'Very High': 'Sangat Tinggi',
    'High':      'Tinggi',
    'Average':   'Rata-rata',
    'Low':       'Rendah',
    'Very Low':  'Sangat Rendah',
}

COGNITIVE_DESC_ID = {
    'fluid': {
        'Very High': 'Kemampuan penalaran sekuensial dan pola angka sangat kuat — kamu cepat mengenali struktur tersembunyi dalam data.',
        'High':      'Penalaran cair di atas rata-rata — baik dalam mendeteksi pola dan membuat prediksi.',
        'Average':   'Penalaran cair rata-rata — dapat mengikuti pola umum dengan baik.',
        'Low':       'Perlu latihan lebih pada deret dan pola angka untuk memperkuat penalaran sekuensial.',
        'Very Low':  'Penalaran sekuensial perlu perhatian khusus — latihan rutin deret angka sangat direkomendasikan.',
    },
    'crystallized': {
        'Very High': 'Kecerdasan verbal dan pengetahuan terkristalisasi sangat tinggi — kosakata dan pemahaman konseptual kamu luar biasa.',
        'High':      'Kemampuan verbal kuat — baik dalam memahami hubungan antar konsep dan analogi.',
        'Average':   'Kemampuan verbal rata-rata — dapat memahami analogi dan hubungan konsep yang umum.',
        'Low':       'Perlu memperluas kosakata dan pemahaman konseptual melalui membaca lebih banyak.',
        'Very Low':  'Kecerdasan verbal perlu pengembangan signifikan — disarankan membaca rutin lintas topik.',
    },
    'abstract': {
        'Very High': 'Penalaran abstrak dan logis sangat kuat — kamu unggul dalam berpikir sistematis dan deduktif.',
        'High':      'Kemampuan logis di atas rata-rata — baik dalam menganalisis premis dan menarik kesimpulan valid.',
        'Average':   'Penalaran logis rata-rata — dapat mengikuti argumen sederhana hingga menengah.',
        'Low':       'Perlu latihan lebih pada penalaran deduktif dan silogisme.',
        'Very Low':  'Penalaran abstrak perlu pengembangan — latihan logika formal sangat direkomendasikan.',
    },
    'quantitative': {
        'Very High': 'Kemampuan numerik dan matematika sangat tinggi — kamu nyaman dengan kalkulasi dan konsep kuantitatif kompleks.',
        'High':      'Kemampuan numerik di atas rata-rata — baik dalam kalkulasi dan pemecahan masalah matematika.',
        'Average':   'Kemampuan numerik rata-rata — dapat menyelesaikan soal matematika tingkat menengah.',
        'Low':       'Perlu memperkuat fondasi matematika dan latihan kalkulasi rutin.',
        'Very Low':  'Kemampuan numerik perlu perhatian serius — disarankan review konsep matematika dasar.',
    },
    'spatial': {
        'Very High': 'Kecerdasan spasial dan visual sangat tinggi — kamu unggul dalam membayangkan dan memanipulasi objek dalam ruang.',
        'High':      'Kemampuan spasial di atas rata-rata — baik dalam mengenali pola visual dan hubungan geometris.',
        'Average':   'Kecerdasan spasial rata-rata — dapat memahami pola visual yang umum.',
        'Low':       'Perlu latihan lebih pada soal pola visual, rotasi mental, dan geometri.',
        'Very Low':  'Kecerdasan spasial perlu pengembangan — puzzle visual dan latihan geometri sangat membantu.',
    },
}

COGNITIVE_DESC_EN = {
    'fluid': {
        'Very High': 'Exceptional sequential reasoning and pattern recognition — you rapidly identify hidden structures in data.',
        'High':      'Above-average fluid reasoning — good at detecting patterns and making predictions.',
        'Average':   'Average fluid reasoning — able to follow common patterns reliably.',
        'Low':       'More practice with number sequences and patterns recommended to strengthen sequential reasoning.',
        'Very Low':  'Sequential reasoning needs focused attention — regular number sequence drills strongly recommended.',
    },
    'crystallized': {
        'Very High': 'Exceptional verbal intelligence and crystallized knowledge — your vocabulary and conceptual understanding are outstanding.',
        'High':      'Strong verbal ability — good at understanding relationships between concepts and analogies.',
        'Average':   'Average verbal ability — can handle common analogies and conceptual relationships.',
        'Low':       'Broaden vocabulary and conceptual understanding through more reading.',
        'Very Low':  'Verbal intelligence needs significant development — regular cross-topic reading is strongly advised.',
    },
    'abstract': {
        'Very High': 'Very strong abstract and logical reasoning — you excel at systematic and deductive thinking.',
        'High':      'Above-average logical ability — good at analyzing premises and drawing valid conclusions.',
        'Average':   'Average logical reasoning — can follow simple to intermediate arguments.',
        'Low':       'More practice with deductive reasoning and syllogisms recommended.',
        'Very Low':  'Abstract reasoning needs development — formal logic practice strongly recommended.',
    },
    'quantitative': {
        'Very High': 'Very high numerical and mathematical ability — you are comfortable with complex quantitative concepts.',
        'High':      'Above-average numerical ability — good at calculations and mathematical problem-solving.',
        'Average':   'Average numerical ability — can solve intermediate-level math problems.',
        'Low':       'Strengthen mathematical foundations with regular calculation practice.',
        'Very Low':  'Numerical ability needs serious attention — review of basic math concepts advised.',
    },
    'spatial': {
        'Very High': 'Exceptional spatial and visual intelligence — you excel at imagining and manipulating objects in space.',
        'High':      'Above-average spatial ability — good at recognizing visual patterns and geometric relationships.',
        'Average':   'Average spatial intelligence — can understand common visual patterns.',
        'Low':       'More practice with visual patterns, mental rotation, and geometry recommended.',
        'Very Low':  'Spatial intelligence needs development — visual puzzles and geometry practice are very helpful.',
    },
}


# ── Public helper dipakai app.py ────────────────────────────────
def get_percentile_bf(trait, score):
    """Lookup percentile Big Five dari norms.json."""
    import json
    with open('processed/norms.json', encoding='utf-8') as f:
        norms = json.load(f)['norms']
    return norms[trait].get(str(min(100,max(0,round(score)))), 50.0)