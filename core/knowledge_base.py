"""
core/knowledge_base.py
────────────────────────────────────────────────────────────
Knowledge Base — satu-satunya sumber kebenaran untuk:
  • Soal Big Five (bilingual, relasi dimensi, reverse scoring)
  • Soal IQ (bilingual, kategori, difficulty)
  • Aturan interpretasi dimensi per level
  • Career mapping rules
  • Archetype rules
────────────────────────────────────────────────────────────
"""

# ══════════════════════════════════════════════════════════════
# BIG FIVE KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════

# Metadata dimensi
BF_DIMENSIONS = {
    'O': {
        'id': 'Openness to Experience',
        'en': 'Openness to Experience',
        'short_id': 'Keterbukaan',
        'short_en': 'Openness',
        'low_id':  'Konvensional & Praktis',
        'low_en':  'Conventional & Practical',
        'high_id': 'Kreatif & Imajinatif',
        'high_en': 'Creative & Imaginative',
        'color':   '#f97316',
    },
    'C': {
        'id': 'Conscientiousness',
        'en': 'Conscientiousness',
        'short_id': 'Kesadaran',
        'short_en': 'Conscientiousness',
        'low_id':  'Fleksibel & Spontan',
        'low_en':  'Flexible & Spontaneous',
        'high_id': 'Terorganisir & Disiplin',
        'high_en': 'Organized & Disciplined',
        'color':   '#3b82f6',
    },
    'E': {
        'id': 'Extraversion',
        'en': 'Extraversion',
        'short_id': 'Ekstraversi',
        'short_en': 'Extraversion',
        'low_id':  'Introvert & Reflektif',
        'low_en':  'Introverted & Reflective',
        'high_id': 'Ekstrovert & Sosial',
        'high_en': 'Extroverted & Social',
        'color':   '#8b5cf6',
    },
    'A': {
        'id': 'Agreeableness',
        'en': 'Agreeableness',
        'short_id': 'Keramahan',
        'short_en': 'Agreeableness',
        'low_id':  'Kompetitif & Tegas',
        'low_en':  'Competitive & Assertive',
        'high_id': 'Kooperatif & Empatik',
        'high_en': 'Cooperative & Empathic',
        'color':   '#27ae60',
    },
    'N': {
        'id': 'Neuroticism',
        'en': 'Neuroticism',
        'short_id': 'Neurotisme',
        'short_en': 'Neuroticism',
        'low_id':  'Stabil & Tenang',
        'low_en':  'Stable & Calm',
        'high_id': 'Sensitif & Emosional',
        'high_en': 'Sensitive & Emotional',
        'color':   '#e74c3c',
    },
}

# Level interpretasi per dimensi (skor 0-100)
BF_LEVELS = [
    {'min': 80, 'key': 'very_high', 'id': 'Sangat Tinggi', 'en': 'Very High'},
    {'min': 65, 'key': 'high',      'id': 'Tinggi',        'en': 'High'},
    {'min': 40, 'key': 'average',   'id': 'Rata-rata',     'en': 'Average'},
    {'min': 25, 'key': 'low',       'id': 'Rendah',        'en': 'Low'},
    {'min':  0, 'key': 'very_low',  'id': 'Sangat Rendah', 'en': 'Very Low'},
]

def get_bf_level(score: float) -> dict:
    for lvl in BF_LEVELS:
        if score >= lvl['min']:
            return lvl
    return BF_LEVELS[-1]


# Soal Big Five — (id, trait, text_id, text_en, reversed)
BF_QUESTIONS = [
    # ── Openness ──
    ('O_01','O','Saya selalu ingin tahu tentang berbagai hal dan menikmati belajar hal baru.','I am always curious about many things and enjoy learning new topics.',False),
    ('O_02','O','Saya suka berimajinasi dan memiliki kehidupan batin yang kaya.','I enjoy daydreaming and have a rich inner life.',False),
    ('O_03','O','Saya lebih suka rutinitas yang sudah terbukti daripada mencoba cara baru.','I prefer tried-and-true routines over trying new ways of doing things.',True),
    ('O_04','O','Saya mudah terpesona oleh seni, musik, atau karya kreatif.','I am easily captivated by art, music, or creative works.',False),
    ('O_05','O','Saya tertarik pada topik-topik abstrak dan filosofis.','I am drawn to abstract and philosophical topics.',False),
    ('O_06','O','Saya memiliki imajinasi yang vivid dan aktif.','I have a vivid and active imagination.',False),
    ('O_07','O','Saya tidak terlalu tertarik pada seni atau sastra.','I am not particularly interested in art or literature.',True),
    ('O_08','O','Saya menikmati memikirkan teori dan ide-ide yang kompleks.','I enjoy thinking about theories and complex ideas.',False),
    ('O_09','O','Saya jarang mencari pengalaman baru atau tidak biasa.','I rarely seek out new or unusual experiences.',True),
    ('O_10','O','Saya mudah menyadari keindahan dalam hal-hal di sekitar saya.','I easily notice beauty in the things around me.',False),
    # ── Conscientiousness ──
    ('C_01','C','Saya selalu menyelesaikan tugas sesuai rencana yang telah saya buat.','I always complete tasks according to the plans I have made.',False),
    ('C_02','C','Saya cenderung rapi dan terorganisir dalam keseharian.','I tend to be neat and organized in my daily life.',False),
    ('C_03','C','Saya sering menunda-nunda pekerjaan yang harus diselesaikan.','I often procrastinate on work that needs to be done.',True),
    ('C_04','C','Saya mempertimbangkan konsekuensi secara matang sebelum bertindak.','I carefully consider consequences before taking action.',False),
    ('C_05','C','Saya bekerja keras untuk mencapai tujuan saya.','I work hard to achieve my goals.',False),
    ('C_06','C','Saya membuat rencana dan mengikutinya dengan disiplin.','I make plans and follow them with discipline.',False),
    ('C_07','C','Saya sering lupa menaruh barang-barang saya.','I often forget where I put my belongings.',True),
    ('C_08','C','Saya sangat teliti dalam segala hal yang saya lakukan.','I am very thorough in everything I do.',False),
    ('C_09','C','Saya kadang bertindak tanpa berpikir panjang terlebih dahulu.','I sometimes act without thinking things through first.',True),
    ('C_10','C','Saya memastikan semua tugas selesai sebelum beristirahat.','I make sure all tasks are done before I rest.',False),
    # ── Extraversion ──
    ('E_01','E','Saya merasa bersemangat dan penuh energi ketika berkumpul dengan banyak orang.','I feel excited and full of energy when around a lot of people.',False),
    ('E_02','E','Saya mudah akrab dengan orang-orang yang baru saya temui.','I easily get along with people I have just met.',False),
    ('E_03','E','Saya lebih suka menghabiskan waktu sendirian daripada di keramaian.','I prefer spending time alone rather than in crowds.',True),
    ('E_04','E','Saya sering menjadi pusat perhatian dalam suatu kelompok.','I often become the center of attention in a group.',False),
    ('E_05','E','Saya terasa hidup dan bersemangat ketika berada di lingkungan sosial.','I feel alive and energized in social environments.',False),
    ('E_06','E','Saya mudah memulai percakapan dengan orang yang belum saya kenal.','I easily start conversations with people I do not know yet.',False),
    ('E_07','E','Saya merasa lelah setelah terlalu banyak berinteraksi sosial.','I feel drained after too much social interaction.',True),
    ('E_08','E','Saya menikmati menjadi bagian dari kelompok besar.','I enjoy being part of a large group.',False),
    ('E_09','E','Saya lebih suka mendengarkan daripada berbicara dalam diskusi kelompok.','I prefer listening rather than speaking in group discussions.',True),
    ('E_10','E','Saya merasa bersemangat dan antusias dalam situasi baru.','I feel enthusiastic and eager in new situations.',False),
    # ── Agreeableness ──
    ('A_01','A','Saya peduli dengan perasaan orang lain dan mudah berempati.','I care about others\'s feelings and empathize easily.',False),
    ('A_02','A','Saya suka membantu orang lain meskipun tidak ada manfaat langsung bagi saya.','I like helping others even when there is no direct benefit for me.',False),
    ('A_03','A','Saya kadang sulit mempercayai motivasi di balik tindakan orang lain.','I sometimes find it hard to trust the motives behind other people\'s actions.',True),
    ('A_04','A','Saya menghindari konflik dan mencari jalan damai dalam perselisihan.','I avoid conflict and look for peaceful solutions in disagreements.',False),
    ('A_05','A','Saya bersikap lemah lembut dan penuh perhatian kepada orang di sekitar saya.','I am gentle and attentive to the people around me.',False),
    ('A_06','A','Saya percaya bahwa orang pada dasarnya memiliki niat baik.','I believe that people are fundamentally well-intentioned.',False),
    ('A_07','A','Saya terkadang terasa dingin dan tidak peduli pada masalah orang lain.','I sometimes come across as cold and indifferent to other people\'s problems.',True),
    ('A_08','A','Saya mudah memaafkan orang yang telah menyakiti saya.','I easily forgive people who have hurt me.',False),
    ('A_09','A','Saya lebih mementingkan kepentingan diri sendiri dibanding orang lain.','I prioritize my own interests over those of others.',True),
    ('A_10','A','Saya berusaha membuat orang lain merasa nyaman saat bersama saya.','I try to make others feel comfortable when they are with me.',False),
    # ── Neuroticism ──
    ('N_01','N','Saya sering merasa cemas atau khawatir tanpa alasan yang jelas.','I often feel anxious or worried without a clear reason.',False),
    ('N_02','N','Suasana hati saya bisa berubah-ubah dengan cukup cepat.','My mood can change quite quickly.',False),
    ('N_03','N','Saya cenderung tetap tenang bahkan dalam situasi yang menegangkan.','I tend to stay calm even in tense situations.',True),
    ('N_04','N','Saya mudah merasa sedih atau tertekan.','I easily feel sad or depressed.',False),
    ('N_05','N','Saya sering merasa tidak yakin dengan keputusan yang saya buat.','I often feel uncertain about the decisions I make.',False),
    ('N_06','N','Saya mudah merasa frustrasi atau kesal saat segala sesuatu tidak berjalan lancar.','I easily feel frustrated or irritated when things do not go smoothly.',False),
    ('N_07','N','Saya jarang merasa sedih atau murung.','I rarely feel sad or gloomy.',True),
    ('N_08','N','Saya sering merasa tertekan oleh tuntutan kehidupan sehari-hari.','I often feel overwhelmed by the demands of daily life.',False),
    ('N_09','N','Saya relatif stabil secara emosional dan tidak mudah terguncang.','I am relatively emotionally stable and not easily rattled.',True),
    ('N_10','N','Saya kadang merasa hidup saya tidak terkendali.','I sometimes feel like my life is out of control.',False),
]

# Index soal BF by trait
BF_BY_TRAIT = {t: [q for q in BF_QUESTIONS if q[1]==t] for t in 'OCEAN'}


# ══════════════════════════════════════════════════════════════
# IQ KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════

IQ_CATEGORY_MAP = {
    'Deret Angka':    {'en': 'Number Series',   'cognitive': 'fluid'},
    'Analogi Verbal': {'en': 'Verbal Analogy',  'cognitive': 'crystallized'},
    'Logika':         {'en': 'Logic',           'cognitive': 'abstract'},
    'Numerik':        {'en': 'Numeric',         'cognitive': 'quantitative'},
    'Pola Visual':    {'en': 'Visual Pattern',  'cognitive': 'spatial'},
}

IQ_COGNITIVE_DOMAINS = {
    'fluid':        {'id': 'Penalaran Cair',         'en': 'Fluid Reasoning',        'color': '#f97316'},
    'crystallized': {'id': 'Kecerdasan Verbal',      'en': 'Verbal Intelligence',     'color': '#8b5cf6'},
    'abstract':     {'id': 'Penalaran Abstrak',      'en': 'Abstract Reasoning',      'color': '#3b82f6'},
    'quantitative': {'id': 'Penalaran Kuantitatif',  'en': 'Quantitative Reasoning',  'color': '#27ae60'},
    'spatial':      {'id': 'Kecerdasan Spasial',     'en': 'Spatial Intelligence',    'color': '#f5a623'},
}

IQ_QUESTIONS = [
    # ── Deret Angka / Number Series ──
    {
        'id': 'IQ_DA_1', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 1,
        'q_id': 'Lanjutkan deret berikut:\n2, 4, 6, 8, __',
        'q_en': 'Continue the series:\n2, 4, 6, 8, __',
        'opts': ['9','10','12','14'], 'ans': 1,
        'exp_id': 'Deret aritmetika +2. Setelah 8 adalah 10.',
        'exp_en': 'Arithmetic series +2. After 8 comes 10.',
    },
    {
        'id': 'IQ_DA_2', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 2,
        'q_id': 'Lanjutkan deret berikut:\n1, 4, 9, 16, 25, __',
        'q_en': 'Continue the series:\n1, 4, 9, 16, 25, __',
        'opts': ['30','36','34','32'], 'ans': 1,
        'exp_id': 'Deret kuadrat sempurna: 6²=36.',
        'exp_en': 'Perfect squares: 6²=36.',
    },
    {
        'id': 'IQ_DA_3', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 3,
        'q_id': 'Lanjutkan deret berikut:\n2, 4, 8, 16, __',
        'q_en': 'Continue the series:\n2, 4, 8, 16, __',
        'opts': ['24','32','28','30'], 'ans': 1,
        'exp_id': 'Deret geometri ×2. 16×2=32.',
        'exp_en': 'Geometric series ×2. 16×2=32.',
    },
    {
        'id': 'IQ_DA_4', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 3,
        'q_id': 'Lanjutkan deret berikut:\n1, 1, 2, 3, 5, 8, __',
        'q_en': 'Continue the series:\n1, 1, 2, 3, 5, 8, __',
        'opts': ['11','12','13','14'], 'ans': 2,
        'exp_id': 'Fibonacci: 5+8=13.',
        'exp_en': 'Fibonacci: 5+8=13.',
    },
    {
        'id': 'IQ_DA_5', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 4,
        'q_id': 'Lanjutkan deret berikut:\n3, 6, 11, 18, 27, __',
        'q_en': 'Continue the series:\n3, 6, 11, 18, 27, __',
        'opts': ['36','38','40','35'], 'ans': 1,
        'exp_id': 'Selisih +3,+5,+7,+9,+11. 27+11=38.',
        'exp_en': 'Differences +3,+5,+7,+9,+11. 27+11=38.',
    },
    {
        'id': 'IQ_DA_6', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 5,
        'q_id': 'Lanjutkan deret berikut:\n2, 6, 12, 20, 30, __',
        'q_en': 'Continue the series:\n2, 6, 12, 20, 30, __',
        'opts': ['40','42','44','45'], 'ans': 1,
        'exp_id': 'Pola n×(n+1). Suku ke-6: 6×7=42.',
        'exp_en': 'Pattern n×(n+1). 6th term: 6×7=42.',
    },
    {
        'id': 'IQ_DA_7', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 6,
        'q_id': 'Lanjutkan deret berikut:\n1, 3, 7, 13, 21, 31, __',
        'q_en': 'Continue the series:\n1, 3, 7, 13, 21, 31, __',
        'opts': ['40','41','43','45'], 'ans': 2,
        'exp_id': 'Selisih +2,+4,+6,+8,+10,+12. 31+12=43.',
        'exp_en': 'Differences +2,+4,+6,+8,+10,+12. 31+12=43.',
    },
    {
        'id': 'IQ_DA_8', 'cat_id': 'Deret Angka', 'cat_en': 'Number Series', 'difficulty': 7,
        'q_id': 'Lanjutkan deret berikut:\n2, 3, 5, 8, 13, 21, __',
        'q_en': 'Continue the series:\n2, 3, 5, 8, 13, 21, __',
        'opts': ['32','33','34','35'], 'ans': 2,
        'exp_id': 'Fibonacci-like: 13+21=34.',
        'exp_en': 'Fibonacci-like: 13+21=34.',
    },
    # ── Analogi Verbal / Verbal Analogy ──
    {
        'id': 'IQ_AV_1', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 1,
        'q_id': 'Panas adalah lawan dari dingin.\nTerang adalah lawan dari __',
        'q_en': 'Hot is the opposite of cold.\nBright is the opposite of __',
        'opts_id': ['Siang','Gelap','Malam','Redup'],
        'opts_en': ['Daytime','Dark','Night','Dim'], 'ans': 1,
        'exp_id': 'Lawan dari terang adalah gelap.',
        'exp_en': 'The opposite of bright is dark.',
    },
    {
        'id': 'IQ_AV_2', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 2,
        'q_id': 'Dokter : Rumah Sakit = Guru : __',
        'q_en': 'Doctor : Hospital = Teacher : __',
        'opts_id': ['Kantor','Perpustakaan','Sekolah','Studio'],
        'opts_en': ['Office','Library','School','Studio'], 'ans': 2,
        'exp_id': 'Dokter bekerja di RS, Guru bekerja di Sekolah.',
        'exp_en': 'A Doctor works at a Hospital, a Teacher at a School.',
    },
    {
        'id': 'IQ_AV_3', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 2,
        'q_id': 'Burung : Terbang = Ikan : __',
        'q_en': 'Bird : Fly = Fish : __',
        'opts_id': ['Berlari','Berenang','Melompat','Merayap'],
        'opts_en': ['Run','Swim','Jump','Crawl'], 'ans': 1,
        'exp_id': 'Burung terbang, ikan berenang.',
        'exp_en': 'Birds fly, fish swim.',
    },
    {
        'id': 'IQ_AV_4', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 3,
        'q_id': 'Buku : Perpustakaan = Lukisan : __',
        'q_en': 'Book : Library = Painting : __',
        'opts_id': ['Toko','Museum','Galeri','Gudang'],
        'opts_en': ['Shop','Museum','Gallery','Warehouse'], 'ans': 2,
        'exp_id': 'Buku di Perpustakaan, Lukisan di Galeri.',
        'exp_en': 'Books in Libraries, Paintings in Galleries.',
    },
    {
        'id': 'IQ_AV_5', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 4,
        'q_id': 'Penulis : Novel = Komposer : __',
        'q_en': 'Writer : Novel = Composer : __',
        'opts_id': ['Buku','Simfoni','Lukisan','Film'],
        'opts_en': ['Book','Symphony','Painting','Film'], 'ans': 1,
        'exp_id': 'Penulis → Novel, Komposer → Simfoni.',
        'exp_en': 'Writer → Novel, Composer → Symphony.',
    },
    {
        'id': 'IQ_AV_6', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 5,
        'q_id': 'Roti : Tepung = Kain : __',
        'q_en': 'Bread : Flour = Fabric : __',
        'opts_id': ['Baju','Benang','Kapas','Jarum'],
        'opts_en': ['Shirt','Thread','Cotton','Needle'], 'ans': 1,
        'exp_id': 'Roti dari Tepung, Kain dari Benang.',
        'exp_en': 'Bread from Flour, Fabric from Thread.',
    },
    {
        'id': 'IQ_AV_7', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 6,
        'q_id': 'Desibel : Suara = Richter : __',
        'q_en': 'Decibel : Sound = Richter : __',
        'opts_id': ['Angin','Gempa bumi','Tekanan','Cahaya'],
        'opts_en': ['Wind','Earthquake','Pressure','Light'], 'ans': 1,
        'exp_id': 'Desibel mengukur Suara, Richter mengukur Gempa.',
        'exp_en': 'Decibels measure Sound, Richter measures Earthquakes.',
    },
    {
        'id': 'IQ_AV_8', 'cat_id': 'Analogi Verbal', 'cat_en': 'Verbal Analogy', 'difficulty': 7,
        'q_id': 'Anemia : Darah = Osteoporosis : __',
        'q_en': 'Anemia : Blood = Osteoporosis : __',
        'opts_id': ['Otot','Kulit','Tulang','Saraf'],
        'opts_en': ['Muscle','Skin','Bone','Nerve'], 'ans': 2,
        'exp_id': 'Anemia → Darah, Osteoporosis → Tulang.',
        'exp_en': 'Anemia → Blood, Osteoporosis → Bone.',
    },
    # ── Logika / Logic ──
    {
        'id': 'IQ_LG_1', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 1,
        'q_id': 'Semua kucing adalah hewan.\nBeberapa hewan adalah predator.\nKesimpulan yang PASTI benar:',
        'q_en': 'All cats are animals.\nSome animals are predators.\nWhich conclusion is DEFINITELY true?',
        'opts_id': ['Semua kucing adalah predator','Beberapa kucing mungkin adalah predator','Tidak ada kucing yang predator','Semua predator adalah kucing'],
        'opts_en': ['All cats are predators','Some cats might be predators','No cats are predators','All predators are cats'], 'ans': 1,
        'exp_id': 'Hanya "mungkin" yang valid karena tidak pasti.',
        'exp_en': 'Only "might be" is valid as it\'s not certain.',
    },
    {
        'id': 'IQ_LG_2', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 2,
        'q_id': 'Jika hari hujan, maka jalanan basah.\nJalanan tidak basah. Kesimpulan:',
        'q_en': 'If it rains, the road is wet.\nThe road is not wet. Conclusion:',
        'opts_id': ['Hari hujan','Hari tidak hujan','Jalanan kering karena angin','Tidak dapat disimpulkan'],
        'opts_en': ['It is raining','It is not raining','Road is dry due to wind','Cannot be concluded'], 'ans': 1,
        'exp_id': 'Modus tollens: bukan Q → bukan P.',
        'exp_en': 'Modus tollens: not Q → not P.',
    },
    {
        'id': 'IQ_LG_3', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 2,
        'q_id': 'A lebih tua dari B. B lebih tua dari C. D lebih muda dari C.\nSiapa yang paling tua?',
        'q_en': 'A is older than B. B is older than C. D is younger than C.\nWho is the oldest?',
        'opts_id': ['B','C','A','D'], 'opts_en': ['B','C','A','D'], 'ans': 2,
        'exp_id': 'Urutan: A>B>C>D. A paling tua.',
        'exp_en': 'Order: A>B>C>D. A is oldest.',
    },
    {
        'id': 'IQ_LG_4', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 3,
        'q_id': 'Andi berolahraga setiap hari ganjil selama 5 hari (hari ke-1,3,5).\nBerapa total hari?',
        'q_en': 'Andi exercises on every odd day over 5 days (days 1,3,5).\nHow many days total?',
        'opts_id': ['2 hari','3 hari','4 hari','5 hari'],
        'opts_en': ['2 days','3 days','4 days','5 days'], 'ans': 1,
        'exp_id': 'Hari ganjil 1-5: hari ke-1,3,5 = 3 hari.',
        'exp_en': 'Odd days 1-5: days 1,3,5 = 3 days.',
    },
    {
        'id': 'IQ_LG_5', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 4,
        'q_id': 'Semua manajer adalah karyawan.\nBeberapa karyawan adalah perempuan.\nKesimpulan PASTI benar:',
        'q_en': 'All managers are employees.\nSome employees are women.\nWhich is DEFINITELY true?',
        'opts_id': ['Semua manajer perempuan','Beberapa manajer perempuan','Tidak ada manajer perempuan','Beberapa karyawan adalah manajer'],
        'opts_en': ['All managers are women','Some managers are women','No managers are women','Some employees are managers'], 'ans': 3,
        'exp_id': 'Semua manajer = karyawan → beberapa karyawan adalah manajer.',
        'exp_en': 'All managers are employees → some employees are managers.',
    },
    {
        'id': 'IQ_LG_6', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 5,
        'q_id': 'Jika semua A adalah B, dan tidak ada B yang C,\nmaka kesimpulan yang benar:',
        'q_en': 'If all A are B, and no B are C,\nthen the correct conclusion is:',
        'opts_id': ['Beberapa A adalah C','Tidak ada A yang C','Semua C adalah A','Beberapa B adalah A'],
        'opts_en': ['Some A are C','No A are C','All C are A','Some B are A'], 'ans': 1,
        'exp_id': 'Semua A=B, tidak ada B=C → tidak ada A=C.',
        'exp_en': 'All A=B, no B=C → no A=C.',
    },
    {
        'id': 'IQ_LG_7', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 6,
        'q_id': 'Dua kereta menuju satu sama lain.\nJarak 600 km, kecepatan 100 dan 50 km/jam.\nBerapa jam sampai bertemu?',
        'q_en': 'Two trains head toward each other.\nDistance 600 km, speeds 100 and 50 km/h.\nHow many hours until they meet?',
        'opts_id': ['3 jam','4 jam','5 jam','6 jam'],
        'opts_en': ['3 hours','4 hours','5 hours','6 hours'], 'ans': 1,
        'exp_id': 'Kecepatan gabungan=150. 600/150=4 jam.',
        'exp_en': 'Combined speed=150. 600/150=4 hours.',
    },
    {
        'id': 'IQ_LG_8', 'cat_id': 'Logika', 'cat_en': 'Logic', 'difficulty': 7,
        'q_id': '5 orang duduk berurutan. A di kiri B. C di antara D dan E.\nD paling kiri. Siapa di posisi ke-3?',
        'q_en': '5 people sit in a row. A is left of B. C is between D and E.\nD is leftmost. Who is in position 3?',
        'opts_id': ['A','B','E','C'], 'opts_en': ['A','B','E','C'], 'ans': 2,
        'exp_id': 'Urutan: D,C,E,A,B. Posisi ke-3 = E.',
        'exp_en': 'Order: D,C,E,A,B. Position 3 = E.',
    },
    # ── Numerik / Numeric ──
    {
        'id': 'IQ_NM_1', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 1,
        'q_id': 'Berapa nilai dari 15 × 4?',
        'q_en': 'What is the value of 15 × 4?',
        'opts': ['50','55','60','65'], 'ans': 2,
        'exp_id': '15 × 4 = 60.',
        'exp_en': '15 × 4 = 60.',
    },
    {
        'id': 'IQ_NM_2', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 2,
        'q_id': 'Sebuah persegi memiliki keliling 36 cm. Berapa luasnya?',
        'q_en': 'A square has a perimeter of 36 cm. What is its area?',
        'opts': ['72 cm²','81 cm²','64 cm²','49 cm²'], 'ans': 1,
        'exp_id': 'Sisi=9. Luas=81 cm².',
        'exp_en': 'Side=9. Area=81 cm².',
    },
    {
        'id': 'IQ_NM_3', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 2,
        'q_id': 'Jika 20% dari X adalah 50, maka X adalah __',
        'q_en': 'If 20% of X is 50, then X is __',
        'opts': ['200','250','300','150'], 'ans': 1,
        'exp_id': '0.2×X=50 → X=250.',
        'exp_en': '0.2×X=50 → X=250.',
    },
    {
        'id': 'IQ_NM_4', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 3,
        'q_id': 'Sebuah kereta menempuh 300 km dalam 4 jam.\nBerapa kecepatan rata-ratanya?',
        'q_en': 'A train travels 300 km in 4 hours.\nWhat is its average speed?',
        'opts_id': ['65 km/jam','70 km/jam','75 km/jam','80 km/jam'],
        'opts_en': ['65 km/h','70 km/h','75 km/h','80 km/h'], 'ans': 2,
        'exp_id': '300/4 = 75 km/jam.',
        'exp_en': '300/4 = 75 km/h.',
    },
    {
        'id': 'IQ_NM_5', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 4,
        'q_id': 'Toko memberi diskon 30%. Harga asli Rp200.000.\nHarga setelah diskon?',
        'q_en': 'A store gives 30% discount. Original price Rp200,000.\nPrice after discount?',
        'opts': ['Rp130.000','Rp140.000','Rp150.000','Rp160.000'], 'ans': 1,
        'exp_id': '200.000×0.7=140.000.',
        'exp_en': '200,000×0.7=140,000.',
    },
    {
        'id': 'IQ_NM_6', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 5,
        'q_id': 'Rasio pria:wanita dalam kelas 3:2, total 40 siswa.\nBerapa jumlah wanita?',
        'q_en': 'Male:female ratio is 3:2, 40 students total.\nHow many are female?',
        'opts': ['14','16','18','20'], 'ans': 1,
        'exp_id': '2/5 × 40 = 16.',
        'exp_en': '2/5 × 40 = 16.',
    },
    {
        'id': 'IQ_NM_7', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 6,
        'q_id': 'Angka mana yang merupakan bilangan prima?',
        'q_en': 'Which number is a prime number?',
        'opts': ['51','57','59','63'], 'ans': 2,
        'exp_id': '51=3×17, 57=3×19, 63=7×9. Hanya 59 prima.',
        'exp_en': '51=3×17, 57=3×19, 63=7×9. Only 59 is prime.',
    },
    {
        'id': 'IQ_NM_8', 'cat_id': 'Numerik', 'cat_en': 'Numeric', 'difficulty': 7,
        'q_id': 'Pipa isi kolam 6 jam. Pipa lain kuras 9 jam.\nJika keduanya aktif, berapa jam kolam penuh?',
        'q_en': 'A pipe fills a pool in 6 h. Another drains in 9 h.\nIf both active, how long to fill?',
        'opts_id': ['14 jam','16 jam','18 jam','20 jam'],
        'opts_en': ['14 hours','16 hours','18 hours','20 hours'], 'ans': 2,
        'exp_id': '1/6-1/9=1/18. Total=18 jam.',
        'exp_en': '1/6-1/9=1/18. Total=18 hours.',
    },
    # ── Pola Visual / Visual Pattern ──
    {
        'id': 'IQ_PV_1', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 1,
        'q_id': 'Jika segitiga=3 sisi, segiempat=4, pentagon=5,\noktagon memiliki berapa sisi?',
        'q_en': 'If triangle=3 sides, quadrilateral=4, pentagon=5,\nhow many sides does an octagon have?',
        'opts': ['6','7','8','9'], 'ans': 2,
        'exp_id': 'Octa = 8.',
        'exp_en': 'Octa = 8.',
    },
    {
        'id': 'IQ_PV_2', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 2,
        'q_id': 'Jam menunjukkan pukul 3:00.\nBerapa derajat sudut antara jarum jam dan menit?',
        'q_en': 'Clock shows 3:00.\nWhat is the angle between hour and minute hands?',
        'opts_id': ['60°','75°','90°','120°'],
        'opts_en': ['60°','75°','90°','120°'], 'ans': 2,
        'exp_id': 'Pukul 3:00 = 90° dari angka 12.',
        'exp_en': '3:00 = 90° from 12.',
    },
    {
        'id': 'IQ_PV_3', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 2,
        'q_id': 'Pola: Putih, Hitam, Putih×2, Hitam, Putih×3, Hitam\nBerapa putih sebelum hitam berikutnya?',
        'q_en': 'Pattern: White, Black, White×2, Black, White×3, Black\nHow many whites before the next black?',
        'opts': ['3','4','5','6'], 'ans': 1,
        'exp_id': 'Pola: 1,2,3,4... Berikutnya 4.',
        'exp_en': 'Pattern: 1,2,3,4... Next is 4.',
    },
    {
        'id': 'IQ_PV_4', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 3,
        'q_id': 'Magic square 3×3:\n2  7  6\n9  5  1\n4  3  ?\nBerapa nilai "?"',
        'q_en': 'Magic square 3×3:\n2  7  6\n9  5  1\n4  3  ?\nWhat is "?"',
        'opts': ['7','8','9','6'], 'ans': 1,
        'exp_id': 'Setiap baris/kolom = 15. Kolom kanan: 6+1+?=15 → ?=8.',
        'exp_en': 'Each row/column = 15. Right col: 6+1+?=15 → ?=8.',
    },
    {
        'id': 'IQ_PV_5', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 4,
        'q_id': 'Kubus 3×3×3 dipotong jadi 27 kubus kecil.\nBerapa kubus tanpa sisi terekspos?',
        'q_en': 'A 3×3×3 cube is cut into 27 small cubes.\nHow many have no exposed face?',
        'opts': ['0','1','2','3'], 'ans': 1,
        'exp_id': 'Hanya 1 kubus di tengah tidak terekspos.',
        'exp_en': 'Only 1 cube at the center has no exposed face.',
    },
    {
        'id': 'IQ_PV_6', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 5,
        'q_id': 'Urutan: △, □, △△, □□, △△△, □□□, __',
        'q_en': 'Sequence: △, □, △△, □□, △△△, □□□, __',
        'opts_id': ['△△△△','□□□□','△□','□△'],
        'opts_en': ['△△△△','□□□□','△□','□△'], 'ans': 0,
        'exp_id': 'Pola bergantian bertambah 1. Setelah □×3 adalah △×4.',
        'exp_en': 'Alternating +1. After □×3 comes △×4.',
    },
    {
        'id': 'IQ_PV_7', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 6,
        'q_id': 'Persegi panjang 8×6 dibagi menjadi persegi 2×2.\nBerapa banyak persegi kecil?',
        'q_en': 'An 8×6 rectangle is divided into 2×2 squares.\nHow many small squares?',
        'opts': ['10','12','14','16'], 'ans': 1,
        'exp_id': '(8/2)×(6/2)=4×3=12.',
        'exp_en': '(8/2)×(6/2)=4×3=12.',
    },
    {
        'id': 'IQ_PV_8', 'cat_id': 'Pola Visual', 'cat_en': 'Visual Pattern', 'difficulty': 7,
        'q_id': 'Bayangan cermin dari "3 6 9" adalah __',
        'q_en': 'The mirror image of "3 6 9" is __',
        'opts': ['9 6 3','6 9 3','3 9 6','E 9 E'], 'ans': 0,
        'exp_id': 'Cermin membalik urutan: "9 6 3".',
        'exp_en': 'Mirror reverses order: "9 6 3".',
    },
]

# Index by category
IQ_BY_CAT_ID = {}
IQ_BY_CAT_EN = {}
for _q in IQ_QUESTIONS:
    IQ_BY_CAT_ID.setdefault(_q['cat_id'], []).append(_q)
    IQ_BY_CAT_EN.setdefault(_q['cat_en'], []).append(_q)


# ══════════════════════════════════════════════════════════════
# CAREER KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════
# Format: (name_id, name_en, {required trait thresholds}, iq_min)
CAREER_KB = [
    {
        'id': 'Ilmuwan / Peneliti',
        'en': 'Scientist / Researcher',
        'weights': {'O': 0.35, 'C': 0.30, 'E': -0.05, 'A': 0.10, 'N': -0.20},
        'iq_weight': 0.30,
        'iq_min': 110,
    },
    {
        'id': 'Arsitek / Desainer',
        'en': 'Architect / Designer',
        'weights': {'O': 0.40, 'C': 0.25, 'E': 0.05, 'A': 0.10, 'N': -0.10},
        'iq_weight': 0.20,
        'iq_min': 100,
    },
    {
        'id': 'Pengusaha / Entrepreneur',
        'en': 'Entrepreneur',
        'weights': {'O': 0.20, 'C': 0.20, 'E': 0.30, 'A': 0.05, 'N': -0.25},
        'iq_weight': 0.20,
        'iq_min': 100,
    },
    {
        'id': 'Pemimpin / Manajer',
        'en': 'Manager / Leader',
        'weights': {'O': 0.10, 'C': 0.25, 'E': 0.35, 'A': 0.20, 'N': -0.10},
        'iq_weight': 0.10,
        'iq_min': 95,
    },
    {
        'id': 'Konselor / Psikolog',
        'en': 'Counselor / Psychologist',
        'weights': {'O': 0.15, 'C': 0.15, 'E': 0.15, 'A': 0.40, 'N': -0.15},
        'iq_weight': 0.15,
        'iq_min': 100,
    },
    {
        'id': 'Guru / Pendidik',
        'en': 'Teacher / Educator',
        'weights': {'O': 0.20, 'C': 0.20, 'E': 0.25, 'A': 0.30, 'N': -0.05},
        'iq_weight': 0.05,
        'iq_min': 95,
    },
    {
        'id': 'Insinyur / Teknisi',
        'en': 'Engineer / Technician',
        'weights': {'O': 0.15, 'C': 0.35, 'E': 0.05, 'A': 0.10, 'N': -0.15},
        'iq_weight': 0.35,
        'iq_min': 105,
    },
    {
        'id': 'Dokter / Tenaga Medis',
        'en': 'Doctor / Medical Professional',
        'weights': {'O': 0.15, 'C': 0.30, 'E': 0.10, 'A': 0.25, 'N': -0.20},
        'iq_weight': 0.35,
        'iq_min': 115,
    },
    {
        'id': 'Seniman / Kreator Konten',
        'en': 'Artist / Content Creator',
        'weights': {'O': 0.50, 'C': 0.05, 'E': 0.20, 'A': 0.10, 'N': 0.15},
        'iq_weight': 0.05,
        'iq_min': 90,
    },
    {
        'id': 'Analis Data / Data Scientist',
        'en': 'Data Analyst / Data Scientist',
        'weights': {'O': 0.20, 'C': 0.30, 'E': -0.05, 'A': 0.05, 'N': -0.20},
        'iq_weight': 0.50,
        'iq_min': 110,
    },
    {
        'id': 'Penulis / Jurnalis',
        'en': 'Writer / Journalist',
        'weights': {'O': 0.40, 'C': 0.20, 'E': 0.10, 'A': 0.15, 'N': 0.15},
        'iq_weight': 0.15,
        'iq_min': 100,
    },
    {
        'id': 'Pengacara / Konsultan Hukum',
        'en': 'Lawyer / Legal Consultant',
        'weights': {'O': 0.10, 'C': 0.30, 'E': 0.25, 'A': 0.05, 'N': -0.10},
        'iq_weight': 0.30,
        'iq_min': 110,
    },
    {
        'id': 'Diplomat / Hubungan Internasional',
        'en': 'Diplomat / International Relations',
        'weights': {'O': 0.20, 'C': 0.20, 'E': 0.25, 'A': 0.25, 'N': -0.10},
        'iq_weight': 0.25,
        'iq_min': 110,
    },
    {
        'id': 'Akuntan / Auditor',
        'en': 'Accountant / Auditor',
        'weights': {'O': -0.05, 'C': 0.45, 'E': 0.05, 'A': 0.15, 'N': -0.20},
        'iq_weight': 0.20,
        'iq_min': 100,
    },
    {
        'id': 'Sales / Business Development',
        'en': 'Sales / Business Development',
        'weights': {'O': 0.10, 'C': 0.15, 'E': 0.45, 'A': 0.20, 'N': -0.10},
        'iq_weight': 0.10,
        'iq_min': 90,
    },
]