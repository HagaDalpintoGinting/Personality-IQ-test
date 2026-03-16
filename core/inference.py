"""
core/inference.py
────────────────────────────────────────────────────────────
Inference Mechanism — semua perhitungan skor, normalisasi,
dan rule-based profiling. TIDAK ada AI di sini.

Alur:
  1. score_bigfive()     → raw + normalized per dimensi
  2. score_iq()          → weighted IQ estimate
  3. build_cognitive()   → 5 domain kognitif
  4. compute_careers()   → career confidence berdasarkan rules
  5. compute_archetype() → tipe kepribadian dari OCEAN
  6. compute_combined()  → profil gabungan IQ × OCEAN
  7. compute_learning_style()
  8. compute_blind_spots()
  9. compute_roadmap()
────────────────────────────────────────────────────────────
"""

import json


def _erf_inv(x):
    """Approximate inverse error function."""
    import math
    a = 0.147
    ln = math.log(1 - x * x)
    part = (2 / (math.pi * a)) + ln / 2
    return (1 if x >= 0 else -1) * math.sqrt(
        math.sqrt(part * part - ln / a) - part
    )

import math
from pathlib import Path

from core.knowledge_base import (
    BF_DIMENSIONS, BF_LEVELS, BF_QUESTIONS, BF_BY_TRAIT,
    IQ_QUESTIONS, IQ_CATEGORY_MAP, IQ_COGNITIVE_DOMAINS,
    CAREER_KB, get_bf_level,
)

# ── Load norma dari processed/ ──────────────────────────────
_norms_cache    = None
_iq_norms_cache = None

def reset_cache():
    global _norms_cache, _iq_norms_cache
    _norms_cache    = None
    _iq_norms_cache = None

def _load_norms():
    global _norms_cache
    if _norms_cache is None:
        try:
            with open('processed/norms.json', encoding='utf-8') as f:
                raw = json.load(f)
            # Pastikan format punya key 'norms' per trait
            if 'norms' in raw and isinstance(raw['norms'], dict) and 'O' in raw['norms']:
                _norms_cache = raw  # format sudah benar
            else:
                # Fallback kalau format berbeda
                _norms_cache = {
                    'norms': {t: {str(i): float(i) for i in range(101)} for t in 'OCEAN'},
                    'n_population': 1000
                }
        except Exception:
            _norms_cache = {
                'norms': {t: {str(i): float(i) for i in range(101)} for t in 'OCEAN'},
                'n_population': 1000
            }
    return _norms_cache

def _load_iq_norms():
    global _iq_norms_cache
    if _iq_norms_cache is None:
        try:
            with open('processed/iq_norms.json', encoding='utf-8') as f:
                raw = json.load(f)

            # Normalisasi format — support dua format:
            # Format A (buatan kita): {'norms': {'0': pct}, 'iq_score_map': [...]}
            # Format B (file user):   {'norms': {'0': pct}, 'iq_score_map': [...]}
            norms_dict   = raw.get('norms', {})
            iq_score_map = raw.get('iq_score_map', None)

            # Kalau tidak ada iq_score_map, buat dari norms
            if iq_score_map is None:
                import math
                def _iq_from_pct(p):
                    # Inverse normal: pct -> IQ
                    # Approx: IQ = 100 + 15 * z
                    if p <= 0: return 55
                    if p >= 100: return 145
                    # Simple linear map
                    return max(55, min(145, int(55 + (p / 100) * 90)))
                iq_score_map = [_iq_from_pct(i) for i in range(101)]

            _iq_norms_cache = {
                'norms':        norms_dict,
                'iq_score_map': iq_score_map,
                'n_population': raw.get('n_population', 2051),
            }
        except Exception as e:
            import math
            def _cdf(x):
                z = (x - 100) / 15
                return round(0.5 * (1 + math.erf(z / math.sqrt(2))) * 100, 1)
            _iq_norms_cache = {
                'norms':        {str(i): _cdf(max(55, min(145, int(55+(i/40)*90)))) for i in range(101)},
                'iq_score_map': [max(55, min(145, int(55 + (i/100)*90))) for i in range(101)],
                'n_population': 1000,
            }
    return _iq_norms_cache


# ══════════════════════════════════════════════════════════════
# 1. BIG FIVE SCORING
# ══════════════════════════════════════════════════════════════
def score_bigfive(answers: list, session: list) -> dict:
    """
    answers : list nilai 1-5 (index sesuai session)
    session : list (qid, trait, text, text_en, reversed)

    Return:
    {
      'O': {'raw': 38, 'normalized': 76.0, 'percentile': 81.2,
            'level': 'high', 'level_id': 'Tinggi', 'level_en': 'High'},
      ...
    }
    """
    norms = _load_norms()
    # Format: {"norms": {"O": {"0": pct, ...}, "C": {...}, ...}}
    bf_norms = norms['norms']   # dict per trait
    n_pop    = norms.get('n_population', 874434)

    raw = {t: 0 for t in 'OCEAN'}
    cnt = {t: 0 for t in 'OCEAN'}

    for i, (qid, trait, _, _, reversed_) in enumerate(session):
        a = answers[i]
        if a is None:
            continue
        v = (6 - a) if reversed_ else a
        raw[trait] += v
        cnt[trait] += 1

    result = {}
    for t in 'OCEAN':
        if cnt[t] == 0:
            result[t] = {'raw': 0, 'normalized': 50.0, 'percentile': 50.0,
                         'level': 'average', 'level_id': 'Rata-rata', 'level_en': 'Average'}
            continue

        # Normalisasi ke 0-100
        max_raw = cnt[t] * 5
        normalized = round((raw[t] / max_raw) * 100, 1)

        # Percentile dari norm table
        key = str(min(100, max(0, round(normalized))))
        percentile = bf_norms.get(t, {}).get(key, 50.0)

        # Level
        lvl = get_bf_level(normalized)

        result[t] = {
            'raw':        raw[t],
            'normalized': normalized,
            'percentile': round(percentile, 1),
            'level':      lvl['key'],
            'level_id':   lvl['id'],
            'level_en':   lvl['en'],
        }

    result['_n_population'] = n_pop
    return result


def bf_scores_to_db_rows(session_id: int, bf_result: dict) -> list[dict]:
    """Convert output score_bigfive() → list siap save_scores()."""
    rows = []
    for t in 'OCEAN':
        d = bf_result[t]
        rows.append({
            'dimension':  t,
            'raw_score':  d['raw'],
            'normalized': d['normalized'],
            'percentile': d['percentile'],
            'level':      d['level'],
        })
    return rows


def bf_answers_to_db_rows(session: list, answers: list) -> list[dict]:
    """Convert session + answers → list siap save_answers()."""
    rows = []
    for i, (qid, trait, _, _, reversed_) in enumerate(session):
        a = answers[i]
        rows.append({
            'question_id': qid,
            'dimension':   trait,
            'value':       a if a is not None else 0,
            'is_correct':  None,
            'difficulty':  None,
        })
    return rows


# ══════════════════════════════════════════════════════════════
# 2. IQ SCORING (weighted)
# ══════════════════════════════════════════════════════════════
def score_iq(answers: list, session: list) -> dict:
    """
    answers : list index jawaban yang dipilih (0-3) atau None
    session : list dict dari knowledge_base.IQ_QUESTIONS (localized)

    Return:
    {
      'iq': 112, 'label': 'High Average', 'color': '#3b82f6',
      'percentile': 79, 'correct': 28, 'total': 40,
      'weighted_pct': 72.4, 'n_population': 2051
    }
    """
    iq_data      = _load_iq_norms()
    iq_norms     = iq_data['norms']        # {"0": 0.0, ..., "100": 99.9}
    n_pop        = iq_data.get('n_population', 2051)
    # iq_score_map: list 101 IQ values (index = percentile 0-100)
    # Jika tidak ada di file, gunakan formula standar IQ = 100 + 15*z
    if 'iq_score_map' in iq_data:
        iq_score_map = iq_data['iq_score_map']
    else:
        import math
        iq_score_map = [
            max(55, min(145, round(100 + 15 * math.sqrt(2) * _erf_inv(2 * (i/100) - 1)))
                if 0 < i < 100 else (55 if i == 0 else 145))
            for i in range(101)
        ]

    correct   = 0
    total     = len(session)
    weighted_sum = 0.0
    max_weight   = 0.0

    for i, q in enumerate(session):
        diff   = q.get('difficulty', 4)
        weight = diff  # difficulty 1-7 langsung jadi bobot
        max_weight += weight
        if answers[i] is not None and answers[i] == q['ans']:
            correct      += 1
            weighted_sum += weight

    w_pct = (weighted_sum / max_weight * 100) if max_weight > 0 else 0

    # Lookup percentile dari weighted score
    key    = str(min(100, max(0, round(w_pct))))
    pctile = float(iq_norms.get(key, 50.0))
    # iq_score_map: list 101 nilai, index = persentil 0-100
    iq_idx = min(100, max(0, round(pctile)))
    iq     = int(iq_score_map[iq_idx])

    # Label & color
    IQ_CATS = [
        (130, 'Very Superior',  '#f5a623'),
        (120, 'Superior',       '#27ae60'),
        (110, 'High Average',   '#3b82f6'),
        (90,  'Average',        '#8b5cf6'),
        (80,  'Low Average',    '#f97316'),
        (70,  'Below Average',  '#e74c3c'),
        (0,   'Well Below Avg', '#e74c3c'),
    ]
    label, color = 'Average', '#8b5cf6'
    for threshold, lbl, col in IQ_CATS:
        if iq >= threshold:
            label, color = lbl, col
            break

    return {
        'iq':           iq,
        'label':        label,
        'color':        color,
        'percentile':   round(pctile),
        'correct':      correct,
        'total':        total,
        'weighted_pct': round(w_pct, 1),
        'n_population': n_pop,
    }


def build_cognitive_profile(answers: list, session: list) -> dict:
    """
    Return 5 domain kognitif dari performance per kategori IQ.
    {
      'fluid': {'score_pct': 62.5, 'level': 'Average', 'rank': 3},
      ...
    }
    """
    cat_scores = {}
    for i, q in enumerate(session):
        cat = q.get('category', q.get('cat_id', ''))
        if cat not in cat_scores:
            cat_scores[cat] = {'weighted': 0.0, 'max_w': 0.0}
        diff   = q.get('difficulty', 4)
        weight = diff
        cat_scores[cat]['max_w'] += weight
        if answers[i] is not None and answers[i] == q['ans']:
            cat_scores[cat]['weighted'] += weight

    LEVEL_TABLE = [
        (80, 'Exceptional'),
        (65, 'Strong'),
        (45, 'Average'),
        (25, 'Developing'),
        (0,  'Needs Work'),
    ]
    LEVEL_ID = {
        'Exceptional': 'Luar Biasa',
        'Strong':      'Kuat',
        'Average':     'Rata-rata',
        'Developing':  'Berkembang',
        'Needs Work':  'Perlu Latihan',
    }

    profile = {}
    for cat, d in cat_scores.items():
        pct  = (d['weighted'] / d['max_w'] * 100) if d['max_w'] > 0 else 0
        cog  = IQ_CATEGORY_MAP.get(cat, {}).get('cognitive', cat.lower())
        lvl  = next((l[1] for l in LEVEL_TABLE if pct >= l[0]), 'Needs Work')
        profile[cog] = {'score_pct': round(pct, 1), 'level': lvl, 'level_id': LEVEL_ID[lvl]}

    # Rank (1=strongest)
    ranked = sorted(profile.items(), key=lambda x: x[1]['score_pct'], reverse=True)
    for rank, (dom, _) in enumerate(ranked, 1):
        profile[dom]['rank'] = rank

    return profile


def iq_answers_to_db_rows(session: list, answers: list) -> list[dict]:
    rows = []
    for i, q in enumerate(session):
        a = answers[i]
        rows.append({
            'question_id': q.get('id', f'IQ_{i}'),
            'dimension':   q.get('category', q.get('cat_id', '')),
            'value':       a if a is not None else -1,
            'is_correct':  1 if (a is not None and a == q['ans']) else 0,
            'difficulty':  q.get('difficulty', 4),
        })
    return rows


def iq_scores_to_db_rows(iq_result: dict, cognitive: dict) -> list[dict]:
    rows = [{
        'dimension':  'IQ',
        'raw_score':  iq_result['correct'],
        'normalized': iq_result['weighted_pct'],
        'percentile': iq_result['percentile'],
        'level':      iq_result['label'],
    }]
    for dom, d in cognitive.items():
        rows.append({
            'dimension':  dom,
            'raw_score':  d['score_pct'],
            'normalized': d['score_pct'],
            'percentile': d['score_pct'],
            'level':      d['level'],
        })
    return rows


# ══════════════════════════════════════════════════════════════
# 3. CAREER SCORING (rule-based)
# ══════════════════════════════════════════════════════════════
def compute_careers(bf_scores: dict, iq: int, lang: str = 'id', top_n: int = 5) -> list[dict]:
    """
    bf_scores: {'O':76,'C':82,...} (normalized 0-100)
    Return top_n karir dengan confidence 0-100.
    """
    results = []
    for c in CAREER_KB:
        score = 0.0
        for trait, w in c['weights'].items():
            s = bf_scores.get(trait, 50) / 100
            score += w * s

        # IQ contribution
        iq_norm = min(1.0, max(0.0, (iq - 70) / 80))
        score  += c['iq_weight'] * iq_norm

        # IQ minimum penalty
        if iq < c['iq_min']:
            penalty = (c['iq_min'] - iq) / 50
            score  -= penalty * 0.3

        # Normalize ke 0-100
        confidence = min(100, max(0, round(score * 100 + 50)))
        results.append({
            'name':       c['id'] if lang == 'id' else c['en'],
            'confidence': confidence,
        })

    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:top_n]


# ══════════════════════════════════════════════════════════════
# 4. ARCHETYPE (rule-based)
# ══════════════════════════════════════════════════════════════
ARCHETYPES = [
    {
        'tag': 'THE VISIONARY', 'name_id': 'Sang Visioner', 'name_en': 'The Visionary',
        'desc_id': 'Pemikir inovatif yang menggabungkan kreativitas tinggi dengan disiplin eksekusi. Kamu melihat pola yang tidak dilihat orang lain dan mampu mewujudkannya.',
        'desc_en': 'An innovative thinker who combines high creativity with disciplined execution. You see patterns others miss and can bring them to life.',
        'rule': lambda s: s['O'] >= 70 and s['C'] >= 65,
    },
    {
        'tag': 'THE CATALYST', 'name_id': 'Sang Katalis', 'name_en': 'The Catalyst',
        'desc_id': 'Energi sosialmu yang tinggi dipadukan rasa ingin tahu membuatmu agen perubahan alami. Kamu menginspirasi orang lain untuk bergerak.',
        'desc_en': 'Your high social energy combined with curiosity makes you a natural change agent. You inspire others to move.',
        'rule': lambda s: s['O'] >= 65 and s['E'] >= 70,
    },
    {
        'tag': 'THE ARCHITECT', 'name_id': 'Sang Arsitek', 'name_en': 'The Architect',
        'desc_id': 'Sistematis dan analitis. Kamu membangun solusi yang solid dan tahan lama, bukan solusi cepat yang mudah runtuh.',
        'desc_en': 'Systematic and analytical. You build solid, lasting solutions rather than quick fixes that crumble.',
        'rule': lambda s: s['C'] >= 70 and s['N'] < 50,
    },
    {
        'tag': 'THE DIPLOMAT', 'name_id': 'Sang Diplomat', 'name_en': 'The Diplomat',
        'desc_id': 'Empatik dan pandai membaca situasi sosial. Kamu menjembatani perbedaan dan menciptakan harmoni di sekitarmu.',
        'desc_en': 'Empathetic and socially astute. You bridge differences and create harmony around you.',
        'rule': lambda s: s['A'] >= 70 and s['E'] >= 60,
    },
    {
        'tag': 'THE GUARDIAN', 'name_id': 'Sang Penjaga', 'name_en': 'The Guardian',
        'desc_id': 'Handal dan bisa diandalkan. Orang tahu bahwa jika kamu berkomitmen, pasti selesai. Fondasi yang membuat tim berfungsi.',
        'desc_en': 'Reliable and dependable. People know if you commit, it gets done. The foundation that makes teams function.',
        'rule': lambda s: s['C'] >= 70 and s['A'] >= 65,
    },
    {
        'tag': 'THE EXPLORER', 'name_id': 'Sang Penjelajah', 'name_en': 'The Explorer',
        'desc_id': 'Spontan dan haus pengalaman baru. Kamu berkembang dalam lingkungan dinamis dan sering menemukan peluang yang tidak disadari orang lain.',
        'desc_en': 'Spontaneous and hungry for new experiences. You thrive in dynamic environments and often spot opportunities others overlook.',
        'rule': lambda s: s['O'] >= 70 and s['C'] < 50,
    },
    {
        'tag': 'THE COMMANDER', 'name_id': 'Sang Komandan', 'name_en': 'The Commander',
        'desc_id': 'Tegas, percaya diri, dan natural dalam memimpin. Kamu tidak ragu mengambil keputusan sulit demi hasil yang lebih besar.',
        'desc_en': 'Decisive, confident, and naturally commanding. You don\'t hesitate to make tough decisions for bigger outcomes.',
        'rule': lambda s: s['E'] >= 70 and s['A'] < 50,
    },
    {
        'tag': 'THE COUNSELOR', 'name_id': 'Sang Konselor', 'name_en': 'The Counselor',
        'desc_id': 'Pendengar yang dalam dan pendukung yang tulus. Orang datang kepadamu karena kamu memahami tanpa menghakimi.',
        'desc_en': 'A deep listener and genuine supporter. People come to you because you understand without judging.',
        'rule': lambda s: s['A'] >= 70 and s['N'] >= 55,
    },
    {
        'tag': 'THE ANALYST', 'name_id': 'Sang Analis', 'name_en': 'The Analyst',
        'desc_id': 'Logis dan metodis. Kamu tidak puas dengan "kira-kira" dan selalu mencari data dan bukti sebelum menyimpulkan.',
        'desc_en': 'Logical and methodical. You\'re never satisfied with "roughly" and always seek data and evidence before concluding.',
        'rule': lambda s: s['O'] >= 60 and s['C'] >= 65 and s['E'] < 55,
    },
    {
        'tag': 'THE PERFORMER', 'name_id': 'Sang Performer', 'name_en': 'The Performer',
        'desc_id': 'Ekspresif, enerjik, dan dicintai banyak orang. Kamu membawa kehidupan ke ruangan apapun yang kamu masuki.',
        'desc_en': 'Expressive, energetic, and loved by many. You bring life to any room you enter.',
        'rule': lambda s: s['E'] >= 70 and s['O'] >= 60,
    },
    {
        'tag': 'THE SENTINEL', 'name_id': 'Sang Sentinel', 'name_en': 'The Sentinel',
        'desc_id': 'Stabil, terorganisir, dan dapat diandalkan dalam jangka panjang. Kamu adalah batu fondasi dalam tim dan keluarga.',
        'desc_en': 'Stable, organized, and reliable over the long term. You are the cornerstone of teams and families.',
        'rule': lambda s: s['C'] >= 65 and s['N'] < 40,
    },
    {
        'tag': 'THE MEDIATOR', 'name_id': 'Sang Mediator', 'name_en': 'The Mediator',
        'desc_id': 'Sensitif secara emosional namun penuh empati. Nilai-nilai pribadimu sangat kuat dan kamu berjuang untuk apa yang kamu yakini.',
        'desc_en': 'Emotionally sensitive yet deeply empathetic. Your personal values are strong and you fight for what you believe in.',
        'rule': lambda s: s['A'] >= 65 and s['N'] >= 60,
    },
    {
        'tag': 'THE STRATEGIST', 'name_id': 'Sang Strateg', 'name_en': 'The Strategist',
        'desc_id': 'Kamu berpikir beberapa langkah ke depan. Kamu melihat gambaran besar, memahami sistem, dan merancang jalan menuju tujuan.',
        'desc_en': 'You think several steps ahead. You see the big picture, understand systems, and design paths to goals.',
        'rule': lambda s: s['O'] >= 65 and s['C'] >= 60 and s['E'] < 60,
    },
    {
        'tag': 'THE INDIVIDUALIST', 'name_id': 'Sang Individualis', 'name_en': 'The Individualist',
        'desc_id': 'Mandiri dan punya identitas yang kuat. Kamu tidak mudah dipengaruhi orang lain dan punya visi unik tentang duniamu.',
        'desc_en': 'Independent with a strong identity. You\'re not easily swayed and have a unique vision of your world.',
        'rule': lambda s: s['O'] >= 65 and s['A'] < 50 and s['E'] < 55,
    },
]

def compute_archetype(bf_scores: dict, lang: str = 'id') -> dict:
    """Return archetype terbaik yang cocok dengan skor OCEAN."""
    for arch in ARCHETYPES:
        if arch['rule'](bf_scores):
            return {
                'tag':  arch['tag'],
                'name': arch['name_id'] if lang == 'id' else arch['name_en'],
                'desc': arch['desc_id'] if lang == 'id' else arch['desc_en'],
            }
    # Default
    return {
        'tag':  'THE BALANCED',
        'name': 'Sang Seimbang' if lang == 'id' else 'The Balanced',
        'desc': ('Profil kepribadianmu seimbang di semua dimensi — fleksibel dan adaptif dalam berbagai situasi.'
                 if lang == 'id' else
                 'Your personality profile is balanced across all dimensions — flexible and adaptive in various situations.'),
    }


# ══════════════════════════════════════════════════════════════
# 5. COMBINED IQ × PERSONALITY
# ══════════════════════════════════════════════════════════════
COMBINED_PROFILES = [
    {
        'name_id': 'Jenius yang Bersemangat',  'name_en': 'The Inspired Genius',
        'desc_id': 'Kecerdasan tinggi yang diperkuat oleh keterbukaan dan rasa ingin tahu tanpa batas. Potensimu hampir tak terbatas jika diarahkan dengan tepat.',
        'desc_en': 'High intelligence amplified by boundless openness and curiosity. Your potential is near limitless when properly directed.',
        'action_id': 'Fokus pada satu proyek besar yang benar-benar bermakna bagimu.',
        'action_en': 'Focus on one big project that truly matters to you.',
        'rule': lambda iq, s: iq >= 115 and s['O'] >= 70,
    },
    {
        'name_id': 'Arsitek Ide',  'name_en': 'Architect of Ideas',
        'desc_id': 'Kecerdasan analitismu dikombinasikan dengan disiplin tinggi menghasilkan kemampuan membangun sistem yang kompleks dengan presisi.',
        'desc_en': 'Your analytical intelligence combined with high discipline produces the ability to build complex systems with precision.',
        'action_id': 'Ambil proyek yang membutuhkan perencanaan jangka panjang.',
        'action_en': 'Take on a project that requires long-term planning.',
        'rule': lambda iq, s: iq >= 110 and s['C'] >= 70,
    },
    {
        'name_id': 'Pemimpin Transformasional',  'name_en': 'Transformational Leader',
        'desc_id': 'IQ-mu di atas rata-rata dikombinasikan dengan karisma sosial yang kuat — kombinasi ideal untuk memimpin dan menginspirasi.',
        'desc_en': 'Your above-average IQ combined with strong social charisma — the ideal combination to lead and inspire.',
        'action_id': 'Cari peran kepemimpinan yang memungkinkanmu mempengaruhi banyak orang.',
        'action_en': 'Seek leadership roles where you can influence many people.',
        'rule': lambda iq, s: iq >= 105 and s['E'] >= 70,
    },
    {
        'name_id': 'Jenius Tersembunyi',  'name_en': 'Hidden Genius',
        'desc_id': 'Kecerdasan tinggi yang bekerja di balik layar. Kamu lebih suka hasil nyata daripada pengakuan, dan sering menjadi otak di balik kesuksesan tim.',
        'desc_en': 'High intelligence working behind the scenes. You prefer tangible results over recognition, often being the brain behind team success.',
        'action_id': 'Dokumentasikan kontribusimu agar dampakmu diakui.',
        'action_en': 'Document your contributions so your impact is recognized.',
        'rule': lambda iq, s: iq >= 110 and s['E'] < 50,
    },
    {
        'name_id': 'Pemikir Empatik',  'name_en': 'Empathic Thinker',
        'desc_id': 'Kecerdasan yang diarahkan untuk memahami manusia. Kamu unggul dalam membaca situasi sosial dan menciptakan solusi yang benar-benar membantu orang.',
        'desc_en': 'Intelligence directed at understanding people. You excel at reading social situations and creating solutions that genuinely help.',
        'action_id': 'Manfaatkan kemampuanmu di bidang yang berdampak sosial langsung.',
        'action_en': 'Apply your abilities in fields with direct social impact.',
        'rule': lambda iq, s: iq >= 100 and s['A'] >= 70,
    },
    {
        'name_id': 'Potensi Berkembang',  'name_en': 'Growing Potential',
        'desc_id': 'Kamu dalam fase membangun fondasi. Kombinasi kepribadianmu sudah tepat — tinggal arahkan energi ini dengan konsisten.',
        'desc_en': 'You\'re in a foundation-building phase. Your personality combination is right — just channel this energy consistently.',
        'action_id': 'Tetapkan satu tujuan 90-hari yang terukur dan mulai hari ini.',
        'action_en': 'Set one measurable 90-day goal and start today.',
        'rule': lambda iq, s: iq < 100 and s['C'] >= 65,
    },
    {
        'name_id': 'Jiwa yang Bebas',  'name_en': 'Free Spirit',
        'desc_id': 'Kreativitas dan spontanitasmu adalah asetmu. Kamu berhasil paling baik di lingkungan yang memberi kebebasan bereksperimen.',
        'desc_en': 'Creativity and spontaneity are your assets. You succeed best in environments that allow freedom to experiment.',
        'action_id': 'Cari atau ciptakan lingkungan kerja yang mendukung kebebasan eksplorasi.',
        'action_en': 'Find or create a work environment that supports freedom of exploration.',
        'rule': lambda iq, s: True,  # catch-all
    },
]

def compute_combined(iq: int, bf_scores: dict, lang: str = 'id') -> dict:
    for p in COMBINED_PROFILES:
        if p['rule'](iq, bf_scores):
            return {
                'name':   p['name_id'] if lang == 'id' else p['name_en'],
                'desc':   p['desc_id'] if lang == 'id' else p['desc_en'],
                'action': p['action_id'] if lang == 'id' else p['action_en'],
            }
    return {
        'name': 'Profil Unik' if lang == 'id' else 'Unique Profile',
        'desc': '', 'action': '',
    }


# ══════════════════════════════════════════════════════════════
# 6. LEARNING STYLE
# ══════════════════════════════════════════════════════════════
def compute_learning_style(bf_scores: dict, cognitive: dict, lang: str = 'id') -> tuple[str, dict]:
    o, c, e, a = bf_scores.get('O',50), bf_scores.get('C',50), bf_scores.get('E',50), bf_scores.get('A',50)
    spatial = cognitive.get('spatial', {}).get('score_pct', 50)
    fluid   = cognitive.get('fluid',   {}).get('score_pct', 50)

    if spatial >= 60 and o >= 65:
        style = 'visual'
    elif e >= 65 and a >= 60:
        style = 'auditory'
    elif c >= 65 and fluid >= 60:
        style = 'read_write'
    else:
        style = 'kinesthetic'

    STYLES = {
        'visual': {
            'name_id': 'Visual', 'name_en': 'Visual',
            'desc_id': 'Kamu belajar paling baik melalui gambar, diagram, dan representasi visual. Mind mapping dan infografis sangat efektif untukmu.',
            'desc_en': 'You learn best through images, diagrams, and visual representations. Mind maps and infographics are highly effective for you.',
            'tips_id': ['Gunakan mind map untuk merangkum materi', 'Tonton video tutorial sebelum membaca teks', 'Buat diagram alur untuk konsep kompleks', 'Gunakan warna berbeda untuk kategorisasi catatan'],
            'tips_en': ['Use mind maps to summarize material', 'Watch tutorial videos before reading text', 'Create flowcharts for complex concepts', 'Use different colors for note categorization'],
            'env_id': 'Ruang tenang dengan whiteboard atau layar besar',
            'env_en': 'Quiet space with a whiteboard or large screen',
        },
        'auditory': {
            'name_id': 'Auditory', 'name_en': 'Auditory',
            'desc_id': 'Kamu menyerap informasi terbaik melalui diskusi, penjelasan lisan, dan podcast. Belajar kelompok sangat cocok denganmu.',
            'desc_en': 'You absorb information best through discussion, verbal explanation, and podcasts. Group learning suits you well.',
            'tips_id': ['Diskusikan materi dengan teman setelah belajar', 'Rekam ringkasan dan dengarkan kembali', 'Jelaskan konsep kepada orang lain', 'Gunakan podcast dan audiobook'],
            'tips_en': ['Discuss material with friends after studying', 'Record summaries and listen back', 'Explain concepts to others', 'Use podcasts and audiobooks'],
            'env_id': 'Lingkungan kolaboratif dengan interaksi aktif',
            'env_en': 'Collaborative environment with active interaction',
        },
        'read_write': {
            'name_id': 'Reading-Writing', 'name_en': 'Reading-Writing',
            'desc_id': 'Kamu unggul dalam memproses teks tertulis. Membuat catatan detail dan membaca dokumen primer sangat efektif untukmu.',
            'desc_en': 'You excel at processing written text. Taking detailed notes and reading primary documents is highly effective for you.',
            'tips_id': ['Buat catatan lengkap dengan kata-katamu sendiri', 'Susun ringkasan tertulis setelah setiap sesi belajar', 'Baca buku teks dan artikel ilmiah', 'Gunakan flashcard berbasis teks'],
            'tips_en': ['Take complete notes in your own words', 'Write summaries after each study session', 'Read textbooks and academic articles', 'Use text-based flashcards'],
            'env_id': 'Ruang sunyi dengan akses perpustakaan atau jurnal',
            'env_en': 'Quiet space with access to library or journals',
        },
        'kinesthetic': {
            'name_id': 'Kinestetik', 'name_en': 'Kinesthetic',
            'desc_id': 'Kamu belajar paling baik melalui pengalaman langsung dan praktik. Simulasi, proyek nyata, dan eksperimen adalah metode idealmu.',
            'desc_en': 'You learn best through direct experience and practice. Simulations, real projects, and experiments are your ideal methods.',
            'tips_id': ['Langsung praktik setelah mempelajari teori', 'Gunakan proyek nyata sebagai media belajar', 'Ambil kursus berbasis lab atau workshop', 'Belajar sambil bergerak atau berdiri'],
            'tips_en': ['Practice immediately after learning theory', 'Use real projects as learning media', 'Take lab-based courses or workshops', 'Study while moving or standing'],
            'env_id': 'Lab, studio, atau lingkungan hands-on',
            'env_en': 'Lab, studio, or hands-on environment',
        },
    }

    s = STYLES[style]
    return s[f'name_{lang}'], {
        'desc':        s[f'desc_{lang}'],
        'tips':        s[f'tips_{lang}'],
        'environment': s[f'env_{lang}'],
    }


# ══════════════════════════════════════════════════════════════
# 7. BLIND SPOTS
# ══════════════════════════════════════════════════════════════
def compute_blind_spots(iq: int, bf_scores: dict, lang: str = 'id') -> list[dict]:
    """Return max 4 blind spots berdasarkan rules."""
    o,c,e,a,n = (bf_scores.get(t,50) for t in 'OCEAN')
    l = lang

    RULES = [
        {
            'cond': o >= 75 and c < 50,
            'title_id': 'Ide Tanpa Eksekusi', 'title_en': 'Ideas Without Execution',
            'desc_id': 'Kreativitasmu tinggi namun disiplin eksekusi rendah — risiko banyak ide yang tidak pernah selesai.',
            'desc_en': 'High creativity but low execution discipline — risk of many ideas that never get finished.',
            'mit_id': 'Gunakan sistem GTD (Getting Things Done) atau Pomodoro untuk menyelesaikan satu proyek sebelum memulai yang baru.',
            'mit_en': 'Use GTD or Pomodoro system to finish one project before starting new ones.',
        },
        {
            'cond': e >= 75 and a < 45,
            'title_id': 'Dominan Tanpa Empati', 'title_en': 'Dominant Without Empathy',
            'desc_id': 'Dorongan sosialmu yang kuat tanpa diimbangi empati bisa membuatmu terkesan menguasai pembicaraan.',
            'desc_en': 'Strong social drive without empathy balance can make you seem to dominate conversations.',
            'mit_id': 'Latih active listening: diam sejenak sebelum merespons dan ajukan pertanyaan lebih banyak.',
            'mit_en': 'Practice active listening: pause before responding and ask more questions.',
        },
        {
            'cond': n >= 65,
            'title_id': 'Sensitivitas Emosi Tinggi', 'title_en': 'High Emotional Sensitivity',
            'desc_id': 'Stres dan kritik bisa mempengaruhi produktivitasmu lebih dari rata-rata orang.',
            'desc_en': 'Stress and criticism can affect your productivity more than average.',
            'mit_id': 'Bangun rutinitas mindfulness 10 menit/hari dan identifikasi trigger stres utamamu.',
            'mit_en': 'Build a 10-min daily mindfulness routine and identify your main stress triggers.',
        },
        {
            'cond': c >= 80 and o < 45,
            'title_id': 'Rigiditas dalam Perubahan', 'title_en': 'Rigidity in Change',
            'desc_id': 'Disiplinmu yang sangat tinggi bisa berubah menjadi kekakuan saat situasi mengharuskan adaptasi cepat.',
            'desc_en': 'Your very high discipline can become rigidity when situations require rapid adaptation.',
            'mit_id': 'Sisipkan satu "eksperimen kecil" setiap minggu — satu cara baru dalam rutinmu.',
            'mit_en': 'Insert one "small experiment" per week — one new approach in your routine.',
        },
        {
            'cond': a >= 75 and e < 45,
            'title_id': 'Terlalu Mengalah', 'title_en': 'Over-Accommodating',
            'desc_id': 'Kombinasi keramahan tinggi dan ekstraversi rendah bisa membuatmu sulit menolak permintaan orang lain.',
            'desc_en': 'High agreeableness combined with low extraversion can make it hard to decline others\' requests.',
            'mit_id': 'Latih asertivitas: "Saya perlu waktu untuk memikirkannya" adalah jawaban yang valid.',
            'mit_en': 'Practice assertiveness: "I need time to think about it" is a valid answer.',
        },
        {
            'cond': iq >= 120 and e < 50,
            'title_id': 'Kesenjangan Komunikasi', 'title_en': 'Communication Gap',
            'desc_id': 'Kecerdasan tinggi + introvert bisa membuatmu sulit mengkomunikasikan ide kompleks kepada audiens umum.',
            'desc_en': 'High intelligence + introversion can make it hard to communicate complex ideas to general audiences.',
            'mit_id': 'Latih public speaking atau menulis artikel populer untuk menjembatani gap ini.',
            'mit_en': 'Practice public speaking or writing popular articles to bridge this gap.',
        },
        {
            'cond': o < 40 and c < 50,
            'title_id': 'Zona Nyaman yang Membatasi', 'title_en': 'Limiting Comfort Zone',
            'desc_id': 'Kombinasi keterbukaan dan disiplin rendah bisa memperlambat pertumbuhan pribadi.',
            'desc_en': 'Low openness and low discipline combined can slow personal growth.',
            'mit_id': 'Buat satu komitmen kecil yang menantang per bulan — sesuatu di luar zona nyamanmu.',
            'mit_en': 'Make one small challenging commitment per month — something outside your comfort zone.',
        },
        {
            'cond': n >= 60 and c < 55,
            'title_id': 'Spiral Prokrastinasi', 'title_en': 'Procrastination Spiral',
            'desc_id': 'Stres yang belum terkelola + disiplin rendah sering memicu siklus prokrastinasi yang sulit diputus.',
            'desc_en': 'Unmanaged stress + low discipline often triggers a procrastination cycle that\'s hard to break.',
            'mit_id': 'Gunakan teknik "5 menit": mulai tugas hanya 5 menit, tidak lebih — momentum akan mengikuti.',
            'mit_en': 'Use the "5-minute technique": start a task for just 5 minutes — momentum will follow.',
        },
    ]

    results = []
    for r in RULES:
        if r['cond']:
            results.append({
                'title':      r[f'title_{l}'],
                'desc':       r[f'desc_{l}'],
                'mitigation': r[f'mit_{l}'],
            })
        if len(results) == 4:
            break
    return results


# ══════════════════════════════════════════════════════════════
# 8. ROADMAP 3 BULAN
# ══════════════════════════════════════════════════════════════
def compute_roadmap(iq: int, bf_scores: dict, cognitive: dict, careers: list, lang: str = 'id') -> list[dict]:
    o,c,e,a,n = (bf_scores.get(t,50) for t in 'OCEAN')
    top_career = careers[0]['name'] if careers else ('Karir Impianmu' if lang=='id' else 'Your Dream Career')
    weak_cog   = min(cognitive.items(), key=lambda x: x[1]['score_pct'])[0] if cognitive else 'fluid'
    cog_names  = {'fluid':'Penalaran Logis','crystallized':'Kecerdasan Verbal',
                  'abstract':'Penalaran Abstrak','quantitative':'Numerik','spatial':'Spasial'}
    cog_names_en = {'fluid':'Logical Reasoning','crystallized':'Verbal Intelligence',
                    'abstract':'Abstract Reasoning','quantitative':'Numerical','spatial':'Spatial'}
    weak_name  = (cog_names if lang=='id' else cog_names_en).get(weak_cog, weak_cog)

    if lang == 'id':
        m1_focus  = 'Fondasi & Kesadaran Diri'
        m1_actions = [
            f'Pelajari lebih dalam bidang {top_career} — ikuti 1 kursus online',
            'Mulai jurnal refleksi harian 10 menit setiap pagi',
            f'Latihan {"regulasi emosi" if n >= 60 else "manajemen waktu"} selama 21 hari berturut-turut',
            'Identifikasi 3 kekuatan utamamu dan 1 area prioritas pengembangan',
        ]
        m2_focus  = 'Pengembangan Keterampilan'
        m2_actions = [
            f'Tingkatkan kemampuan {weak_name} melalui latihan rutin 20 menit/hari',
            f'{"Bergabung komunitas atau networking" if e >= 55 else "Bangun portofolio atau proyek personal"}',
            'Baca 2 buku yang relevan dengan bidang karirmu',
            f'{"Latih public speaking" if e < 55 else "Dalami skill teknikal yang relevan"}',
        ]
        m3_focus  = 'Aksi & Eksposur'
        m3_actions = [
            f'Lamar atau jadikan {top_career} sebagai target konkret dengan timeline',
            'Temui 3 orang yang sudah sukses di bidang yang kamu tuju',
            'Presentasikan atau publikasikan satu hasil kerjamu',
            'Evaluasi kemajuan dan susun rencana 6 bulan berikutnya',
        ]
    else:
        m1_focus  = 'Foundation & Self-Awareness'
        m1_actions = [
            f'Explore {top_career} in depth — take 1 online course',
            'Start a 10-minute daily reflection journal each morning',
            f'Practice {"emotional regulation" if n >= 60 else "time management"} for 21 consecutive days',
            'Identify your 3 core strengths and 1 priority development area',
        ]
        m2_focus  = 'Skill Development'
        m2_actions = [
            f'Strengthen {weak_name} through 20-minute daily practice',
            f'{"Join a community or network" if e >= 55 else "Build a portfolio or personal project"}',
            'Read 2 books relevant to your career field',
            f'{"Practice public speaking" if e < 55 else "Deepen relevant technical skills"}',
        ]
        m3_focus  = 'Action & Exposure'
        m3_actions = [
            f'Apply to or set {top_career} as a concrete target with a timeline',
            'Meet 3 people already succeeding in your target field',
            'Present or publish one piece of your work',
            'Evaluate progress and draft your next 6-month plan',
        ]

    return [
        {'month': 1, 'focus': m1_focus, 'actions': m1_actions},
        {'month': 2, 'focus': m2_focus, 'actions': m2_actions},
        {'month': 3, 'focus': m3_focus, 'actions': m3_actions},
    ]


# ══════════════════════════════════════════════════════════════
# HELPER: FULL ANALYSIS
# ══════════════════════════════════════════════════════════════
def run_full_analysis(bf_answers, bf_session, iq_answers=None, iq_session=None, lang='id') -> dict:
    """
    Jalankan semua layer inference dan return dict lengkap.
    iq_answers / iq_session boleh None jika hanya BF.
    """
    bf_result = score_bigfive(bf_answers, bf_session)
    bf_scores = {t: bf_result[t]['normalized'] for t in 'OCEAN'}
    bf_pcts   = {t: bf_result[t]['percentile']  for t in 'OCEAN'}

    if iq_answers and iq_session:
        iq_result = score_iq(iq_answers, iq_session)
        cognitive = build_cognitive_profile(iq_answers, iq_session)
    else:
        iq_result = {'iq': 100, 'label': 'Average', 'color': '#8b5cf6',
                     'percentile': 50, 'correct': 0, 'total': 0,
                     'weighted_pct': 50, 'n_population': 2051}
        cognitive = {d: {'score_pct': 50, 'level': 'Average', 'level_id': 'Rata-rata', 'rank': i}
                     for i, d in enumerate(['fluid','crystallized','abstract','quantitative','spatial'], 1)}

    iq = iq_result['iq']

    archetype    = compute_archetype(bf_scores, lang)
    combined     = compute_combined(iq, bf_scores, lang)
    careers      = compute_careers(bf_scores, iq, lang, top_n=5)
    style_name, style_detail = compute_learning_style(bf_scores, cognitive, lang)
    blind_spots  = compute_blind_spots(iq, bf_scores, lang)
    roadmap      = compute_roadmap(iq, bf_scores, cognitive, careers, lang)

    return {
        **iq_result,
        'cognitive':            cognitive,
        'archetype':            archetype,
        'combined':             combined,
        'careers':              careers,
        'learning_style_name':  style_name,
        'learning_style_detail':style_detail,
        'blind_spots':          blind_spots,
        'roadmap':              roadmap,
        'bf_scores':            bf_scores,
        'bf_pcts':              bf_pcts,
        'bf_result':            bf_result,
        'lang':                 lang,
        'n_bf_pop':             bf_result.get('_n_population', 874434),
    }