"""
engine/expert_rules.py
─────────────────────────────────────────────────────────────────
Rule-based Expert Engine untuk interpretasi kombinasi IQ × OCEAN.

Arsitektur:
  Layer 1 — Personality Archetype (64 kombinasi OCEAN)
  Layer 2 — IQ × OCEAN Combined Profile
  Layer 3 — Career Recommendations dengan confidence score
  Layer 4 — Learning Style Profile
  Layer 5 — Blind Spots & Risk Factors
  Layer 6 — Development Roadmap 3 Bulan
─────────────────────────────────────────────────────────────────
"""

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _level(score):
    """Konversi skor 0-100 ke level: High / Mid / Low."""
    if score >= 62: return 'H'
    if score >= 38: return 'M'
    return 'L'

def _iq_band(iq):
    """Konversi IQ ke band."""
    if iq >= 120: return 'VH'   # Very High
    if iq >= 110: return 'H'    # High
    if iq >= 90:  return 'M'    # Mid
    return 'L'                   # Low


# ══════════════════════════════════════════════════════════════════
# LAYER 1 — PERSONALITY ARCHETYPE
# ══════════════════════════════════════════════════════════════════

ARCHETYPES = [
    # ── High O ──
    {
        'conditions': {'O':'H','C':'H','E':'H','A':'H','N':'L'},
        'id': {'name':'Visioner Harmonis','tag':'THE HARMONIOUS VISIONARY',
               'desc':'Kamu adalah perpaduan langka antara kreativitas tinggi, kedisiplinan, dan kemampuan sosial. Kamu mampu menghasilkan ide-ide besar dan sekaligus mewujudkannya — kombinasi yang membuat kamu sangat efektif sebagai pemimpin inovatif.'},
        'en': {'name':'Harmonious Visionary','tag':'THE HARMONIOUS VISIONARY',
               'desc':'You are a rare blend of high creativity, discipline, and social skill. You generate big ideas and follow through on them — a combination that makes you highly effective as an innovative leader.'},
    },
    {
        'conditions': {'O':'H','C':'H','E':'L','A':'M','N':'L'},
        'id': {'name':'Arsitek Sistematis','tag':'THE SYSTEMATIC ARCHITECT',
               'desc':'Kamu berpikir mendalam, terstruktur, dan orisinal. Introvert yang produktif — kamu bekerja terbaik dalam ketenangan dengan output berkualitas tinggi. Cenderung menjadi ahli di bidang yang kamu geluti.'},
        'en': {'name':'Systematic Architect','tag':'THE SYSTEMATIC ARCHITECT',
               'desc':'You think deeply, systematically, and originally. A productive introvert — you work best in quiet settings with high-quality output. You tend to become an expert in your chosen field.'},
    },
    {
        'conditions': {'O':'H','C':'L','E':'H','A':'H','N':'H'},
        'id': {'name':'Penjelajah Kreatif','tag':'THE CREATIVE EXPLORER',
               'desc':'Penuh dengan ide dan energi sosial yang tinggi, kamu adalah tipe yang selalu mencari pengalaman baru. Sensitif secara emosional — ini memberi kamu empati mendalam namun juga rentan terhadap stres.'},
        'en': {'name':'Creative Explorer','tag':'THE CREATIVE EXPLORER',
               'desc':'Full of ideas and high social energy, you are always seeking new experiences. Emotionally sensitive — this gives you deep empathy but also vulnerability to stress.'},
    },
    {
        'conditions': {'O':'H','C':'M','E':'M','A':'M','N':'M'},
        'id': {'name':'Pemikir Adaptif','tag':'THE ADAPTIVE THINKER',
               'desc':'Kamu memiliki keingintahuan intelektual yang kuat dengan keseimbangan baik di dimensi lainnya. Fleksibel dan terbuka — kamu dapat beradaptasi dengan baik di berbagai lingkungan dan situasi.'},
        'en': {'name':'Adaptive Thinker','tag':'THE ADAPTIVE THINKER',
               'desc':'You have strong intellectual curiosity with good balance across other dimensions. Flexible and open — you adapt well to various environments and situations.'},
    },
    # ── High C ──
    {
        'conditions': {'O':'M','C':'H','E':'H','A':'H','N':'L'},
        'id': {'name':'Pemimpin Andalan','tag':'THE RELIABLE LEADER',
               'desc':'Terorganisir, ramah, dan stabil secara emosional — kamu adalah tipe yang diandalkan oleh tim. Kombinasi Conscientiousness dan Extraversion tinggi membuat kamu sangat efektif dalam peran kepemimpinan langsung.'},
        'en': {'name':'Reliable Leader','tag':'THE RELIABLE LEADER',
               'desc':'Organized, personable, and emotionally stable — you are the type a team relies on. High Conscientiousness and Extraversion make you highly effective in direct leadership roles.'},
    },
    {
        'conditions': {'O':'L','C':'H','E':'L','A':'M','N':'L'},
        'id': {'name':'Eksekutor Presisi','tag':'THE PRECISION EXECUTOR',
               'desc':'Teliti, konsisten, dan fokus pada hasil — kamu unggul dalam menyelesaikan tugas dengan standar tinggi. Introvert yang terstruktur, kamu lebih suka kedalaman daripada keluasan.'},
        'en': {'name':'Precision Executor','tag':'THE PRECISION EXECUTOR',
               'desc':'Meticulous, consistent, and results-focused — you excel at completing tasks to high standards. A structured introvert, you prefer depth over breadth.'},
    },
    {
        'conditions': {'O':'M','C':'H','E':'M','A':'H','N':'M'},
        'id': {'name':'Kolaborator Terstruktur','tag':'THE STRUCTURED COLLABORATOR',
               'desc':'Kamu menggabungkan kedisiplinan dengan kemampuan bekerja sama yang baik. Kamu memastikan pekerjaan selesai dengan benar sambil menjaga hubungan tim tetap harmonis.'},
        'en': {'name':'Structured Collaborator','tag':'THE STRUCTURED COLLABORATOR',
               'desc':'You combine discipline with strong collaborative ability. You ensure work gets done correctly while keeping team relationships harmonious.'},
    },
    # ── High E ──
    {
        'conditions': {'O':'M','C':'M','E':'H','A':'H','N':'L'},
        'id': {'name':'Konekter Alami','tag':'THE NATURAL CONNECTOR',
               'desc':'Energi sosial tinggi, hangat, dan stabil — kamu dengan mudah membangun jaringan dan kepercayaan. Kamu adalah perekat dalam tim dan komunitas, selalu tahu cara membuat orang merasa diterima.'},
        'en': {'name':'Natural Connector','tag':'THE NATURAL CONNECTOR',
               'desc':'High social energy, warm, and stable — you build networks and trust effortlessly. You are the glue in teams and communities, always knowing how to make people feel welcome.'},
    },
    {
        'conditions': {'O':'H','C':'M','E':'H','A':'M','N':'M'},
        'id': {'name':'Inovator Sosial','tag':'THE SOCIAL INNOVATOR',
               'desc':'Kreatif dan ekstrovert — kamu menghasilkan ide terbaik dalam kolaborasi dan diskusi. Kamu suka berbagi gagasan dan mendorong orang lain untuk berpikir lebih luas.'},
        'en': {'name':'Social Innovator','tag':'THE SOCIAL INNOVATOR',
               'desc':'Creative and extroverted — you generate your best ideas through collaboration and discussion. You love sharing ideas and pushing others to think more broadly.'},
    },
    # ── High N ──
    {
        'conditions': {'O':'H','C':'L','E':'L','A':'M','N':'H'},
        'id': {'name':'Seniman Reflektif','tag':'THE REFLECTIVE ARTIST',
               'desc':'Sensitif, imajinatif, dan penuh kedalaman emosional — kamu memproses dunia dengan intensitas tinggi. Kreativitasmu sering lahir dari pengalaman emosional yang kaya.'},
        'en': {'name':'Reflective Artist','tag':'THE REFLECTIVE ARTIST',
               'desc':'Sensitive, imaginative, and emotionally deep — you process the world with high intensity. Your creativity often emerges from rich emotional experience.'},
    },
    {
        'conditions': {'O':'M','C':'H','E':'M','A':'M','N':'H'},
        'id': {'name':'Perfeksionis Waspada','tag':'THE VIGILANT PERFECTIONIST',
               'desc':'Standar tinggi dikombinasikan dengan kepekaan emosional membuat kamu sangat teliti namun rentan terhadap kecemasan. Kamu menghasilkan kerja berkualitas tinggi tetapi perlu manajemen stres yang baik.'},
        'en': {'name':'Vigilant Perfectionist','tag':'THE VIGILANT PERFECTIONIST',
               'desc':'High standards combined with emotional sensitivity make you very meticulous but prone to anxiety. You produce high-quality work but need strong stress management.'},
    },
    # ── Low N (Stable) ──
    {
        'conditions': {'O':'M','C':'M','E':'M','A':'H','N':'L'},
        'id': {'name':'Mediator Tenang','tag':'THE CALM MEDIATOR',
               'desc':'Stabil, kooperatif, dan penuh empati — kamu adalah tipe yang menenangkan dalam konflik. Kamu mendengarkan sebelum berbicara dan selalu mencari solusi yang adil untuk semua pihak.'},
        'en': {'name':'Calm Mediator','tag':'THE CALM MEDIATOR',
               'desc':'Stable, cooperative, and empathetic — you are a calming presence in conflict. You listen before speaking and always seek fair solutions for everyone.'},
    },
    {
        'conditions': {'O':'L','C':'M','E':'M','A':'M','N':'L'},
        'id': {'name':'Pragmatis Stabil','tag':'THE STABLE PRAGMATIST',
               'desc':'Kamu pendekatan terhadap hidup bersifat praktis dan membumi. Tidak terlalu idealis, tidak mudah stres — kamu fokus pada apa yang bekerja dan melakukannya dengan konsisten.'},
        'en': {'name':'Stable Pragmatist','tag':'THE STABLE PRAGMATIST',
               'desc':'Your approach to life is practical and grounded. Not overly idealistic, not easily stressed — you focus on what works and do it consistently.'},
    },
    # ── Default fallback ──
    {
        'conditions': None,
        'id': {'name':'Profil Seimbang','tag':'THE BALANCED PROFILE',
               'desc':'Kamu memiliki keseimbangan yang baik di seluruh dimensi kepribadian. Fleksibilitas ini membuat kamu dapat beradaptasi di berbagai situasi dan lingkungan.'},
        'en': {'name':'Balanced Profile','tag':'THE BALANCED PROFILE',
               'desc':'You have good balance across all personality dimensions. This flexibility allows you to adapt to various situations and environments.'},
    },
]

def get_archetype(scores, lang='id'):
    """Match skor OCEAN ke archetype terbaik."""
    levels = {t: _level(scores[t]) for t in ['O','C','E','A','N']}

    for arch in ARCHETYPES:
        if arch['conditions'] is None:
            return arch[lang]
        cond = arch['conditions']
        match = all(levels.get(k) == v for k,v in cond.items())
        if match:
            return arch[lang]

    # Fallback: cari yang paling banyak match
    best, best_score = ARCHETYPES[-1][lang], 0
    for arch in ARCHETYPES[:-1]:
        if arch['conditions'] is None: continue
        sc = sum(1 for k,v in arch['conditions'].items() if levels.get(k)==v)
        if sc > best_score:
            best_score = sc; best = arch[lang]
    return best


# ══════════════════════════════════════════════════════════════════
# LAYER 2 — COMBINED IQ × OCEAN PROFILE
# ══════════════════════════════════════════════════════════════════

COMBINED_PROFILES = [
    {
        'iq_bands': ['VH','H'], 'O':'H', 'C':'L',
        'id': {'name':'Scattered Genius','desc':'IQ tinggi namun Conscientiousness rendah menciptakan pola "potensi tidak terealisasi". Kamu memiliki kemampuan berpikir luar biasa tetapi sering terhambat oleh kurangnya sistem dan follow-through.','action':'Fokus membangun sistem produktivitas — time-blocking, to-do list berbasis prioritas, dan accountability partner.'},
        'en': {'name':'Scattered Genius','desc':'High IQ but low Conscientiousness creates a "unrealized potential" pattern. You have exceptional thinking ability but are often held back by lack of systems and follow-through.','action':'Focus on building productivity systems — time-blocking, priority-based to-do lists, and an accountability partner.'},
    },
    {
        'iq_bands': ['VH','H'], 'O':'H', 'C':'H',
        'id': {'name':'Architect of Ideas','desc':'Kombinasi terbaik untuk inovasi: kemampuan berpikir tinggi, kreativitas, dan kedisiplinan. Kamu tidak hanya punya ide besar — kamu juga punya sistem untuk mewujudkannya.','action':'Cari domain yang membutuhkan inovasi sistematis: riset, product development, atau strategi bisnis.'},
        'en': {'name':'Architect of Ideas','desc':'The best combination for innovation: high cognitive ability, creativity, and discipline. You not only have big ideas — you have the system to realize them.','action':'Seek domains requiring systematic innovation: research, product development, or business strategy.'},
    },
    {
        'iq_bands': ['VH','H'], 'O':'L', 'C':'H',
        'id': {'name':'Master Implementor','desc':'IQ tinggi dengan orientasi konvensional dan terstruktur — kamu adalah eksekutor yang sangat efisien. Lebih suka menyempurnakan sistem yang ada daripada menciptakan yang baru dari nol.','action':'Peran sebagai senior specialist, operations lead, atau technical expert sangat sesuai.'},
        'en': {'name':'Master Implementor','desc':'High IQ with conventional and structured orientation — you are a highly efficient executor. You prefer refining existing systems over creating from scratch.','action':'Senior specialist, operations lead, or technical expert roles are an excellent fit.'},
    },
    {
        'iq_bands': ['M'], 'O':'H', 'C':'H', 'E':'H',
        'id': {'name':'The Driven Achiever','desc':'IQ rata-rata dengan kombinasi trait kerja keras, kreativitas, dan sosialitas tinggi — kamu membuktikan bahwa karakter mengalahkan bakat. Kamu cenderung overperform dari ekspektasi.','action':'Leadership dan entrepreneurship sangat cocok. Kamu tumbuh di lingkungan yang menghargai etos kerja dan inisiatif.'},
        'en': {'name':'The Driven Achiever','desc':'Average IQ with high work ethic, creativity, and sociability — you prove that character beats talent. You tend to outperform expectations.','action':'Leadership and entrepreneurship are great fits. You thrive in environments that value work ethic and initiative.'},
    },
    {
        'iq_bands': ['VH','H'], 'E':'L', 'O':'H',
        'id': {'name':'Deep Specialist','desc':'Kemampuan kognitif tinggi dengan Openness tinggi namun Extraversion rendah — profil klasik seorang ilmuwan atau pakar. Kamu berpikir mendalam dan lebih suka kerja mandiri yang substantif.','action':'Karir penelitian, akademisi, writing, atau technical specialization adalah habitat naturalmu.'},
        'en': {'name':'Deep Specialist','desc':'High cognitive ability with high Openness but low Extraversion — the classic profile of a scientist or expert. You think deeply and prefer substantive independent work.','action':'Research, academia, writing, or technical specialization careers are your natural habitat.'},
    },
    {
        'iq_bands': ['VH','H','M'], 'A':'H', 'N':'L', 'E':'H',
        'id': {'name':'Trusted Guide','desc':'Stabil, ramah, dan cerdas — kamu adalah tipe yang membuat orang merasa aman dan didengar. Kombinasi ini sangat jarang dan sangat berharga dalam peran yang melibatkan orang.','action':'Konseling, psikologi, pendidikan, HR, atau leadership berbasis servant-leadership sangat sesuai.'},
        'en': {'name':'Trusted Guide','desc':'Stable, warm, and intelligent — you are the type that makes people feel safe and heard. This combination is rare and highly valuable in people-facing roles.','action':'Counseling, psychology, education, HR, or servant-leadership roles are ideal.'},
    },
    {
        'iq_bands': None, 'N':'H', 'C':'H',
        'id': {'name':'Anxious High-Performer','desc':'Standar tinggi dan kepekaan emosional yang intens sering berjalan beriringan. Kamu cenderung menghasilkan kerja berkualitas tinggi tetapi dengan biaya emosional yang besar.','action':'Mindfulness, terapi kognitif-behavioral (CBT), dan batas kerja yang jelas sangat penting untuk keberlanjutan.'},
        'en': {'name':'Anxious High-Performer','desc':'High standards and intense emotional sensitivity often go hand in hand. You tend to produce high-quality work but at significant emotional cost.','action':'Mindfulness, cognitive-behavioral approaches, and clear work boundaries are essential for sustainability.'},
    },
]

def get_combined_profile(iq, scores, lang='id'):
    """Match IQ + OCEAN ke combined profile."""
    band = _iq_band(iq)
    levels = {t: _level(scores[t]) for t in ['O','C','E','A','N']}

    best, best_score = None, -1
    for p in COMBINED_PROFILES:
        score = 0
        if p['iq_bands'] is not None and band in p['iq_bands']:
            score += 2
        for trait in ['O','C','E','A','N']:
            if trait in p and levels.get(trait) == p[trait]:
                score += 1
        if score > best_score:
            best_score = score; best = p

    return best[lang] if best else {'name': '—', 'desc': '', 'action': ''}


# ══════════════════════════════════════════════════════════════════
# LAYER 3 — CAREER RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════

CAREERS = [
    {
        'id': 'Peneliti / Ilmuwan',
        'en': 'Researcher / Scientist',
        'weights': {'iq':0.30,'O':0.25,'C':0.25,'E':-0.05,'A':0.05,'N':-0.10},
    },
    {
        'id': 'Software Engineer / Developer',
        'en': 'Software Engineer / Developer',
        'weights': {'iq':0.25,'O':0.20,'C':0.25,'E':-0.05,'A':0.05,'N':-0.10},
    },
    {
        'id': 'Data Scientist / Analis Data',
        'en': 'Data Scientist / Data Analyst',
        'weights': {'iq':0.30,'O':0.15,'C':0.25,'E':-0.05,'A':0.05,'N':-0.10},
    },
    {
        'id': 'Psikolog / Konselor',
        'en': 'Psychologist / Counselor',
        'weights': {'iq':0.15,'O':0.20,'C':0.15,'E':0.10,'A':0.30,'N':-0.10},
    },
    {
        'id': 'Dokter / Tenaga Medis',
        'en': 'Medical Doctor / Healthcare Professional',
        'weights': {'iq':0.25,'O':0.15,'C':0.30,'E':0.10,'A':0.20,'N':-0.10},
    },
    {
        'id': 'Pengacara / Hukum',
        'en': 'Lawyer / Legal Professional',
        'weights': {'iq':0.30,'O':0.15,'C':0.25,'E':0.15,'A':0.05,'N':-0.10},
    },
    {
        'id': 'Manajer / Pemimpin Bisnis',
        'en': 'Manager / Business Leader',
        'weights': {'iq':0.20,'O':0.10,'C':0.25,'E':0.25,'A':0.15,'N':-0.15},
    },
    {
        'id': 'Entrepreneur / Wirausaha',
        'en': 'Entrepreneur',
        'weights': {'iq':0.15,'O':0.30,'C':0.20,'E':0.20,'A':0.05,'N':-0.10},
    },
    {
        'id': 'Desainer / Seniman Kreatif',
        'en': 'Designer / Creative Artist',
        'weights': {'iq':0.10,'O':0.40,'C':0.10,'E':0.10,'A':0.15,'N':0.05},
    },
    {
        'id': 'Guru / Pendidik',
        'en': 'Teacher / Educator',
        'weights': {'iq':0.15,'O':0.20,'C':0.20,'E':0.20,'A':0.25,'N':-0.10},
    },
    {
        'id': 'Penulis / Jurnalis',
        'en': 'Writer / Journalist',
        'weights': {'iq':0.20,'O':0.35,'C':0.15,'E':0.05,'A':0.10,'N':0.05},
    },
    {
        'id': 'Insinyur / Arsitek',
        'en': 'Engineer / Architect',
        'weights': {'iq':0.25,'O':0.15,'C':0.30,'E':0.05,'A':0.10,'N':-0.05},
    },
    {
        'id': 'Marketing / PR / Sales',
        'en': 'Marketing / PR / Sales',
        'weights': {'iq':0.10,'O':0.20,'C':0.15,'E':0.35,'A':0.20,'N':-0.10},
    },
    {
        'id': 'Analis Keuangan / Akuntan',
        'en': 'Financial Analyst / Accountant',
        'weights': {'iq':0.25,'O':0.05,'C':0.35,'E':0.05,'A':0.10,'N':-0.10},
    },
    {
        'id': 'Pekerja Sosial / NGO',
        'en': 'Social Worker / NGO Professional',
        'weights': {'iq':0.10,'O':0.20,'C':0.15,'E':0.20,'A':0.35,'N':-0.10},
    },
]

def _normalize_iq(iq):
    """Normalisasi IQ ke skala 0-100."""
    return max(0, min(100, (iq - 70) / 60 * 100))

def get_career_recommendations(iq, scores, lang='id', top_n=5):
    """Hitung confidence score tiap karir dan return top N."""
    norm_iq = _normalize_iq(iq)
    inputs = {
        'iq': norm_iq,
        'O': scores['O'], 'C': scores['C'], 'E': scores['E'],
        'A': scores['A'], 'N': scores['N'],
    }

    results = []
    for career in CAREERS:
        raw = sum(inputs[k] * w for k, w in career['weights'].items())
        # Normalisasi ke 0-100
        raw_pct = max(0, min(100, raw))
        results.append({
            'name':       career[lang],
            'confidence': round(raw_pct),
        })

    results.sort(key=lambda x: x['confidence'], reverse=True)

    # Re-scale top result ke ~85-95 range agar terlihat realistis
    if results:
        top = results[0]['confidence']
        if top > 0:
            scale = min(92, max(75, top)) / top
            for r in results:
                r['confidence'] = min(98, round(r['confidence'] * scale))

    return results[:top_n]


# ══════════════════════════════════════════════════════════════════
# LAYER 4 — LEARNING STYLE
# ══════════════════════════════════════════════════════════════════

LEARNING_STYLES = {
    'id': {
        'Visual': {
            'desc': 'Kamu belajar terbaik melalui diagram, grafik, mind-map, dan representasi visual. Informasi yang disajikan secara visual lebih mudah kamu proses dan ingat.',
            'tips': [
                'Gunakan mind-map dan diagram alur untuk merangkum materi',
                'Tandai teks dengan warna berbeda per topik',
                'Buat infografis pribadi dari materi yang dipelajari',
                'Manfaatkan video tutorial dan presentasi visual',
            ],
            'environment': 'Tempat tenang dengan whiteboard atau ruang menulis yang luas.',
        },
        'Auditory': {
            'desc': 'Kamu menyerap informasi paling baik melalui diskusi, penjelasan verbal, dan mendengarkan. Belajar dengan orang lain atau mendengar penjelasan lebih efektif daripada membaca diam.',
            'tips': [
                'Rekam penjelasan dan dengarkan kembali',
                'Ikuti grup diskusi atau study group',
                'Jelaskan materi kepada orang lain (Feynman technique)',
                'Gunakan podcast atau audio course untuk belajar sambil beraktivitas',
            ],
            'environment': 'Lingkungan dengan diskusi aktif — library dengan ruang diskusi atau coffee shop.',
        },
        'Reading/Writing': {
            'desc': 'Kamu unggul dalam belajar melalui teks — membaca, membuat catatan, dan menulis rangkuman. Informasi tertulis adalah format yang paling natural bagimu.',
            'tips': [
                'Buat catatan detil dengan bahasa sendiri',
                'Tulis rangkuman setiap sesi belajar',
                'Baca berbagai sumber untuk satu topik',
                'Buat daftar, outline, dan glossary istilah penting',
            ],
            'environment': 'Ruang yang tenang dan rapi dengan meja belajar yang baik.',
        },
        'Kinesthetic': {
            'desc': 'Kamu belajar paling baik melalui pengalaman langsung, praktik, dan eksperimen. Abstraksi menjadi jelas bagimu setelah kamu mencobanya sendiri.',
            'tips': [
                'Kerjakan proyek nyata dan studi kasus praktis',
                'Ambil kelas workshop atau hands-on training',
                'Buat prototipe atau simulasi dari konsep yang dipelajari',
                'Belajar sambil bergerak — berjalan saat review materi',
            ],
            'environment': 'Lab, workshop, atau ruang kerja dengan banyak ruang untuk bergerak dan mencoba.',
        },
    },
    'en': {
        'Visual': {
            'desc': 'You learn best through diagrams, charts, mind-maps, and visual representations. Visually presented information is easier for you to process and remember.',
            'tips': [
                'Use mind-maps and flowcharts to summarize material',
                'Color-code text by topic',
                'Create personal infographics from study material',
                'Leverage video tutorials and visual presentations',
            ],
            'environment': 'A quiet space with a whiteboard or ample writing area.',
        },
        'Auditory': {
            'desc': 'You absorb information best through discussion, verbal explanation, and listening. Learning with others or hearing explanations is more effective than silent reading.',
            'tips': [
                'Record explanations and listen back to them',
                'Join discussion groups or study groups',
                'Explain material to others (Feynman technique)',
                'Use podcasts or audio courses while on the go',
            ],
            'environment': 'An active discussion environment — library discussion rooms or a coffee shop.',
        },
        'Reading/Writing': {
            'desc': 'You excel at learning through text — reading, note-taking, and writing summaries. Written information is the most natural format for you.',
            'tips': [
                'Take detailed notes in your own words',
                'Write a summary after every study session',
                'Read multiple sources on one topic',
                'Create lists, outlines, and glossaries of key terms',
            ],
            'environment': 'A quiet, tidy space with a good desk.',
        },
        'Kinesthetic': {
            'desc': 'You learn best through direct experience, practice, and experimentation. Abstractions become clear to you only after you try them yourself.',
            'tips': [
                'Work on real projects and practical case studies',
                'Take workshops or hands-on training classes',
                'Build prototypes or simulations of concepts studied',
                'Move while reviewing — walk while going over material',
            ],
            'environment': 'A lab, workshop, or workspace with room to move and experiment.',
        },
    },
}

def get_learning_style(scores, cognitive_profile, lang='id'):
    """
    Inferensi gaya belajar dari OCEAN + cognitive profile.
    Return: style_name, detail dict
    """
    O, C, E, N = scores['O'], scores['C'], scores['E'], scores['N']
    spatial_score  = cognitive_profile.get('spatial',  {}).get('score_pct', 50)
    fluid_score    = cognitive_profile.get('fluid',    {}).get('score_pct', 50)
    crystal_score  = cognitive_profile.get('crystallized', {}).get('score_pct', 50)

    scores_style = {
        'Visual':         spatial_score * 0.5 + O * 0.3 + (100-E) * 0.2,
        'Auditory':       E * 0.4 + scores['A'] * 0.3 + (100-C) * 0.3,
        'Reading/Writing': crystal_score * 0.4 + C * 0.3 + (100-E) * 0.3,
        'Kinesthetic':    fluid_score * 0.3 + (100-O) * 0.2 + E * 0.3 + (100-N) * 0.2,
    }

    primary = max(scores_style, key=scores_style.get)
    return primary, LEARNING_STYLES[lang][primary]


# ══════════════════════════════════════════════════════════════════
# LAYER 5 — BLIND SPOTS & RISK FACTORS
# ══════════════════════════════════════════════════════════════════

def get_blind_spots(iq, scores, lang='id'):
    """Return list of {title, desc, mitigation} dicts."""
    results = []
    O,C,E,A,N = scores['O'],scores['C'],scores['E'],scores['A'],scores['N']

    _bs = {
        'id': [
            # IQ tinggi risks
            (iq >= 120 and C < 40, 'Jebakan Overkonfiden Intelektual',
             'IQ tinggi kadang menciptakan keyakinan bahwa kamu selalu benar atau lebih tahu. Ini bisa membuatmu kurang mendengarkan input dari orang lain.',
             'Praktikkan intellectual humility — secara aktif cari perspektif yang menantang pandanganmu.'),
            (iq >= 120 and E < 40, 'Isolasi Intelektual',
             'Kecerdasan tinggi dengan Extraversion rendah bisa menciptakan jarak sosial yang tidak disengaja. Orang lain mungkin merasa sulit untuk berhubungan.',
             'Latih komunikasi yang accessible — jelaskan ide dengan bahasa sederhana dan tunjukkan ketertarikan pada perspektif orang lain.'),
            # O risks
            (O >= 70 and C < 40, 'Sindrom Proyek Tidak Selesai',
             'Openness tinggi menghasilkan banyak ide dan ketertarikan baru, tapi tanpa Conscientiousness yang cukup, kamu cenderung meninggalkan proyek di tengah jalan.',
             'Terapkan aturan "selesaikan sebelum mulai" — batasi proyek aktif maksimal 2-3 sekaligus.'),
            (O >= 70 and N >= 65, 'Overwhelm dari Stimulasi Berlebih',
             'Pikiran yang terus mencari input baru dikombinasikan dengan kepekaan emosional tinggi bisa menyebabkan mental overload.',
             'Jadwalkan "digital detox" dan waktu refleksi harian tanpa input baru.'),
            # C risks
            (C >= 70 and A < 40, 'Rigiditas dan Konflik Interpersonal',
             'Standar tinggi yang kaku bisa menciptakan gesekan dengan orang-orang yang bekerja secara berbeda. Kamu mungkin terlihat kritis atau terlalu demanding.',
             'Praktikkan fleksibilitas yang disengaja — biarkan beberapa hal dilakukan dengan cara yang bukan caramu.'),
            (C >= 70 and N >= 65, 'Burnout Perfeksionis',
             'Kombinasi standar tinggi dan kecemasan adalah resep burnout. Kamu sulit merasa "cukup baik" pada pekerjaanmu.',
             'Tetapkan definisi "selesai" yang eksplisit sebelum memulai tugas. Latih self-compassion.'),
            # E risks
            (E < 35 and A < 40, 'Kesan Dingin atau Tidak Dapat Didekati',
             'Kombinasi Extraversion dan Agreeableness rendah bisa membuat orang pertama kali menganggapmu sulit atau tidak ramah.',
             'Investasikan dalam koneksi satu-satu yang lebih dalam daripada interaksi sosial yang luas.'),
            # A risks
            (A >= 70 and N >= 65, 'People-Pleasing dan Burnout Emosional',
             'Sangat ingin menyenangkan orang lain dikombinasikan dengan kepekaan tinggi bisa membuatmu sulit menolak permintaan dan menguras energi emosional.',
             'Latih asertivitas — mengatakan tidak adalah bentuk self-care, bukan keegoisan.'),
            (A >= 70 and C < 40, 'Kesulitan Prioritas dan Batas Tegas',
             'Terlalu akomodatif bisa mengorbankan tujuanmu sendiri. Kamu cenderung memprioritaskan kebutuhan orang lain di atas kebutuhanmu.',
             'Buat "non-negotiable list" — hal-hal yang tidak bisa kamu kompromikan untuk orang lain.'),
            # N risks
            (N >= 70, 'Reaktivitas Emosional Tinggi',
             'Kepekaan emosional yang tinggi bisa membuatmu bereaksi berlebihan terhadap stres, kritik, atau ketidakpastian — dan ini bisa memengaruhi pengambilan keputusan.',
             'Kembangkan "ruang jeda" antara stimulus dan respons. Teknik breathing, journaling, atau mindfulness sangat efektif.'),
            (N >= 65 and E >= 65, 'Energi Sosial Tidak Stabil',
             'Kamu menginginkan koneksi sosial tapi mudah terkuras secara emosional olehnya — ini bisa menciptakan pola push-pull dalam hubungan.',
             'Kenali tanda-tanda emotional depletion lebih awal dan rencanakan recovery time setelah interaksi sosial intensif.'),
        ],
        'en': [
            (iq >= 120 and C < 40, 'Intellectual Overconfidence Trap',
             'High IQ can create a belief that you are always right or know better. This may cause you to dismiss input from others.',
             'Practice intellectual humility — actively seek out perspectives that challenge your views.'),
            (iq >= 120 and E < 40, 'Intellectual Isolation',
             'High intelligence combined with low Extraversion can create unintentional social distance. Others may find it hard to relate.',
             'Practice accessible communication — explain ideas in simple language and show genuine interest in others\' perspectives.'),
            (O >= 70 and C < 40, 'Unfinished Project Syndrome',
             'High Openness generates many ideas and interests, but without sufficient Conscientiousness, you tend to abandon projects midway.',
             'Apply a "finish before starting" rule — limit active projects to 2-3 at a time.'),
            (O >= 70 and N >= 65, 'Overstimulation Overwhelm',
             'A mind constantly seeking new input combined with high emotional sensitivity can cause mental overload.',
             'Schedule daily "digital detox" and reflection time without new input.'),
            (C >= 70 and A < 40, 'Rigidity and Interpersonal Conflict',
             'High rigid standards can create friction with people who work differently. You may come across as critical or overly demanding.',
             'Practice intentional flexibility — allow some things to be done in ways other than your own.'),
            (C >= 70 and N >= 65, 'Perfectionist Burnout',
             'The combination of high standards and anxiety is a recipe for burnout. You struggle to feel "good enough" about your work.',
             'Set an explicit definition of "done" before starting tasks. Practice self-compassion.'),
            (E < 35 and A < 40, 'Cold or Unapproachable Impression',
             'Low Extraversion combined with low Agreeableness can make people initially perceive you as difficult or unfriendly.',
             'Invest in deeper one-on-one connections rather than broad social interactions.'),
            (A >= 70 and N >= 65, 'People-Pleasing and Emotional Burnout',
             'Wanting to please others combined with high sensitivity can make it hard to decline requests and emotionally drains you.',
             'Practice assertiveness — saying no is self-care, not selfishness.'),
            (A >= 70 and C < 40, 'Difficulty with Priorities and Firm Limits',
             'Being overly accommodating can sacrifice your own goals. You tend to prioritize others\' needs above your own.',
             'Create a "non-negotiable list" — things you cannot compromise for others.'),
            (N >= 70, 'High Emotional Reactivity',
             'High emotional sensitivity can cause you to overreact to stress, criticism, or uncertainty — affecting decision-making.',
             'Develop a "pause space" between stimulus and response. Breathing techniques, journaling, or mindfulness are very effective.'),
            (N >= 65 and E >= 65, 'Unstable Social Energy',
             'You desire social connection but are easily emotionally drained by it — creating a push-pull pattern in relationships.',
             'Recognize signs of emotional depletion early and plan recovery time after intensive social interactions.'),
        ],
    }

    for condition, title, desc, mitigation in _bs[lang]:
        if condition:
            results.append({'title': title, 'desc': desc, 'mitigation': mitigation})

    # Minimal 1 item, maksimal 4
    if not results:
        if lang == 'id':
            results.append({
                'title': 'Zona Nyaman yang Terlalu Luas',
                'desc': 'Profilmu cukup seimbang, namun keseimbangan juga bisa berarti kurang dorongan untuk keluar dari zona nyaman.',
                'mitigation': 'Tetapkan satu tantangan baru setiap bulan yang sedikit di luar zona nyamanmu.',
            })
        else:
            results.append({
                'title': 'Overly Wide Comfort Zone',
                'desc': 'Your profile is quite balanced, but balance can also mean less drive to step outside your comfort zone.',
                'mitigation': 'Set one new challenge each month that is slightly outside your comfort zone.',
            })
    return results[:4]


# ══════════════════════════════════════════════════════════════════
# LAYER 6 — DEVELOPMENT ROADMAP 3 BULAN
# ══════════════════════════════════════════════════════════════════

def get_roadmap(iq, scores, cognitive_profile, careers, lang='id'):
    """
    Generate 3-month development roadmap berdasarkan profil.
    Return: list of 3 dict {month, focus, actions: [str]}
    """
    O,C,E,A,N = scores['O'],scores['C'],scores['E'],scores['A'],scores['N']
    top_career = careers[0]['name'] if careers else ('Karir Pilihan' if lang=='id' else 'Chosen Career')

    # Cari cognitive weakness (rank terburuk)
    cog_sorted = sorted(cognitive_profile.items(), key=lambda x: x[1]['score_pct'])
    weak_cog   = cog_sorted[0][0] if cog_sorted else 'fluid'

    cog_fix_id = {
        'fluid':        'Latihan deret angka dan pola 15 menit/hari (aplikasi: Lumosity, Elevate)',
        'crystallized': 'Baca 1 buku non-fiksi per bulan + review vocab harian',
        'abstract':     'Kerjakan soal logika dan silogisme 3x seminggu',
        'quantitative': 'Review matematika dasar dan kerjakan soal numerik harian',
        'spatial':      'Puzzle visual, origami, atau game strategi berbasis spasial',
    }
    cog_fix_en = {
        'fluid':        'Practice number sequences and patterns 15 min/day (apps: Lumosity, Elevate)',
        'crystallized': 'Read 1 non-fiction book per month + daily vocabulary review',
        'abstract':     'Work on logic and syllogism problems 3x per week',
        'quantitative': 'Review foundational math and work daily numerical problems',
        'spatial':      'Visual puzzles, origami, or spatial strategy games',
    }
    cog_fix = cog_fix_id if lang == 'id' else cog_fix_en

    if lang == 'id':
        roadmap = [
            {
                'month': 1,
                'focus': 'Fondasi & Kesadaran Diri',
                'actions': [
                    f'Pelajari lebih dalam tentang profil kepribadianmu — baca 1 buku tentang {("Openness & kreativitas" if O>=60 else "produktivitas & disiplin")}',
                    cog_fix.get(weak_cog, 'Latihan kognitif harian 15 menit'),
                    'Mulai journaling harian (5-10 menit) untuk tracking mood dan produktivitas',
                    f'Research tentang karir {top_career} — cari 3 profesional di bidang tersebut di LinkedIn',
                    'Tetapkan 1 habit baru yang mendukung tujuan jangka panjangmu' if C < 55 else 'Evaluasi sistem produktivitas yang ada dan perbaiki 1 bottleneck utama',
                ],
            },
            {
                'month': 2,
                'focus': 'Pengembangan Skill & Jaringan',
                'actions': [
                    f'Ambil 1 online course yang relevan dengan {top_career} (Coursera, edX, atau Udemy)',
                    'Bangun atau perbarui profil LinkedIn dengan highlight kekuatan pribadimu' if E >= 50 else 'Mulai aktif di 1 komunitas online yang relevan dengan minatmu',
                    'Kerjakan 1 proyek kecil yang menunjukkan kemampuanmu secara konkret',
                    'Latihan presentasi atau komunikasi — join Toastmasters atau rekam video penjelasan' if E < 50 else 'Lakukan 2-3 informational interview dengan profesional di bidang targetmu',
                    'Review dan sesuaikan tujuan dari bulan pertama',
                ],
            },
            {
                'month': 3,
                'focus': 'Aksi & Eksekusi Nyata',
                'actions': [
                    f'Apply ke 3-5 posisi atau peluang di bidang {top_career}',
                    'Finalisasi portfolio atau showcase dari proyek yang sudah dikerjakan',
                    'Minta feedback dari mentor atau profesional tepercaya tentang progresmu',
                    'Tetapkan OKR (Objectives & Key Results) untuk 3 bulan berikutnya',
                    'Rayakan progress — dokumentasikan perjalananmu dan apa yang sudah berubah',
                ],
            },
        ]
    else:
        roadmap = [
            {
                'month': 1,
                'focus': 'Foundation & Self-Awareness',
                'actions': [
                    f'Dive deeper into your personality profile — read 1 book on {("Openness & creativity" if O>=60 else "productivity & discipline")}',
                    cog_fix.get(weak_cog, 'Daily 15-minute cognitive training'),
                    'Start daily journaling (5-10 min) to track mood and productivity',
                    f'Research {top_career} — find 3 professionals in the field on LinkedIn',
                    'Establish 1 new habit that supports your long-term goals' if C < 55 else 'Evaluate your existing productivity system and fix 1 main bottleneck',
                ],
            },
            {
                'month': 2,
                'focus': 'Skill Development & Networking',
                'actions': [
                    f'Take 1 online course relevant to {top_career} (Coursera, edX, or Udemy)',
                    'Build or update your LinkedIn profile highlighting your personal strengths' if E >= 50 else 'Become active in 1 online community relevant to your interests',
                    'Complete 1 small project that concretely demonstrates your abilities',
                    'Practice presentation or communication — join Toastmasters or record explanation videos' if E < 50 else 'Conduct 2-3 informational interviews with professionals in your target field',
                    'Review and adjust goals from month one',
                ],
            },
            {
                'month': 3,
                'focus': 'Action & Real Execution',
                'actions': [
                    f'Apply to 3-5 positions or opportunities in {top_career}',
                    'Finalize portfolio or showcase from completed projects',
                    'Request feedback from a mentor or trusted professional on your progress',
                    'Set OKRs (Objectives & Key Results) for the next 3 months',
                    'Celebrate progress — document your journey and what has changed',
                ],
            },
        ]

    return roadmap