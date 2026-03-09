"""
app.py — Assessment IQ & Kepribadian v4.0
──────────────────────────────────────────
Fitur baru v4:
  • Bilingual EN/ID — toggle di setiap halaman
  • Weighted IRT-inspired IQ scoring
  • Expert Rule Engine (6 layer)
  • Cognitive Profile breakdown
  • Career recommendations + confidence bar
  • Learning Style Profile
  • Blind Spots & Risk Factors
  • 3-Month Development Roadmap
  • PDF 2-in-1: Executive Summary + Full Report (7 section)
"""

import sys, json, math, random, os
from datetime import datetime
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QFrame,
    QButtonGroup, QSizePolicy, QFileDialog, QGraphicsOpacityEffect,
    QSpacerItem, QMessageBox
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty,
    pyqtSignal, QPoint
)
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QPen, QPalette, QPolygon, QLinearGradient
)

# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
with open('processed/norms.json',    encoding='utf-8') as f: NORMS_DATA    = json.load(f)
with open('processed/clusters.json', encoding='utf-8') as f: CLUSTERS      = json.load(f)
with open('processed/iq_norms.json', encoding='utf-8') as f: IQ_NORMS_DATA = json.load(f)

NORMS        = NORMS_DATA['norms']
POP_STAT     = NORMS_DATA['stats']
IQ_NORMS     = IQ_NORMS_DATA['norms']
IQ_SCORE_MAP = IQ_NORMS_DATA['iq_score_map']

# ══════════════════════════════════════════════════════════════
# i18n — bilingual system
# ══════════════════════════════════════════════════════════════
_I18N = {}
for _lang in ['id','en']:
    with open(f'i18n/{_lang}.json', encoding='utf-8') as _f:
        _I18N[_lang] = json.load(_f)

_CURRENT_LANG = ['id']   # mutable list agar bisa diubah globally

def T(path, lang=None):
    """
    Lookup i18n key via dot notation.
    Contoh: T('home.iq_btn') → 'Mulai Tes IQ'
    """
    l = lang or _CURRENT_LANG[0]
    node = _I18N[l]
    for k in path.split('.'):
        if isinstance(node, dict): node = node.get(k, path)
        else: return path
    return node

def set_lang(lang):
    _CURRENT_LANG[0] = lang

def get_lang():
    return _CURRENT_LANG[0]

# ══════════════════════════════════════════════════════════════
# ENGINE IMPORTS — deferred, called inside functions only
# (importing at module level would run before QApplication)
# ══════════════════════════════════════════════════════════════
def _import_engine():
    global engine_score_to_iq, build_cognitive_profile
    global COGNITIVE_LEVEL_COLORS, COGNITIVE_LEVEL_ID
    global COGNITIVE_DESC_ID, COGNITIVE_DESC_EN
    global get_archetype, get_combined_profile
    global get_career_recommendations, get_learning_style
    global get_blind_spots, get_roadmap
    from engine.scoring import (
        score_to_iq as engine_score_to_iq,
        build_cognitive_profile,
        COGNITIVE_LEVEL_COLORS, COGNITIVE_LEVEL_ID,
        COGNITIVE_DESC_ID, COGNITIVE_DESC_EN,
    )
    from engine.expert_rules import (
        get_archetype, get_combined_profile,
        get_career_recommendations, get_learning_style,
        get_blind_spots, get_roadmap,
    )

# Placeholders so references don't break before _import_engine() is called
engine_score_to_iq = build_cognitive_profile = None
COGNITIVE_LEVEL_COLORS = COGNITIVE_LEVEL_ID = {}
COGNITIVE_DESC_ID = COGNITIVE_DESC_EN = {}
get_archetype = get_combined_profile = get_career_recommendations = None
get_learning_style = get_blind_spots = get_roadmap = None

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

GOLD      = '#f5a623'
GOLD_LIGHT= '#fff3dc'
GREEN     = '#27ae60'
RED       = '#e74c3c'
BLUE      = '#3b82f6'
PURPLE    = '#8b5cf6'
ORANGE    = '#f97316'

TRAITS       = ['O','C','E','A','N']
TRAIT_COLORS = {'O':'#f97316','C':'#3b82f6','E':'#8b5cf6','A':'#27ae60','N':'#e74c3c'}

CAT_COLORS = {
    'Deret Angka':    '#f97316',
    'Analogi Verbal': '#8b5cf6',
    'Logika':         '#3b82f6',
    'Numerik':        '#27ae60',
    'Pola Visual':    '#f5a623',
    # English keys
    'Number Series':  '#f97316',
    'Verbal Analogy': '#8b5cf6',
    'Logic':          '#3b82f6',
    'Numeric':        '#27ae60',
    'Visual Pattern': '#f5a623',
}

IQ_CATEGORIES_LIST = ['Deret Angka','Analogi Verbal','Logika','Numerik','Pola Visual']
IQ_CATEGORIES_EN   = ['Number Series','Verbal Analogy','Logic','Numeric','Visual Pattern']

def get_iq_categories():
    return IQ_CATEGORIES_LIST if get_lang()=='id' else IQ_CATEGORIES_EN

IQ_CATEGORY_TABLE = [
    (130,'Very Superior','#f5a623'),
    (120,'Superior','#27ae60'),
    (110,'High Average','#3b82f6'),
    (90, 'Average','#8b5cf6'),
    (80, 'Low Average','#f97316'),
    (70, 'Below Average','#e74c3c'),
    (0,  'Well Below Avg','#e74c3c'),
]

COG_NAMES_ID = {
    'fluid':'Penalaran Cair','crystallized':'Kecerdasan Verbal',
    'abstract':'Penalaran Abstrak','quantitative':'Penalaran Kuantitatif',
    'spatial':'Kecerdasan Spasial',
}
COG_NAMES_EN = {
    'fluid':'Fluid Reasoning','crystallized':'Verbal Intelligence',
    'abstract':'Abstract Reasoning','quantitative':'Quantitative Reasoning',
    'spatial':'Spatial Intelligence',
}
COG_COLORS = {
    'fluid':'#f97316','crystallized':'#8b5cf6',
    'abstract':'#3b82f6','quantitative':'#27ae60','spatial':'#f5a623',
}

# ══════════════════════════════════════════════════════════════
# QUESTION POOLS
# ══════════════════════════════════════════════════════════════
# Bilingual Big Five questions — (trait, {id: text, en: text}, reversed)
BF_QUESTION_POOL_BILINGUAL = [
    ('O',{'id':'Saya selalu ingin tahu tentang berbagai hal dan menikmati belajar hal baru.','en':'I am always curious about many things and enjoy learning new topics.'},False),
    ('O',{'id':'Saya suka berimajinasi dan memiliki kehidupan batin yang kaya.','en':'I enjoy daydreaming and have a rich inner life.'},False),
    ('O',{'id':'Saya lebih suka rutinitas yang sudah terbukti daripada mencoba cara baru.','en':'I prefer tried-and-true routines over trying new ways of doing things.'},True),
    ('O',{'id':'Saya mudah terpesona oleh seni, musik, atau karya kreatif.','en':'I am easily captivated by art, music, or creative works.'},False),
    ('O',{'id':'Saya tertarik pada topik-topik abstrak dan filosofis.','en':'I am drawn to abstract and philosophical topics.'},False),
    ('O',{'id':'Saya memiliki imajinasi yang vivid dan aktif.','en':'I have a vivid and active imagination.'},False),
    ('O',{'id':'Saya tidak terlalu tertarik pada seni atau sastra.','en':'I am not particularly interested in art or literature.'},True),
    ('O',{'id':'Saya menikmati memikirkan teori dan ide-ide yang kompleks.','en':'I enjoy thinking about theories and complex ideas.'},False),
    ('O',{'id':'Saya jarang mencari pengalaman baru atau tidak biasa.','en':'I rarely seek out new or unusual experiences.'},True),
    ('O',{'id':'Saya mudah menyadari keindahan dalam hal-hal di sekitar saya.','en':'I easily notice beauty in the things around me.'},False),
    ('C',{'id':'Saya selalu menyelesaikan tugas sesuai rencana yang telah saya buat.','en':'I always complete tasks according to the plans I have made.'},False),
    ('C',{'id':'Saya cenderung rapi dan terorganisir dalam keseharian.','en':'I tend to be neat and organized in my daily life.'},False),
    ('C',{'id':'Saya sering menunda-nunda pekerjaan yang harus diselesaikan.','en':'I often procrastinate on work that needs to be done.'},True),
    ('C',{'id':'Saya mempertimbangkan konsekuensi secara matang sebelum bertindak.','en':'I carefully consider consequences before taking action.'},False),
    ('C',{'id':'Saya bekerja keras untuk mencapai tujuan saya.','en':'I work hard to achieve my goals.'},False),
    ('C',{'id':'Saya membuat rencana dan mengikutinya dengan disiplin.','en':'I make plans and follow them with discipline.'},False),
    ('C',{'id':'Saya sering lupa menaruh barang-barang saya.','en':'I often forget where I put my belongings.'},True),
    ('C',{'id':'Saya sangat teliti dalam segala hal yang saya lakukan.','en':'I am very thorough in everything I do.'},False),
    ('C',{'id':'Saya kadang bertindak tanpa berpikir panjang terlebih dahulu.','en':'I sometimes act without thinking things through first.'},True),
    ('C',{'id':'Saya memastikan semua tugas selesai sebelum beristirahat.','en':'I make sure all tasks are done before I rest.'},False),
    ('E',{'id':'Saya merasa bersemangat dan penuh energi ketika berkumpul dengan banyak orang.','en':'I feel excited and full of energy when around a lot of people.'},False),
    ('E',{'id':'Saya mudah akrab dengan orang-orang yang baru saya temui.','en':'I easily get along with people I have just met.'},False),
    ('E',{'id':'Saya lebih suka menghabiskan waktu sendirian daripada di keramaian.','en':'I prefer spending time alone rather than in crowds.'},True),
    ('E',{'id':'Saya sering menjadi pusat perhatian dalam suatu kelompok.','en':'I often become the center of attention in a group.'},False),
    ('E',{'id':'Saya terasa hidup dan bersemangat ketika berada di lingkungan sosial.','en':'I feel alive and energized in social environments.'},False),
    ('E',{'id':'Saya mudah memulai percakapan dengan orang yang belum saya kenal.','en':'I easily start conversations with people I do not know yet.'},False),
    ('E',{'id':'Saya merasa lelah setelah terlalu banyak berinteraksi sosial.','en':'I feel drained after too much social interaction.'},True),
    ('E',{'id':'Saya menikmati menjadi bagian dari kelompok besar.','en':'I enjoy being part of a large group.'},False),
    ('E',{'id':'Saya lebih suka mendengarkan daripada berbicara dalam diskusi kelompok.','en':'I prefer listening rather than speaking in group discussions.'},True),
    ('E',{'id':'Saya merasa bersemangat dan antusias dalam situasi baru.','en':'I feel enthusiastic and eager in new situations.'},False),
    ('A',{'id':'Saya peduli dengan perasaan orang lain dan mudah berempati.','en':'I care about others\'s feelings and empathize easily.'},False),
    ('A',{'id':'Saya suka membantu orang lain meskipun tidak ada manfaat langsung bagi saya.','en':'I like helping others even when there is no direct benefit for me.'},False),
    ('A',{'id':'Saya kadang sulit mempercayai motivasi di balik tindakan orang lain.','en':'I sometimes find it hard to trust the motives behind other people\'s actions.'},True),
    ('A',{'id':'Saya menghindari konflik dan mencari jalan damai dalam perselisihan.','en':'I avoid conflict and look for peaceful solutions in disagreements.'},False),
    ('A',{'id':'Saya bersikap lemah lembut dan penuh perhatian kepada orang di sekitar saya.','en':'I am gentle and attentive to the people around me.'},False),
    ('A',{'id':'Saya percaya bahwa orang pada dasarnya memiliki niat baik.','en':'I believe that people are fundamentally well-intentioned.'},False),
    ('A',{'id':'Saya terkadang terasa dingin dan tidak peduli pada masalah orang lain.','en':'I sometimes come across as cold and indifferent to other people\'s problems.'},True),
    ('A',{'id':'Saya mudah memaafkan orang yang telah menyakiti saya.','en':'I easily forgive people who have hurt me.'},False),
    ('A',{'id':'Saya lebih mementingkan kepentingan diri sendiri dibanding orang lain.','en':'I prioritize my own interests over those of others.'},True),
    ('A',{'id':'Saya berusaha membuat orang lain merasa nyaman saat bersama saya.','en':'I try to make others feel comfortable when they are with me.'},False),
    ('N',{'id':'Saya sering merasa cemas atau khawatir tanpa alasan yang jelas.','en':'I often feel anxious or worried without a clear reason.'},False),
    ('N',{'id':'Suasana hati saya bisa berubah-ubah dengan cukup cepat.','en':'My mood can change quite quickly.'},False),
    ('N',{'id':'Saya cenderung tetap tenang bahkan dalam situasi yang menegangkan.','en':'I tend to stay calm even in tense situations.'},True),
    ('N',{'id':'Saya mudah merasa sedih atau tertekan.','en':'I easily feel sad or depressed.'},False),
    ('N',{'id':'Saya sering merasa tidak yakin dengan keputusan yang saya buat.','en':'I often feel uncertain about the decisions I make.'},False),
    ('N',{'id':'Saya mudah merasa frustrasi atau kesal saat segala sesuatu tidak berjalan lancar.','en':'I easily feel frustrated or irritated when things do not go smoothly.'},False),
    ('N',{'id':'Saya jarang merasa sedih atau murung.','en':'I rarely feel sad or gloomy.'},True),
    ('N',{'id':'Saya sering merasa tertekan oleh tuntutan kehidupan sehari-hari.','en':'I often feel overwhelmed by the demands of daily life.'},False),
    ('N',{'id':'Saya relatif stabil secara emosional dan tidak mudah terguncang.','en':'I am relatively emotionally stable and not easily rattled.'},True),
    ('N',{'id':'Saya kadang merasa hidup saya tidak terkendali.','en':'I sometimes feel like my life is out of control.'},False),
]

def get_bf_pool(lang=None):
    """Return BF pool as (trait, text, reversed) for current language."""
    l = lang or get_lang()
    return [(t, d[l], r) for t, d, r in BF_QUESTION_POOL_BILINGUAL]

# Keep compatibility alias
BF_QUESTION_POOL = get_bf_pool('id')

# Bilingual IQ questions — category key stays consistent, q/opts/explanation localized
IQ_QUESTION_POOL_BILINGUAL = [
    # ── Deret Angka / Number Series ──
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':1,
     'q_id':'Lanjutkan deret berikut:\n2, 4, 6, 8, __',
     'q_en':'Continue the series:\n2, 4, 6, 8, __',
     'opts':['9','10','12','14'],'ans':1,
     'exp_id':'Deret aritmetika +2. Setelah 8 adalah 10.',
     'exp_en':'Arithmetic series +2. After 8 comes 10.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':2,
     'q_id':'Lanjutkan deret berikut:\n1, 4, 9, 16, 25, __',
     'q_en':'Continue the series:\n1, 4, 9, 16, 25, __',
     'opts':['30','36','34','32'],'ans':1,
     'exp_id':'Deret kuadrat sempurna: 1²,2²,3²,4²,5²,6²=36.',
     'exp_en':'Perfect squares: 1²,2²,3²,4²,5²,6²=36.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':3,
     'q_id':'Lanjutkan deret berikut:\n2, 4, 8, 16, __',
     'q_en':'Continue the series:\n2, 4, 8, 16, __',
     'opts':['24','32','28','30'],'ans':1,
     'exp_id':'Deret geometri ×2. 16×2=32.',
     'exp_en':'Geometric series ×2. 16×2=32.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':3,
     'q_id':'Lanjutkan deret berikut:\n1, 1, 2, 3, 5, 8, __',
     'q_en':'Continue the series:\n1, 1, 2, 3, 5, 8, __',
     'opts':['11','12','13','14'],'ans':2,
     'exp_id':'Fibonacci: setiap suku = jumlah dua sebelumnya. 5+8=13.',
     'exp_en':'Fibonacci: each term = sum of the two before it. 5+8=13.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':4,
     'q_id':'Lanjutkan deret berikut:\n3, 6, 11, 18, 27, __',
     'q_en':'Continue the series:\n3, 6, 11, 18, 27, __',
     'opts':['36','38','40','35'],'ans':1,
     'exp_id':'Selisih: +3,+5,+7,+9,+11. Jadi 27+11=38.',
     'exp_en':'Differences: +3,+5,+7,+9,+11. So 27+11=38.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':5,
     'q_id':'Lanjutkan deret berikut:\n2, 6, 12, 20, 30, __',
     'q_en':'Continue the series:\n2, 6, 12, 20, 30, __',
     'opts':['40','42','44','45'],'ans':1,
     'exp_id':'Pola: n×(n+1). Suku ke-6: 6×7=42.',
     'exp_en':'Pattern: n×(n+1). 6th term: 6×7=42.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':6,
     'q_id':'Lanjutkan deret berikut:\n1, 3, 7, 13, 21, 31, __',
     'q_en':'Continue the series:\n1, 3, 7, 13, 21, 31, __',
     'opts':['40','41','43','45'],'ans':2,
     'exp_id':'Selisih +2,+4,+6,+8,+10,+12. Jadi 31+12=43.',
     'exp_en':'Differences +2,+4,+6,+8,+10,+12. So 31+12=43.'},
    {'cat_id':'Deret Angka','cat_en':'Number Series','difficulty':7,
     'q_id':'Lanjutkan deret berikut:\n2, 3, 5, 8, 13, 21, __',
     'q_en':'Continue the series:\n2, 3, 5, 8, 13, 21, __',
     'opts':['32','33','34','35'],'ans':2,
     'exp_id':'Fibonacci-like: 13+21=34.',
     'exp_en':'Fibonacci-like: 13+21=34.'},
    # ── Analogi Verbal / Verbal Analogy ──
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':1,
     'q_id':'Panas adalah lawan dari dingin.\nTerang adalah lawan dari __',
     'q_en':'Hot is the opposite of cold.\nBright is the opposite of __',
     'opts_id':['Siang','Gelap','Malam','Redup'],
     'opts_en':['Daytime','Dark','Night','Dim'],'ans':1,
     'exp_id':'Lawan dari terang adalah gelap (antonim langsung).',
     'exp_en':'The opposite of bright is dark (direct antonym).'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':2,
     'q_id':'Dokter : Rumah Sakit = Guru : __',
     'q_en':'Doctor : Hospital = Teacher : __',
     'opts_id':['Kantor','Perpustakaan','Sekolah','Studio'],
     'opts_en':['Office','Library','School','Studio'],'ans':2,
     'exp_id':'Dokter bekerja di RS, Guru bekerja di Sekolah.',
     'exp_en':'A Doctor works at a Hospital, a Teacher works at a School.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':2,
     'q_id':'Burung : Terbang = Ikan : __',
     'q_en':'Bird : Fly = Fish : __',
     'opts_id':['Berlari','Berenang','Melompat','Merayap'],
     'opts_en':['Run','Swim','Jump','Crawl'],'ans':1,
     'exp_id':'Burung terbang, ikan berenang.',
     'exp_en':'Birds fly, fish swim.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':3,
     'q_id':'Buku : Perpustakaan = Lukisan : __',
     'q_en':'Book : Library = Painting : __',
     'opts_id':['Toko','Museum','Galeri','Gudang'],
     'opts_en':['Shop','Museum','Gallery','Warehouse'],'ans':2,
     'exp_id':'Buku di Perpustakaan, Lukisan di Galeri.',
     'exp_en':'Books are in Libraries, Paintings are in Galleries.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':4,
     'q_id':'Penulis : Novel = Komposer : __',
     'q_en':'Writer : Novel = Composer : __',
     'opts_id':['Buku','Simfoni','Lukisan','Film'],
     'opts_en':['Book','Symphony','Painting','Film'],'ans':1,
     'exp_id':'Penulis → Novel, Komposer → Simfoni.',
     'exp_en':'Writer → Novel, Composer → Symphony.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':5,
     'q_id':'Roti : Tepung = Kain : __',
     'q_en':'Bread : Flour = Fabric : __',
     'opts_id':['Baju','Benang','Kapas','Jarum'],
     'opts_en':['Shirt','Thread','Cotton','Needle'],'ans':1,
     'exp_id':'Roti dibuat dari Tepung, Kain dari Benang.',
     'exp_en':'Bread is made from Flour, Fabric from Thread.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':6,
     'q_id':'Desibel : Suara = Richter : __',
     'q_en':'Decibel : Sound = Richter : __',
     'opts_id':['Angin','Gempa bumi','Tekanan','Cahaya'],
     'opts_en':['Wind','Earthquake','Pressure','Light'],'ans':1,
     'exp_id':'Desibel mengukur Suara, Richter mengukur Gempa.',
     'exp_en':'Decibels measure Sound, Richter measures Earthquakes.'},
    {'cat_id':'Analogi Verbal','cat_en':'Verbal Analogy','difficulty':7,
     'q_id':'Anemia : Darah = Osteoporosis : __',
     'q_en':'Anemia : Blood = Osteoporosis : __',
     'opts_id':['Otot','Kulit','Tulang','Saraf'],
     'opts_en':['Muscle','Skin','Bone','Nerve'],'ans':2,
     'exp_id':'Anemia memengaruhi Darah, Osteoporosis memengaruhi Tulang.',
     'exp_en':'Anemia affects Blood, Osteoporosis affects Bone.'},
    # ── Logika / Logic ──
    {'cat_id':'Logika','cat_en':'Logic','difficulty':1,
     'q_id':'Semua kucing adalah hewan.\nBeberapa hewan adalah predator.\nKesimpulan yang PASTI benar:',
     'q_en':'All cats are animals.\nSome animals are predators.\nWhich conclusion is DEFINITELY true?',
     'opts_id':['Semua kucing adalah predator','Beberapa kucing mungkin adalah predator','Tidak ada kucing yang predator','Semua predator adalah kucing'],
     'opts_en':['All cats are predators','Some cats might be predators','No cats are predators','All predators are cats'],'ans':1,
     'exp_id':'"Beberapa hewan predator" tidak menentukan apakah kucing termasuk, sehingga hanya "mungkin" yang valid.',
     'exp_en':'"Some animals are predators" does not determine if cats are included, so only "might be" is valid.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':2,
     'q_id':'Jika hari hujan, maka jalanan basah.\nJalanan tidak basah. Kesimpulan:',
     'q_en':'If it rains, the road is wet.\nThe road is not wet. Conclusion:',
     'opts_id':['Hari hujan','Hari tidak hujan','Jalanan kering karena angin','Tidak dapat disimpulkan'],
     'opts_en':['It is raining','It is not raining','The road is dry due to wind','Cannot be concluded'],'ans':1,
     'exp_id':'Modus tollens: jika P→Q dan bukan Q, maka bukan P.',
     'exp_en':'Modus tollens: if P→Q and not Q, then not P.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':2,
     'q_id':'A lebih tua dari B. B lebih tua dari C. D lebih muda dari C.\nSiapa yang paling tua?',
     'q_en':'A is older than B. B is older than C. D is younger than C.\nWho is the oldest?',
     'opts_id':['B','C','A','D'],
     'opts_en':['B','C','A','D'],'ans':2,
     'exp_id':'Urutan: A>B>C>D. Jadi A paling tua.',
     'exp_en':'Order: A>B>C>D. So A is the oldest.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':3,
     'q_id':'Dalam 5 hari ke depan, Andi berolahraga setiap hari ganjil (hari ke-1,3,5).\nBerapa total hari ia berolahraga?',
     'q_en':'Over the next 5 days, Andi exercises on every odd day (day 1,3,5).\nHow many days does he exercise in total?',
     'opts_id':['2 hari','3 hari','4 hari','5 hari'],
     'opts_en':['2 days','3 days','4 days','5 days'],'ans':1,
     'exp_id':'Hari ganjil dari 1-5: hari ke-1,3,5 = 3 hari.',
     'exp_en':'Odd days from 1-5: days 1,3,5 = 3 days.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':4,
     'q_id':'Semua manajer adalah karyawan.\nBeberapa karyawan adalah perempuan.\nKesimpulan yang PASTI benar:',
     'q_en':'All managers are employees.\nSome employees are women.\nWhich conclusion is DEFINITELY true?',
     'opts_id':['Semua manajer adalah perempuan','Beberapa manajer adalah perempuan','Tidak ada manajer yang perempuan','Beberapa karyawan adalah manajer'],
     'opts_en':['All managers are women','Some managers are women','No managers are women','Some employees are managers'],'ans':3,
     'exp_id':'Karena semua manajer adalah karyawan, beberapa karyawan (para manajer) adalah manajer.',
     'exp_en':'Since all managers are employees, some employees (the managers) are managers.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':5,
     'q_id':'Jika semua A adalah B, dan tidak ada B yang C,\nmaka kesimpulan yang benar:',
     'q_en':'If all A are B, and no B are C,\nthen the correct conclusion is:',
     'opts_id':['Beberapa A adalah C','Tidak ada A yang C','Semua C adalah A','Beberapa B adalah A'],
     'opts_en':['Some A are C','No A are C','All C are A','Some B are A'],'ans':1,
     'exp_id':'Semua A adalah B, dan tidak ada B yang C → tidak ada A yang C.',
     'exp_en':'All A are B, and no B are C → no A are C.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':6,
     'q_id':'Dua kereta berangkat menuju satu sama lain.\nJarak 600 km, kecepatan 100 km/jam dan 50 km/jam.\nBerapa jam sampai bertemu?',
     'q_en':'Two trains head toward each other.\nDistance 600 km, speeds 100 km/h and 50 km/h.\nHow many hours until they meet?',
     'opts_id':['3 jam','4 jam','5 jam','6 jam'],
     'opts_en':['3 hours','4 hours','5 hours','6 hours'],'ans':1,
     'exp_id':'Kecepatan gabungan=150 km/jam. 600/150=4 jam.',
     'exp_en':'Combined speed=150 km/h. 600/150=4 hours.'},
    {'cat_id':'Logika','cat_en':'Logic','difficulty':7,
     'q_id':'5 orang duduk berurutan. A di kiri B. C di antara D dan E.\nD paling kiri. Siapa di posisi tengah (ke-3)?',
     'q_en':'5 people sit in a row. A is to the left of B. C is between D and E.\nD is leftmost. Who sits in the middle (position 3)?',
     'opts_id':['A','B','E','C'],
     'opts_en':['A','B','E','C'],'ans':2,
     'exp_id':'Urutan: D,C,E,A,B. Posisi ke-3 = E.',
     'exp_en':'Order: D,C,E,A,B. Position 3 = E.'},
    # ── Numerik / Numeric ──
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':1,
     'q_id':'Berapa nilai dari 15 × 4?',
     'q_en':'What is the value of 15 × 4?',
     'opts':['50','55','60','65'],'ans':2,
     'exp_id':'15 × 4 = 60.',
     'exp_en':'15 × 4 = 60.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':2,
     'q_id':'Sebuah persegi memiliki keliling 36 cm. Berapa luasnya?',
     'q_en':'A square has a perimeter of 36 cm. What is its area?',
     'opts':['72 cm²','81 cm²','64 cm²','49 cm²'],'ans':1,
     'exp_id':'Sisi=36/4=9. Luas=9×9=81 cm².',
     'exp_en':'Side=36/4=9. Area=9×9=81 cm².'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':2,
     'q_id':'Jika 20% dari X adalah 50, maka X adalah __',
     'q_en':'If 20% of X is 50, then X is __',
     'opts':['200','250','300','150'],'ans':1,
     'exp_id':'20% × X = 50 → X = 50/0.2 = 250.',
     'exp_en':'20% × X = 50 → X = 50/0.2 = 250.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':3,
     'q_id':'Sebuah kereta menempuh 300 km dalam 4 jam.\nBerapa kecepatan rata-ratanya?',
     'q_en':'A train travels 300 km in 4 hours.\nWhat is its average speed?',
     'opts_id':['65 km/jam','70 km/jam','75 km/jam','80 km/jam'],
     'opts_en':['65 km/h','70 km/h','75 km/h','80 km/h'],'ans':2,
     'exp_id':'Kecepatan = 300/4 = 75 km/jam.',
     'exp_en':'Speed = 300/4 = 75 km/h.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':4,
     'q_id':'Sebuah toko memberi diskon 30%. Harga asli Rp200.000.\nBerapa harga setelah diskon?',
     'q_en':'A store gives a 30% discount. Original price Rp200,000.\nWhat is the price after discount?',
     'opts':['Rp130.000','Rp140.000','Rp150.000','Rp160.000'],'ans':1,
     'exp_id':'Diskon=30%×200.000=60.000. Harga=200.000-60.000=140.000.',
     'exp_en':'Discount=30%×200,000=60,000. Price=200,000-60,000=140,000.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':5,
     'q_id':'Rasio pria:wanita dalam kelas adalah 3:2, total 40 siswa.\nBerapa jumlah wanita?',
     'q_en':'The male:female ratio in a class is 3:2, with 40 students total.\nHow many are female?',
     'opts':['14','16','18','20'],'ans':1,
     'exp_id':'Wanita = 2/5 × 40 = 16.',
     'exp_en':'Female = 2/5 × 40 = 16.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':6,
     'q_id':'Angka mana yang merupakan bilangan prima?',
     'q_en':'Which number is a prime number?',
     'opts':['51','57','59','63'],'ans':2,
     'exp_id':'51=3×17, 57=3×19, 63=7×9. Hanya 59 yang prima.',
     'exp_en':'51=3×17, 57=3×19, 63=7×9. Only 59 is prime.'},
    {'cat_id':'Numerik','cat_en':'Numeric','difficulty':7,
     'q_id':'Pipa mengisi kolam dalam 6 jam.\nPipa lain menguras dalam 9 jam.\nJika keduanya aktif, berapa jam kolam penuh?',
     'q_en':'A pipe fills a pool in 6 hours.\nAnother pipe drains it in 9 hours.\nIf both are active, how many hours to fill the pool?',
     'opts_id':['14 jam','16 jam','18 jam','20 jam'],
     'opts_en':['14 hours','16 hours','18 hours','20 hours'],'ans':2,
     'exp_id':'Net per jam: 1/6-1/9=1/18. Total=18 jam.',
     'exp_en':'Net per hour: 1/6-1/9=1/18. Total=18 hours.'},
    # ── Pola Visual / Visual Pattern ──
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':1,
     'q_id':'Jika segitiga=3 sisi, segiempat=4 sisi, pentagon=5 sisi,\nmaka oktagon memiliki berapa sisi?',
     'q_en':'If triangle=3 sides, quadrilateral=4 sides, pentagon=5 sides,\nhow many sides does an octagon have?',
     'opts':['6','7','8','9'],'ans':2,
     'exp_id':'Oktagon (octa=8) memiliki 8 sisi.',
     'exp_en':'Octagon (octa=8) has 8 sides.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':2,
     'q_id':'Sebuah jam menunjukkan pukul 3:00.\nBerapa derajat sudut antara jarum jam dan jarum menit?',
     'q_en':'A clock shows 3:00.\nWhat is the angle between the hour and minute hands?',
     'opts_id':['60 derajat','75 derajat','90 derajat','120 derajat'],
     'opts_en':['60 degrees','75 degrees','90 degrees','120 degrees'],'ans':2,
     'exp_id':'Pukul 3:00, jarum jam di angka 3 = 90 derajat dari angka 12.',
     'exp_en':'At 3:00, the hour hand is at 3 = 90 degrees from 12.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':2,
     'q_id':'Dalam pola: Lingkaran putih, Hitam, Putih,Putih, Hitam, Putih,Putih,Putih, Hitam\nBerapa lingkaran putih sebelum hitam berikutnya?',
     'q_en':'In the pattern: White circle, Black, White,White, Black, White,White,White, Black\nHow many white circles before the next black?',
     'opts':['3','4','5','6'],'ans':1,
     'exp_id':'Pola jumlah putih sebelum hitam: 1,2,3,4... Berikutnya ada 4.',
     'exp_en':'Pattern of whites before black: 1,2,3,4... Next is 4.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':3,
     'q_id':'Pola angka dalam magic square 3x3:\n2  7  6\n9  5  1\n4  3  ?\nBerapa nilai "?"',
     'q_en':'Number pattern in a 3x3 magic square:\n2  7  6\n9  5  1\n4  3  ?\nWhat is "?"',
     'opts':['7','8','9','6'],'ans':1,
     'exp_id':'Magic square: setiap baris/kolom berjumlah 15. Kolom kanan: 6+1+?=15 → ?=8.',
     'exp_en':'Magic square: every row/column sums to 15. Right column: 6+1+?=15 → ?=8.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':4,
     'q_id':'Sebuah kubus dipotong menjadi 27 kubus kecil (3x3x3).\nBerapa kubus kecil yang tidak memiliki sisi terekspos?',
     'q_en':'A cube is cut into 27 small cubes (3x3x3).\nHow many small cubes have no exposed face?',
     'opts':['0','1','2','3'],'ans':1,
     'exp_id':'Hanya 1 kubus di tengah yang tidak terekspos di sisi manapun.',
     'exp_en':'Only 1 cube at the center has no exposed face on any side.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':5,
     'q_id':'Urutan bentuk:\nSegitiga, Kotak, Segitiga-Segitiga, Kotak-Kotak, Segitiga x3, Kotak x3, __',
     'q_en':'Shape sequence:\nTriangle, Square, Triangle-Triangle, Square-Square, Triangle x3, Square x3, __',
     'opts_id':['Segitiga x4','Kotak x4','Segitiga-Kotak','Kotak-Segitiga'],
     'opts_en':['Triangle x4','Square x4','Triangle-Square','Square-Triangle'],'ans':1,
     'exp_id':'Pola bergantian segitiga-kotak bertambah 1. Setelah Kotak x3 adalah Segitiga x4.',
     'exp_en':'Alternating triangle-square pattern grows by 1. After Square x3 comes Triangle x4.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':6,
     'q_id':'Persegi panjang 8x6 dibagi menjadi persegi-persegi kecil 2x2.\nBerapa banyak persegi kecil?',
     'q_en':'An 8x6 rectangle is divided into 2x2 small squares.\nHow many small squares are there?',
     'opts':['10','12','14','16'],'ans':1,
     'exp_id':'Horizontal: 8/2=4, Vertikal: 6/2=3. Total=4x3=12.',
     'exp_en':'Horizontal: 8/2=4, Vertical: 6/2=3. Total=4×3=12.'},
    {'cat_id':'Pola Visual','cat_en':'Visual Pattern','difficulty':7,
     'q_id':'Bayangan cermin dari "3 6 9" adalah __',
     'q_en':'The mirror image of "3 6 9" is __',
     'opts':['9 6 3','6 9 3','3 9 6','E 9 E'],'ans':0,
     'exp_id':'Bayangan cermin membalik urutan: "3 6 9" menjadi "9 6 3".',
     'exp_en':'A mirror image reverses order: "3 6 9" becomes "9 6 3".'},
]

def _localize_iq_q(q, lang):
    """Convert bilingual IQ question dict ke format lama untuk lang tertentu."""
    l = lang or get_lang()
    cat  = q['cat_id'] if l == 'id' else q['cat_en']
    text = q['q_id']   if l == 'id' else q['q_en']
    exp  = q['exp_id'] if l == 'id' else q['exp_en']
    # opts: cek apakah ada opts_id/opts_en atau shared opts
    if f'opts_{l}' in q:
        opts = q[f'opts_{l}']
    else:
        opts = q.get('opts', [])
    return {'category': cat, 'difficulty': q['difficulty'],
            'q': text, 'opts': opts, 'ans': q['ans'], 'explanation': exp}

def get_iq_pool(lang=None):
    """Return IQ pool dalam bahasa yang dipilih."""
    l = lang or get_lang()
    return [_localize_iq_q(q, l) for q in IQ_QUESTION_POOL_BILINGUAL]

# Alias kompatibilitas
IQ_QUESTION_POOL = get_iq_pool('id')

def _rebuild_iq_pool_by_cat(lang=None):
    pool = get_iq_pool(lang)
    cats_id  = ['Deret Angka','Analogi Verbal','Logika','Numerik','Pola Visual']
    cats_en  = ['Number Series','Verbal Analogy','Logic','Numeric','Visual Pattern']
    cats = cats_id if (lang or get_lang()) == 'id' else cats_en
    return {cat: sorted([q for q in pool if q['category']==cat],
                        key=lambda x: x['difficulty'])
            for cat in cats}

IQ_POOL_BY_CAT = _rebuild_iq_pool_by_cat('id')

# ══════════════════════════════════════════════════════════════
# SESSION HELPERS
# ══════════════════════════════════════════════════════════════
def make_iq_session():
    pool_by_cat = _rebuild_iq_pool_by_cat()   # pakai bahasa aktif saat ini
    session = []
    for cat in pool_by_cat:
        pool = pool_by_cat[cat][:]
        random.shuffle(pool)
        picked = sorted(pool[:8], key=lambda q: q['difficulty'])
        session.extend(picked)
    return session

def make_bf_session():
    bf_pool = get_bf_pool()   # pakai bahasa aktif saat ini
    by_trait = {t: [q for q in bf_pool if q[0]==t] for t in TRAITS}
    session = []
    for t in TRAITS:
        random.shuffle(by_trait[t])
        session.extend(by_trait[t])
    random.shuffle(session)
    return session

def compute_bf_scores(answers, session):
    raw={t:0 for t in TRAITS}; cnt={t:0 for t in TRAITS}
    for i,(trait,_,reverse) in enumerate(session):
        a=answers[i]
        if a is None: continue
        v=(6-a) if reverse else a
        raw[trait]+=v; cnt[trait]+=1
    return {t: round((raw[t]/(cnt[t]*5))*100) if cnt[t]>0 else 50 for t in TRAITS}

def get_percentile_bf(trait, score):
    return NORMS[trait].get(str(min(100,max(0,round(score)))), 50.0)

def run_full_analysis(iq_answers, iq_session, bf_scores):
    """Jalankan semua layer engine dan return dict lengkap."""
    lang = get_lang()
    iq_result  = engine_score_to_iq(iq_answers, iq_session)
    cognitive  = build_cognitive_profile(iq_answers, iq_session)
    iq         = iq_result['iq']
    archetype  = get_archetype(bf_scores, lang)
    combined   = get_combined_profile(iq, bf_scores, lang)
    careers    = get_career_recommendations(iq, bf_scores, lang, top_n=5)
    style_name, style_detail = get_learning_style(bf_scores, cognitive, lang)
    blind_spots = get_blind_spots(iq, bf_scores, lang)
    roadmap    = get_roadmap(iq, bf_scores, cognitive, careers, lang)
    pcts       = {t: get_percentile_bf(t, bf_scores[t]) for t in TRAITS}
    return {
        **iq_result,
        'cognitive': cognitive,
        'archetype': archetype,
        'combined':  combined,
        'careers':   careers,
        'learning_style_name':   style_name,
        'learning_style_detail': style_detail,
        'blind_spots': blind_spots,
        'roadmap':   roadmap,
        'bf_scores': bf_scores,
        'bf_pcts':   pcts,
        'lang':      lang,
        'n_bf_pop':  NORMS_DATA.get('n_population', 874434),
    }

# ══════════════════════════════════════════════════════════════
# LANGUAGE CHANGE SIGNAL — broadcast ke semua page
# ══════════════════════════════════════════════════════════════
class LangBus(QWidget):
    changed = pyqtSignal(str)

LANG_BUS = None   # dibuat setelah QApplication — lihat _init_lang_bus()

def _init_lang_bus():
    global LANG_BUS
    if LANG_BUS is None:
        LANG_BUS = LangBus()

# ══════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════
class AnimatedBar(QWidget):
    def __init__(self, color, pop_pct=0, parent=None):
        super().__init__(parent)
        self.color=QColor(color); self.pop_pct=pop_pct
        self._value=0; self.setFixedHeight(8); self.setMinimumWidth(200)

    def get_value(self): return self._value
    def set_value(self,v): self._value=v; self.update()
    value=pyqtProperty(float,get_value,set_value)

    def animate_to(self,target):
        self.anim=QPropertyAnimation(self,b'value')
        self.anim.setDuration(900); self.anim.setStartValue(0.0)
        self.anim.setEndValue(float(target)); self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        p.setBrush(QColor(L_BORDER)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0,0,w,h,h//2,h//2)
        fw=int(w*self._value/100)
        if fw>0:
            p.setBrush(self.color); p.drawRoundedRect(0,0,fw,h,h//2,h//2)
        if self.pop_pct>0:
            mx=int(w*self.pop_pct/100)
            p.setPen(QPen(QColor(150,150,150,180),2)); p.drawLine(mx,-2,mx,h+2)
        p.end()

class ProgressBar(QWidget):
    def __init__(self, color=GOLD):
        super().__init__()
        self._v=0; self.color=color; self.setFixedHeight(4)

    def set_value(self,v): self._v=v; self.update()

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w=self.width()
        p.setBrush(QColor(L_BORDER)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0,0,w,4,2,2)
        fw=int(w*self._v/100)
        if fw>0:
            grad=QLinearGradient(0,0,fw,0)
            grad.setColorAt(0,QColor(self.color))
            grad.setColorAt(1,QColor(self.color).lighter(120))
            p.setBrush(grad); p.drawRoundedRect(0,0,fw,4,2,2)
        p.end()

class CountdownTimer(QWidget):
    time_up = pyqtSignal()
    def __init__(self, total_seconds=1200, parent=None):
        super().__init__(parent)
        self.total=total_seconds; self.remain=total_seconds
        self.running=False; self.setFixedSize(80,80)
        self._timer=QTimer(self); self._timer.timeout.connect(self._tick)

    def start(self):
        self.remain=self.total; self.running=True
        self._timer.start(1000); self.update()

    def stop(self):
        self.running=False; self._timer.stop()

    def _tick(self):
        self.remain-=1; self.update()
        if self.remain<=0: self.stop(); self.time_up.emit()

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w=self.width(); cx,cy,R=w//2,w//2,w//2-6
        p.setPen(QPen(QColor(L_BORDER),5)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-R,cy-R,R*2,R*2)
        pct=self.remain/self.total
        urgent=self.remain<=120
        arc_color=QColor(RED) if urgent else QColor(BLUE)
        p.setPen(QPen(arc_color,5,Qt.SolidLine,Qt.RoundCap))
        p.drawArc(cx-R,cy-R,R*2,R*2,90*16,int(pct*360*16))
        mins=self.remain//60; secs=self.remain%60
        p.setPen(arc_color if urgent else QColor(L_TEXT))
        p.setFont(QFont('Segoe UI',11,QFont.Bold))
        p.drawText(0,0,w,w,Qt.AlignCenter,f'{mins:02d}:{secs:02d}')
        p.end()

class RadarWidget(QWidget):
    def __init__(self, scores, pop_stats, parent=None):
        super().__init__(parent)
        self.scores=scores; self.pop_stats=pop_stats
        self.setFixedSize(280,280); self.setStyleSheet('background:transparent;')

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        cx,cy,R=140,140,105; keys=['O','C','E','A','N']; n=len(keys)
        angles=[(math.pi*2*i/n)-math.pi/2 for i in range(n)]
        for g in range(1,6):
            r=R*g/5; pts=[(int(cx+r*math.cos(a)),int(cy+r*math.sin(a))) for a in angles]
            p.setPen(QPen(QColor(200,205,220,160),1)); p.setBrush(Qt.NoBrush)
            for i in range(n): p.drawLine(pts[i][0],pts[i][1],pts[(i+1)%n][0],pts[(i+1)%n][1])
        p.setPen(QPen(QColor(200,205,220,120),1))
        for a in angles: p.drawLine(cx,cy,int(cx+R*math.cos(a)),int(cy+R*math.sin(a)))
        pop_pts=[QPoint(int(cx+(R*self.pop_stats[k]['mean']/100)*math.cos(angles[i])),
                        int(cy+(R*self.pop_stats[k]['mean']/100)*math.sin(angles[i])))
                 for i,k in enumerate(keys)]
        p.setPen(QPen(QColor(150,155,170,120),1,Qt.DashLine))
        p.setBrush(QColor(150,155,170,20)); p.drawPolygon(QPolygon(pop_pts))
        user_pts=[QPoint(int(cx+(R*self.scores[k]/100)*math.cos(angles[i])),
                         int(cy+(R*self.scores[k]/100)*math.sin(angles[i])))
                  for i,k in enumerate(keys)]
        p.setPen(QPen(QColor(GOLD),2)); p.setBrush(QColor(245,166,35,50))
        p.drawPolygon(QPolygon(user_pts))
        for i,k in enumerate(keys):
            x,y=user_pts[i].x(),user_pts[i].y()
            p.setBrush(QColor(TRAIT_COLORS[k])); p.setPen(Qt.NoPen)
            p.drawEllipse(x-5,y-5,10,10)
        p.setFont(QFont('Segoe UI',8,QFont.Bold))
        for i,k in enumerate(keys):
            r=R+18; lx=int(cx+r*math.cos(angles[i])); ly=int(cy+r*math.sin(angles[i]))
            p.setPen(QColor(TRAIT_COLORS[k]))
            p.drawText(lx-18,ly-8,36,20,Qt.AlignCenter,f"{k} {self.scores[k]}")
        p.end()

class AccordionItem(QWidget):
    def __init__(self, number, question, user_ans, correct_ans, parent=None):
        super().__init__(parent)
        self.expanded=False
        is_correct=(user_ans==correct_ans)
        self.setStyleSheet('background:transparent;')
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,4); outer.setSpacing(0)
        self._header=QFrame()
        self._header.setStyleSheet(f'background:{L_BG};border:1px solid {L_BORDER};border-radius:8px;')
        hl=QHBoxLayout(self._header); hl.setContentsMargins(12,8,12,8)
        num=QLabel(f'{number}'); num.setStyleSheet(f'color:{L_MUTED};font-size:11px;min-width:22px;')
        short_q=question['q'].replace('\n',' ')
        if len(short_q)>62: short_q=short_q[:59]+'…'
        ql=QLabel(short_q); ql.setStyleSheet(f'color:{L_TEXT};font-size:12px;'); ql.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
        cat_c=CAT_COLORS.get(question['category'],GOLD)
        cl=QLabel(question['category']); cl.setStyleSheet(f'color:{cat_c};font-size:9px;border:1px solid {cat_c};padding:1px 6px;border-radius:3px;')
        status_color=GREEN if is_correct else RED
        sl=QLabel('✓' if is_correct else '✗'); sl.setStyleSheet(f'color:{status_color};font-size:13px;font-weight:700;min-width:18px;'); sl.setAlignment(Qt.AlignCenter)
        self._arrow=QLabel('▶'); self._arrow.setStyleSheet(f'color:{L_MUTED};font-size:9px;')
        hl.addWidget(num); hl.addWidget(ql); hl.addWidget(cl); hl.addWidget(sl); hl.addWidget(self._arrow)
        self._header.mousePressEvent=lambda _: self._toggle()
        outer.addWidget(self._header)
        self._body=QFrame()
        self._body.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-top:none;border-radius:0 0 8px 8px;')
        bl=QVBoxLayout(self._body); bl.setContentsMargins(14,10,14,10); bl.setSpacing(6)
        fq=QLabel(question['q']); fq.setWordWrap(True)
        fq.setStyleSheet(f'color:{L_TEXT};font-size:13px;font-weight:500;')
        bl.addWidget(fq)
        for i,opt in enumerate(question['opts']):
            if i==correct_ans and i==user_ans: bg,fg,sfx=f'rgba(39,174,96,0.08)',GREEN,' ✓ Jawabanmu & Benar'
            elif i==correct_ans:               bg,fg,sfx=f'rgba(39,174,96,0.06)',GREEN,' ← Jawaban benar'
            elif i==user_ans:                  bg,fg,sfx=f'rgba(231,76,60,0.08)',RED,' ✗ Jawabanmu'
            else:                              bg,fg,sfx='transparent',L_MUTED,''
            ol=QLabel(f'{chr(65+i)}. {opt}{sfx}'); ol.setWordWrap(True)
            ol.setStyleSheet(f'color:{fg};font-size:12px;background:{bg};padding:3px 8px;border-radius:4px;')
            bl.addWidget(ol)
        if 'explanation' in question:
            el=QLabel(f'💡  {question["explanation"]}'); el.setWordWrap(True)
            el.setStyleSheet(f'color:{GOLD};font-size:11px;background:{GOLD_LIGHT};padding:6px 10px;border-radius:6px;')
            bl.addWidget(el)
        self._body.setVisible(False); outer.addWidget(self._body)

    def _toggle(self):
        self.expanded=not self.expanded; self._body.setVisible(self.expanded)
        self._arrow.setText('▼' if self.expanded else '▶')
        self._header.setStyleSheet(f'background:{"#eef0f8" if self.expanded else L_BG};border:1px solid {L_BORDER};border-radius:{"8px 8px 0 0" if self.expanded else "8px"};')

# ══════════════════════════════════════════════════════════════
# SHARED UI HELPERS
# ══════════════════════════════════════════════════════════════
def lcard(title=''):
    f=QFrame(); f.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:12px;')
    l=QVBoxLayout(f); l.setContentsMargins(20,16,20,16)
    if title:
        h=QLabel(title.upper()); h.setStyleSheet(f'color:{L_MUTED};font-size:9px;font-weight:700;letter-spacing:2px;background:transparent;')
        l.addWidget(h)
    return f

def dark_btn(text,w=160,h=40):
    b=QPushButton(text); b.setFixedSize(w,h)
    b.setStyleSheet(f'QPushButton{{background:{D_BG};color:{D_TEXT};border:1px solid {D_BORDER};border-radius:6px;font-size:13px;font-weight:600;}} QPushButton:hover{{background:{D_BG2};}}')
    return b

def gold_btn(text,w=180,h=42):
    b=QPushButton(text); b.setFixedSize(w,h)
    b.setStyleSheet(f'QPushButton{{background:{GOLD};color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:700;}} QPushButton:hover{{background:#e8940a;}}')
    return b

def fade_anim(widget,start=0.0,end=1.0,duration=200):
    eff=widget.graphicsEffect()
    if not isinstance(eff,QGraphicsOpacityEffect):
        eff=QGraphicsOpacityEffect(widget); widget.setGraphicsEffect(eff)
    eff.setOpacity(start)
    a=QPropertyAnimation(eff,b'opacity'); a.setDuration(duration)
    a.setStartValue(start); a.setEndValue(end); a.setEasingCurve(QEasingCurve.InOutQuad)
    widget._fade_anim=a; widget._fade_eff=eff
    return a

def lang_toggle_btn():
    """Language toggle button EN/ID."""
    lang=get_lang()
    lbl='EN' if lang=='id' else 'ID'
    b=QPushButton(lbl); b.setFixedSize(44,26)
    b.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:1px solid {D_BORDER};border-radius:4px;font-size:10px;font-weight:700;}} QPushButton:hover{{color:{D_TEXT};border-color:{D_TEXT};}}')
    return b

# ══════════════════════════════════════════════════════════════
# DUAL-PAGE BASE
# ══════════════════════════════════════════════════════════════
class DualPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background:{L_BG};')
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.sidebar=QWidget(); self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f'background:{D_BG};')
        self.sidebar_lay=QVBoxLayout(self.sidebar)
        self.sidebar_lay.setContentsMargins(24,32,24,32); self.sidebar_lay.setSpacing(0)
        root.addWidget(self.sidebar)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet('border:none;background:transparent;')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.verticalScrollBar().setStyleSheet(
            f'QScrollBar:vertical{{background:{L_BG};width:6px;}} '
            f'QScrollBar::handle:vertical{{background:{L_BORDER};border-radius:3px;}} '
            f'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}')
        self.content_w=QWidget(); self.content_w.setStyleSheet(f'background:{L_BG};')
        self.content_lay=QVBoxLayout(self.content_w)
        self.content_lay.setContentsMargins(36,36,36,36); self.content_lay.setSpacing(20)
        scroll.setWidget(self.content_w)
        root.addWidget(scroll,1)
        self._scroll=scroll

    def add_sidebar(self,w): self.sidebar_lay.addWidget(w)
    def add_sidebar_stretch(self): self.sidebar_lay.addStretch()
    def add_content(self,w,**kw): self.content_lay.addWidget(w,**kw)
    def add_content_stretch(self): self.content_lay.addStretch()
    def scroll_to_top(self): self._scroll.verticalScrollBar().setValue(0)

    def sidebar_label(self,text,size=11,bold=False,color=D_TEXT,spacing=0):
        l=QLabel(text); l.setWordWrap(True)
        weight='700' if bold else '400'
        l.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:{weight};letter-spacing:{spacing}px;background:transparent;')
        return l

    def content_label(self,text,size=13,bold=False,color=L_TEXT):
        l=QLabel(text); l.setWordWrap(True)
        weight='700' if bold else '400'
        l.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:{weight};background:transparent;')
        return l

    def _make_lang_btn(self):
        b=lang_toggle_btn()
        b.clicked.connect(self._toggle_lang)
        return b

    def _toggle_lang(self):
        new_lang='en' if get_lang()=='id' else 'id'
        set_lang(new_lang)
        LANG_BUS.changed.emit(new_lang)

    def on_lang_changed(self, lang):
        """Override di subclass untuk refresh teks."""
        pass

# ══════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════
class HomePage(DualPage):
    def __init__(self, on_iq, on_bigfive):
        super().__init__()
        self.on_iq=on_iq; self.on_bigfive=on_bigfive
        self._build()
        LANG_BUS.changed.connect(self.on_lang_changed)

    def _build(self):
        # Sidebar
        logo=self.sidebar_label(T('home.badge'), size=10, bold=True, color=GOLD, spacing=0)
        logo.setAlignment(Qt.AlignCenter); logo.setWordWrap(True)
        self.add_sidebar(logo)

        # Lang toggle top right of sidebar
        lt=self._make_lang_btn(); self.lang_btn=lt
        lt_wrap=QWidget(); lt_wrap.setStyleSheet('background:transparent;')
        ltl=QHBoxLayout(lt_wrap); ltl.setContentsMargins(0,0,0,0); ltl.addStretch(); ltl.addWidget(lt)
        self.add_sidebar(lt_wrap)
        self.add_sidebar_stretch()

        desc=self.sidebar_label(
            f'N={NORMS_DATA["n_population"]:,}\nIPIP Big Five · Kaggle\n\nOpen Psychometrics\nIQ Alpha Dataset',
            size=10, color=D_MUTED)
        self.add_sidebar(desc)
        self.add_sidebar_stretch()
        self.add_sidebar(self.sidebar_label('v4.0', size=10, color=D_MUTED))

        # Content
        self.title_lbl=self.content_label(T('home.title'), size=32, bold=True)
        self.title_lbl.setStyleSheet(f'color:{L_TEXT};font-size:32px;font-weight:700;background:transparent;')
        self.add_content(self.title_lbl)

        self.sub_lbl=self.content_label(T('home.subtitle'), size=14, color=L_MUTED)
        self.add_content(self.sub_lbl)

        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f'background:{L_BORDER};')
        self.add_content(sep)

        self._card_row=QWidget(); self._card_row.setStyleSheet('background:transparent;')
        self._card_rl=QHBoxLayout(self._card_row); self._card_rl.setContentsMargins(0,0,0,0); self._card_rl.setSpacing(16)
        self.iq_card  = self._menu_card('🧠', 'iq',   BLUE,  self.on_iq)
        self.bf_card  = self._menu_card('🎭', 'bf',   GOLD,  self.on_bigfive)
        self._card_rl.addWidget(self.iq_card); self._card_rl.addWidget(self.bf_card)
        self.add_content(self._card_row)
        self.add_content_stretch()

    def _menu_card(self, icon, key, color, on_click):
        card=QFrame()
        card.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:14px;')
        cl=QVBoxLayout(card); cl.setContentsMargins(24,24,24,24); cl.setSpacing(10)
        icon_l=QLabel(icon); icon_l.setStyleSheet('font-size:32px;background:transparent;border:none;')
        title_l=QLabel(T(f'home.{"iq" if key=="iq" else "bf"}_title'))
        title_l.setStyleSheet(f'color:{L_TEXT};font-size:18px;font-weight:700;background:transparent;border:none;')
        desc_l=QLabel(T(f'home.{"iq" if key=="iq" else "bf"}_desc'))
        desc_l.setWordWrap(True)
        desc_l.setStyleSheet(f'color:{L_MUTED};font-size:12px;background:transparent;border:none;')
        time_l=QLabel(f'⏱  {T(f"home.{"iq" if key=="iq" else "bf"}_time")}')
        time_l.setStyleSheet(f'color:{color};font-size:11px;font-weight:600;background:transparent;border:none;')
        btn=QPushButton(T(f'home.{"iq" if key=="iq" else "bf"}_btn')); btn.setFixedHeight(40)
        btn.setStyleSheet(f'QPushButton{{background:{color};color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:700;}} QPushButton:hover{{opacity:0.9;}}')
        btn.clicked.connect(on_click)
        cl.addWidget(icon_l); cl.addWidget(title_l); cl.addWidget(desc_l)
        cl.addWidget(time_l); cl.addStretch(); cl.addWidget(btn)
        return card

    def on_lang_changed(self, lang):
        self.lang_btn.setText('EN' if lang=='id' else 'ID')
        self.title_lbl.setText(T('home.title'))
        self.sub_lbl.setText(T('home.subtitle'))
        self._rebuild_cards()

    def _rebuild_cards(self):
        # Hapus semua widget di row, lalu rebuild
        while self._card_rl.count():
            item = self._card_rl.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
        self.iq_card = self._menu_card('🧠', 'iq', BLUE, self.on_iq)
        self.bf_card = self._menu_card('🎭', 'bf', GOLD, self.on_bigfive)
        self._card_rl.addWidget(self.iq_card)
        self._card_rl.addWidget(self.bf_card)

# ══════════════════════════════════════════════════════════════
# IQ QUESTION PAGE
# ══════════════════════════════════════════════════════════════
class IQQuestionPage(DualPage):
    def __init__(self, on_finish, on_home):
        super().__init__()
        self.on_finish=on_finish; self.on_home=on_home
        self.session=[]; self.answers=[]; self.current=0
        self._build_sidebar(); self._build_content()
        LANG_BUS.changed.connect(self.on_lang_changed)

    def _build_sidebar(self):
        top=QWidget(); top.setStyleSheet('background:transparent;')
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        self.side_title=self.sidebar_label(T('iq_test.sidebar_title'), size=11, bold=True, color=GOLD, spacing=2)
        self.lang_btn=self._make_lang_btn()
        tl.addWidget(self.side_title); tl.addStretch(); tl.addWidget(self.lang_btn)
        self.add_sidebar(top)
        self.add_sidebar(QWidget())
        self.timer_widget=CountdownTimer(1200)
        self.timer_widget.time_up.connect(self._time_up)
        tw=QWidget(); tw.setStyleSheet('background:transparent;')
        twl=QVBoxLayout(tw); twl.setAlignment(Qt.AlignCenter)
        twl.addWidget(self.timer_widget, alignment=Qt.AlignCenter)
        self.timer_lbl=self.sidebar_label(T('iq_test.time_label'), size=10, color=D_MUTED)
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        twl.addWidget(self.timer_lbl)
        self.add_sidebar(tw)
        self.add_sidebar_stretch()
        self.side_cat=self.sidebar_label('', size=10, color=D_MUTED)
        self.side_prog=self.sidebar_label('', size=22, bold=True, color=D_TEXT)
        self.add_sidebar(self.side_cat); self.add_sidebar(self.side_prog)
        self.add_sidebar_stretch()
        self.back_btn=QPushButton(T('iq_test.back_home'))
        self.back_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;text-align:left;padding:0;}} QPushButton:hover{{color:{D_TEXT};}}')
        self.back_btn.clicked.connect(self._go_home)
        self.add_sidebar(self.back_btn)

    def _build_content(self):
        self.prog_bar=ProgressBar(BLUE); self.add_content(self.prog_bar)
        self.q_container=QWidget(); self.q_container.setStyleSheet('background:transparent;')
        qcl=QVBoxLayout(self.q_container); qcl.setContentsMargins(0,0,0,0); qcl.setSpacing(12)
        self.q_card=lcard()
        self.q_label=QLabel('...')
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(f'color:{L_TEXT};font-size:16px;font-weight:400;line-height:1.7;')
        self.q_card.layout().addWidget(self.q_label)
        qcl.addWidget(self.q_card)
        self.opt_btns=[]
        for i in range(4):
            btn=QPushButton(); btn.setCheckable(True); btn.setFixedHeight(48)
            btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            btn.setStyleSheet(self._opt_s(False))
            btn.clicked.connect(lambda _,idx=i: self._pick(idx))
            self.opt_btns.append(btn); qcl.addWidget(btn)
        self.add_content(self.q_container)
        nav=QWidget(); nav.setStyleSheet('background:transparent;')
        nl=QHBoxLayout(nav); nl.setContentsMargins(0,0,0,0)
        self.btn_prev=dark_btn(T('iq_test.prev'),w=130,h=40); self.btn_prev.clicked.connect(self._prev)
        self.btn_next=gold_btn(T('iq_test.next'),w=130,h=40); self.btn_next.setEnabled(False); self.btn_next.clicked.connect(self._next)
        nl.addWidget(self.btn_prev); nl.addStretch(); nl.addWidget(self.btn_next)
        self.add_content(nav); self.add_content_stretch()

    def _opt_s(self,selected):
        if selected:
            return f'QPushButton{{background:rgba(59,130,246,0.08);border:2px solid {BLUE};color:{BLUE};font-size:13px;font-weight:600;border-radius:10px;text-align:left;padding:0 16px;}}'
        return f'QPushButton{{background:{L_SURFACE};border:1px solid {L_BORDER};color:{L_TEXT};font-size:13px;border-radius:10px;text-align:left;padding:0 16px;}} QPushButton:hover{{border-color:{BLUE};background:rgba(59,130,246,0.04);}}'

    def start_session(self):
        self.session=make_iq_session(); self.answers=[None]*len(self.session)
        self.current=0; self.timer_widget.start(); self.scroll_to_top(); self._render()

    def _render(self):
        if not self.session: return
        q=self.session[self.current]; n=len(self.session)
        self.prog_bar.set_value((self.current+1)/n*100)
        self.side_cat.setText(q['category'].upper())
        self.side_prog.setText(f'{self.current+1}/{n}')
        self.q_label.setText(q['q'])
        cur=self.answers[self.current]
        for i,btn in enumerate(self.opt_btns):
            btn.setText(f'  {chr(65+i)}.  {q["opts"][i]}')
            btn.setChecked(cur==i); btn.setStyleSheet(self._opt_s(cur==i))
        enabled=cur is not None
        self.btn_next.setEnabled(enabled)
        self.btn_next.setText(T('iq_test.finish') if self.current==n-1 else T('iq_test.next'))
        self.btn_prev.setVisible(self.current>0)
        fade_anim(self.q_container).start()

    def _pick(self,idx):
        self.answers[self.current]=idx
        for i,btn in enumerate(self.opt_btns): btn.setStyleSheet(self._opt_s(i==idx))
        self.btn_next.setEnabled(True)

    def _next(self):
        if self.answers[self.current] is None: return
        if self.current==len(self.session)-1:
            self.timer_widget.stop(); self.on_finish(self.answers,self.session); return
        self.current+=1; self._render()

    def _prev(self):
        if self.current==0: return
        self.current-=1; self._render()

    def _time_up(self): self.on_finish(self.answers,self.session)
    def _go_home(self): self.timer_widget.stop(); self.on_home()

    def on_lang_changed(self,lang):
        self.lang_btn.setText('EN' if lang=='id' else 'ID')
        self.side_title.setText(T('iq_test.sidebar_title'))
        self.timer_lbl.setText(T('iq_test.time_label'))
        self.back_btn.setText(T('iq_test.back_home'))
        if self.session: self._render()

# ══════════════════════════════════════════════════════════════
# IQ RESULT PAGE
# ══════════════════════════════════════════════════════════════
class IQResultPage(DualPage):
    def __init__(self, on_restart, on_home):
        super().__init__()
        self.on_restart=on_restart; self.on_home=on_home
        self._analysis=None; self._iq_answers=None; self._iq_session=None
        self._build_sidebar(); self._build_content()
        LANG_BUS.changed.connect(self.on_lang_changed)

    def _build_sidebar(self):
        top=QWidget(); top.setStyleSheet('background:transparent;')
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        self.side_title=self.sidebar_label(T('iq_result.sidebar_title'),size=11,bold=True,color=GOLD,spacing=2)
        self.lang_btn=self._make_lang_btn()
        tl.addWidget(self.side_title); tl.addStretch(); tl.addWidget(self.lang_btn)
        self.add_sidebar(top)
        self.add_sidebar_stretch()
        self.side_iq=self.sidebar_label('—',size=48,bold=True,color=D_TEXT)
        self.side_iq.setAlignment(Qt.AlignCenter)
        self.side_label_lbl=self.sidebar_label('—',size=13,color=D_MUTED)
        self.side_label_lbl.setAlignment(Qt.AlignCenter)
        self.side_pct=self.sidebar_label('',size=11,color=D_MUTED)
        self.side_pct.setAlignment(Qt.AlignCenter)
        self.add_sidebar(self.side_iq); self.add_sidebar(self.side_label_lbl); self.add_sidebar(self.side_pct)
        self.add_sidebar_stretch()
        self.export_btn=QPushButton(T('iq_result.export_btn'))
        self.export_btn.setFixedHeight(38)
        self.export_btn.setStyleSheet(f'QPushButton{{background:{GOLD};color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;}} QPushButton:hover{{background:#e8940a;}}')
        self.export_btn.clicked.connect(self._export)
        self.add_sidebar(self.export_btn)
        self.add_sidebar(QWidget())
        self.restart_btn=QPushButton(T('iq_result.restart_btn'))
        self.restart_btn.setFixedHeight(38)
        self.restart_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:1px solid {D_BORDER};border-radius:6px;font-size:12px;}} QPushButton:hover{{color:{D_TEXT};border-color:{D_TEXT};}}')
        self.restart_btn.clicked.connect(self.on_restart)
        self.add_sidebar(self.restart_btn)
        self.home_btn=QPushButton(T('iq_result.home_btn'))
        self.home_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;padding:8px 0;}} QPushButton:hover{{color:{D_TEXT};}}')
        self.home_btn.clicked.connect(self.on_home)
        self.add_sidebar(self.home_btn)

    def _build_content(self):
        # Summary row
        self.summary_row=QWidget(); self.summary_row.setStyleSheet('background:transparent;')
        self.summary_l=QHBoxLayout(self.summary_row); self.summary_l.setSpacing(12); self.summary_l.setContentsMargins(0,0,0,0)
        self.add_content(self.summary_row)
        # Cognitive Profile
        self.cog_card=lcard(T('expert.cognitive_title'))
        self.cog_l=QVBoxLayout(); self.cog_l.setSpacing(10)
        self.cog_card.layout().addLayout(self.cog_l)
        self.add_content(self.cog_card)
        # Breakdown
        self.breakdown_card=lcard(T('iq_result.breakdown_title'))
        self.breakdown_l=QVBoxLayout(); self.breakdown_l.setSpacing(10)
        self.breakdown_card.layout().addLayout(self.breakdown_l)
        self.add_content(self.breakdown_card)
        # Accordion review
        self.review_card=lcard(T('iq_result.review_title'))
        self.review_l=QVBoxLayout(); self.review_l.setSpacing(0)
        self.review_card.layout().addLayout(self.review_l)
        self.add_content(self.review_card)
        # Insight
        self.insight_card=lcard()
        self.insight_card.setStyleSheet(f'background:{GOLD_LIGHT};border:1px solid #f5d88a;border-radius:12px;')
        il=self.insight_card.layout()
        il.addWidget(QLabel(f'⚡  {T("iq_result.insight_title")}', styleSheet=f'color:{GOLD};font-size:10px;font-weight:700;letter-spacing:2px;background:transparent;'))
        self.insight_lbl=QLabel(); self.insight_lbl.setWordWrap(True)
        self.insight_lbl.setStyleSheet(f'color:#7a5200;font-size:13px;line-height:1.8;background:transparent;')
        il.addWidget(self.insight_lbl)
        self.add_content(self.insight_card)
        self.add_content_stretch()

    def load(self, answers, session, bf_scores=None):
        self._iq_answers=answers; self._iq_session=session
        lang=get_lang()
        iq_res = engine_score_to_iq(answers, session)
        cognitive = build_cognitive_profile(answers, session)

        iq=iq_res['iq']; label=iq_res['label']; color=iq_res['color']
        pctile=iq_res['percentile']; correct=iq_res['correct']; total=iq_res['total']

        # If bf available, run full analysis
        if bf_scores:
            self._analysis = run_full_analysis(answers, session, bf_scores)
        else:
            self._analysis = {**iq_res, 'cognitive': cognitive, 'lang': lang,
                              'n_bf_pop': NORMS_DATA.get('n_population',874434)}
        self._analysis['iq_answers'] = answers
        self._analysis['iq_session'] = session

        label_loc = T(f'iq_categories.{label}')
        self.side_iq.setText(str(iq))
        self.side_iq.setStyleSheet(f'color:{color};font-size:48px;font-weight:700;background:transparent;')
        self.side_label_lbl.setText(label_loc)
        self.side_pct.setText(f'{T("iq_result.percentile_label")}{pctile}')

        # Summary cards
        self._clear_layout(self.summary_l)
        wrong=total-correct
        for val,lbl2,col in [(correct,T('iq_result.summary_correct'),GREEN),
                             (wrong,T('iq_result.summary_wrong'),RED),
                             (total,T('iq_result.summary_total'),BLUE)]:
            cell=QFrame(); cell.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl=QVBoxLayout(cell); cl.setAlignment(Qt.AlignCenter); cl.setContentsMargins(12,14,12,14)
            vl=QLabel(str(val)); vl.setStyleSheet(f'color:{col};font-size:26px;font-weight:700;background:transparent;'); vl.setAlignment(Qt.AlignCenter)
            ll=QLabel(lbl2); ll.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;'); ll.setAlignment(Qt.AlignCenter)
            cl.addWidget(vl); cl.addWidget(ll)
            self.summary_l.addWidget(cell)

        # Cognitive Profile
        self._clear_layout(self.cog_l)
        cog_names = COG_NAMES_ID if lang=='id' else COG_NAMES_EN
        cog_desc  = COGNITIVE_DESC_ID if lang=='id' else COGNITIVE_DESC_EN
        for dom, d in sorted(cognitive.items(), key=lambda x: x[1]['rank']):
            pct_c = d['score_pct']; lvl = d['level']
            col_c = COG_COLORS.get(dom, BLUE)
            name  = cog_names.get(dom, dom)
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,2); rl.setSpacing(3)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            nl=QLabel(name); nl.setStyleSheet(f'color:{col_c};font-weight:700;font-size:12px;background:transparent;')
            lv=QLabel(COGNITIVE_LEVEL_ID.get(lvl,lvl) if lang=='id' else lvl)
            lv.setStyleSheet(f'color:{col_c};font-size:10px;background:rgba(0,0,0,0.05);padding:1px 8px;border-radius:4px;')
            sl2=QLabel(f'{pct_c:.0f}%'); sl2.setStyleSheet(f'color:{col_c};font-size:14px;font-weight:700;background:transparent;')
            hl.addWidget(nl); hl.addWidget(lv); hl.addStretch(); hl.addWidget(sl2)
            rl.addWidget(hdr)
            desc_txt = cog_desc.get(dom,{}).get(lvl,'')
            if desc_txt:
                dl=QLabel(desc_txt); dl.setWordWrap(True)
                dl.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;')
                rl.addWidget(dl)
            bar=AnimatedBar(col_c); rl.addWidget(bar)
            self.cog_l.addWidget(row)
            QTimer.singleShot(300, lambda b=bar,v=pct_c: b.animate_to(v))

        # Category Breakdown
        self._clear_layout(self.breakdown_l)
        cats={}
        for i,q in enumerate(session):
            c=q['category']
            if c not in cats: cats[c]={'correct':0,'total':0}
            cats[c]['total']+=1
            if answers[i]==q['ans']: cats[c]['correct']+=1
        for cat,d in cats.items():
            pct_cat=d['correct']/d['total']*100; cc=CAT_COLORS.get(cat,GOLD)
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            hl.addWidget(QLabel(cat, styleSheet=f'color:{cc};font-size:12px;font-weight:600;background:transparent;'))
            hl.addStretch()
            hl.addWidget(QLabel(f'{d["correct"]}/{d["total"]} ({pct_cat:.0f}%)', styleSheet=f'color:{L_MUTED};font-size:11px;background:transparent;'))
            rl.addWidget(hdr)
            bar=AnimatedBar(cc); rl.addWidget(bar)
            self.breakdown_l.addWidget(row)
            QTimer.singleShot(300, lambda b=bar,v=pct_cat: b.animate_to(v))

        # Accordion
        self._clear_layout(self.review_l)
        for i,q in enumerate(session):
            self.review_l.addWidget(AccordionItem(i+1,q,answers[i],q['ans']))

        # Insight
        pop_mean=IQ_NORMS_DATA['stats']['total']['mean']
        pct_c2=correct/total*100
        if lang=='id':
            ins=f"IQ {iq} — {label_loc}. Kamu menjawab benar {correct}/{total} soal ({pct_c2:.0f}%). "\
                f"Berada di persentil ke-{pctile} dari {iq_res['n_population']:,} {T('iq_result.population_label')}."
        else:
            ins=f"IQ {iq} — {label_loc}. You answered {correct}/{total} correctly ({pct_c2:.0f}%). "\
                f"Ranked at the {pctile}th percentile among {iq_res['n_population']:,} {T('iq_result.population_label')}."
        self.insight_lbl.setText(ins)
        self.scroll_to_top()

    def _clear_layout(self, lay):
        while lay.count():
            item=lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _export(self):
        if not self._analysis:
            QMessageBox.warning(self,'','Selesaikan tes dulu.' if get_lang()=='id' else 'Complete the test first.')
            return
        path,_=QFileDialog.getSaveFileName(self,'Save PDF','hasil_assessment.pdf','PDF Files (*.pdf)')
        if not path: return
        try:
            from report.pdf_generator import generate_pdf
            txt=_I18N[get_lang()]
            generate_pdf(path, self._analysis, txt)
            QMessageBox.information(self,'OK',f'PDF saved:\n{path}')
        except Exception as ex:
            QMessageBox.warning(self,'Error',str(ex))

    def on_lang_changed(self,lang):
        self.lang_btn.setText('EN' if lang=='id' else 'ID')
        self.side_title.setText(T('iq_result.sidebar_title'))
        self.export_btn.setText(T('iq_result.export_btn'))
        self.restart_btn.setText(T('iq_result.restart_btn'))
        self.home_btn.setText(T('iq_result.home_btn'))
        if self._iq_answers: self.load(self._iq_answers, self._iq_session,
                                        self._analysis.get('bf_scores') if self._analysis else None)

# ══════════════════════════════════════════════════════════════
# BF QUESTION PAGE
# ══════════════════════════════════════════════════════════════
class BFQuestionPage(DualPage):
    def __init__(self, on_finish, on_home):
        super().__init__()
        self.on_finish=on_finish; self.on_home=on_home
        self.session=[]; self.answers=[]; self.current=0
        self._build_sidebar(); self._build_content()
        LANG_BUS.changed.connect(self.on_lang_changed)

    def _build_sidebar(self):
        top=QWidget(); top.setStyleSheet('background:transparent;')
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        self.side_title=self.sidebar_label(T('bf_test.sidebar_title'),size=11,bold=True,color=GOLD,spacing=1)
        self.lang_btn=self._make_lang_btn()
        tl.addWidget(self.side_title); tl.addStretch(); tl.addWidget(self.lang_btn)
        self.add_sidebar(top)
        self.add_sidebar_stretch()
        self.side_trait=self.sidebar_label('',size=13,bold=True,color=D_TEXT)
        self.side_prog=self.sidebar_label('',size=22,bold=True,color=D_TEXT)
        self.side_desc=self.sidebar_label('',size=10,color=D_MUTED)
        self.add_sidebar(self.side_trait); self.add_sidebar(self.side_prog); self.add_sidebar(self.side_desc)
        self.add_sidebar_stretch()
        self.back_btn=QPushButton(T('bf_test.back_home'))
        self.back_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;text-align:left;padding:0;}} QPushButton:hover{{color:{D_TEXT};}}')
        self.back_btn.clicked.connect(self.on_home)
        self.add_sidebar(self.back_btn)

    def _build_content(self):
        self.prog_bar=ProgressBar(GOLD); self.add_content(self.prog_bar)
        self.q_container=QWidget(); self.q_container.setStyleSheet('background:transparent;')
        qcl=QVBoxLayout(self.q_container); qcl.setContentsMargins(0,0,0,0); qcl.setSpacing(12)
        self.q_card=lcard()
        self.q_label=QLabel('...')
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(f'color:{L_TEXT};font-size:16px;font-weight:400;line-height:1.7;')
        self.q_card.layout().addWidget(self.q_label)
        qcl.addWidget(self.q_card)
        scale=QWidget(); scale.setStyleSheet('background:transparent;')
        sl=QHBoxLayout(scale); sl.setContentsMargins(0,0,0,0)
        self.scale_l=QLabel(T('bf_test.scale_left')); self.scale_l.setStyleSheet(f'color:{L_MUTED};font-size:10px;background:transparent;')
        self.scale_m=QLabel(T('bf_test.scale_mid'));  self.scale_m.setStyleSheet(f'color:{L_MUTED};font-size:10px;background:transparent;')
        self.scale_r=QLabel(T('bf_test.scale_right'));self.scale_r.setStyleSheet(f'color:{L_MUTED};font-size:10px;background:transparent;')
        sl.addWidget(self.scale_l); sl.addStretch(); sl.addWidget(self.scale_m); sl.addStretch(); sl.addWidget(self.scale_r)
        qcl.addWidget(scale)
        likert=QWidget(); likert.setStyleSheet('background:transparent;')
        ll=QHBoxLayout(likert); ll.setSpacing(10)
        self.likert_btns=[]
        self.btn_group=QButtonGroup(self); self.btn_group.setExclusive(True)
        for v in range(1,6):
            btn=QPushButton(str(v)); btn.setCheckable(True); btn.setFixedHeight(52)
            btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            btn.setStyleSheet(self._btn_s(False))
            btn.clicked.connect(lambda _,val=v: self._pick(val))
            self.btn_group.addButton(btn,v); self.likert_btns.append(btn); ll.addWidget(btn)
        qcl.addWidget(likert)
        self.add_content(self.q_container)
        nav=QWidget(); nav.setStyleSheet('background:transparent;')
        nl=QHBoxLayout(nav); nl.setContentsMargins(0,0,0,0)
        self.btn_prev=dark_btn(T('bf_test.prev'),w=130,h=40); self.btn_prev.clicked.connect(self._prev)
        self.btn_next=gold_btn(T('bf_test.next'),w=130,h=40); self.btn_next.setEnabled(False); self.btn_next.clicked.connect(self._next)
        nl.addWidget(self.btn_prev); nl.addStretch(); nl.addWidget(self.btn_next)
        self.add_content(nav); self.add_content_stretch()

    def _btn_s(self,sel):
        if sel: return f'QPushButton{{background:rgba(245,166,35,0.10);border:2px solid {GOLD};color:{GOLD};font-size:15px;font-weight:700;border-radius:10px;}}'
        return f'QPushButton{{background:{L_SURFACE};border:1px solid {L_BORDER};color:{L_TEXT};font-size:15px;border-radius:10px;}} QPushButton:hover{{border-color:{GOLD};background:rgba(245,166,35,0.04);}}'

    def start_session(self):
        self.session=make_bf_session(); self.answers=[None]*len(self.session)
        self.current=0; self.scroll_to_top(); self._render()

    def _render(self):
        if not self.session: return
        trait,text,_=self.session[self.current]; n=len(self.session)
        self.prog_bar.set_value((self.current+1)/n*100)
        tc=TRAIT_COLORS[trait]
        trait_names=_I18N[get_lang()]['trait_names']
        trait_low  =_I18N[get_lang()]['trait_low']
        trait_high =_I18N[get_lang()]['trait_high']
        self.side_trait.setText(trait_names.get(trait,trait))
        self.side_trait.setStyleSheet(f'color:{tc};font-size:13px;font-weight:700;background:transparent;')
        self.side_prog.setText(f'{self.current+1}/{n}')
        self.side_desc.setText(f'{trait_low.get(trait,"")} ↔ {trait_high.get(trait,"")}')
        self.q_label.setText(text)
        cur=self.answers[self.current]
        for i,btn in enumerate(self.likert_btns):
            btn.setChecked(cur==i+1); btn.setStyleSheet(self._btn_s(cur==i+1))
        enabled=cur is not None; self.btn_next.setEnabled(enabled)
        self.btn_next.setText(T('bf_test.finish') if self.current==n-1 else T('bf_test.next'))
        self.btn_prev.setVisible(self.current>0)
        fade_anim(self.q_container).start()

    def _pick(self,val):
        self.answers[self.current]=val
        for i,btn in enumerate(self.likert_btns): btn.setStyleSheet(self._btn_s(i+1==val))
        self.btn_next.setEnabled(True)

    def _next(self):
        if self.answers[self.current] is None: return
        if self.current==len(self.session)-1: self.on_finish(self.answers,self.session); return
        self.current+=1; self._render()

    def _prev(self):
        if self.current==0: return
        self.current-=1; self._render()

    def on_lang_changed(self,lang):
        self.lang_btn.setText('EN' if lang=='id' else 'ID')
        self.side_title.setText(T('bf_test.sidebar_title'))
        self.back_btn.setText(T('bf_test.back_home'))
        self.scale_l.setText(T('bf_test.scale_left'))
        self.scale_m.setText(T('bf_test.scale_mid'))
        self.scale_r.setText(T('bf_test.scale_right'))
        if self.session: self._render()

# ══════════════════════════════════════════════════════════════
# BF RESULT PAGE — with full expert engine output
# ══════════════════════════════════════════════════════════════
class BFResultPage(DualPage):
    def __init__(self, on_restart, on_home, get_iq_data_fn=None):
        super().__init__()
        self.on_restart=on_restart; self.on_home=on_home
        self.get_iq_data_fn=get_iq_data_fn
        self._analysis=None; self.bars={}
        self._bf_answers=None; self._bf_session=None
        self._build_sidebar(); self._build_content()
        LANG_BUS.changed.connect(self.on_lang_changed)

    def _build_sidebar(self):
        top=QWidget(); top.setStyleSheet('background:transparent;')
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        self.side_title=self.sidebar_label(T('bf_result.sidebar_title'),size=11,bold=True,color=GOLD,spacing=1)
        self.lang_btn=self._make_lang_btn()
        tl.addWidget(self.side_title); tl.addStretch(); tl.addWidget(self.lang_btn)
        self.add_sidebar(top)
        self.add_sidebar_stretch()
        self.side_tag=self.sidebar_label('',size=9,color=D_MUTED,spacing=1)
        self.side_name=self.sidebar_label('',size=15,bold=True,color=D_TEXT)
        self.side_name.setWordWrap(True)
        self.add_sidebar(self.side_tag); self.add_sidebar(self.side_name)
        self.add_sidebar_stretch()
        self.export_btn=QPushButton(T('iq_result.export_btn'))
        self.export_btn.setFixedHeight(38)
        self.export_btn.setStyleSheet(f'QPushButton{{background:{GOLD};color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;}} QPushButton:hover{{background:#e8940a;}}')
        self.export_btn.clicked.connect(self._export)
        self.add_sidebar(self.export_btn)
        self.add_sidebar(QWidget())
        self.restart_btn=QPushButton(T('bf_result.restart_btn'))
        self.restart_btn.setFixedHeight(38)
        self.restart_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:1px solid {D_BORDER};border-radius:6px;font-size:12px;}} QPushButton:hover{{color:{D_TEXT};border-color:{D_TEXT};}}')
        self.restart_btn.clicked.connect(self.on_restart)
        self.add_sidebar(self.restart_btn)
        self.home_btn=QPushButton(T('bf_result.home_btn'))
        self.home_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;padding:8px 0;}} QPushButton:hover{{color:{D_TEXT};}}')
        self.home_btn.clicked.connect(self.on_home)
        self.add_sidebar(self.home_btn)

    def _build_content(self):
        # Percentile cards
        self.pct_row=QWidget(); self.pct_row.setStyleSheet('background:transparent;')
        self.pct_l=QHBoxLayout(self.pct_row); self.pct_l.setSpacing(8); self.pct_l.setContentsMargins(0,0,0,0)
        self.pct_labels={}
        for t in TRAITS:
            cell=QFrame(); cell.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl=QVBoxLayout(cell); cl.setAlignment(Qt.AlignCenter); cl.setContentsMargins(8,12,8,12); cl.setSpacing(2)
            tl2=QLabel(t); tl2.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:10px;font-weight:700;background:transparent;'); tl2.setAlignment(Qt.AlignCenter)
            vl=QLabel('—'); vl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:20px;font-weight:700;background:transparent;'); vl.setAlignment(Qt.AlignCenter)
            sl2=QLabel(T('bf_result.percentile_label')); sl2.setStyleSheet(f'color:{L_MUTED};font-size:9px;background:transparent;'); sl2.setAlignment(Qt.AlignCenter)
            cl.addWidget(tl2); cl.addWidget(vl); cl.addWidget(sl2)
            self.pct_l.addWidget(cell); self.pct_labels[t]=vl
        self.add_content(self.pct_row)
        # Radar
        radar_card=lcard(T('bf_result.radar_title'))
        self.radar_container=QVBoxLayout(); self.radar_container.setAlignment(Qt.AlignCenter)
        radar_card.layout().addLayout(self.radar_container)
        self.add_content(radar_card)
        # Trait bars
        self.bars_card=lcard(T('bf_result.bars_title'))
        self.bars_l=QVBoxLayout(); self.bars_l.setSpacing(14)
        self.bars_card.layout().addLayout(self.bars_l)
        self.add_content(self.bars_card)
        # Combined profile
        self.combined_card=lcard(T('expert.combined_title'))
        self.combined_l=QVBoxLayout(); self.combined_l.setSpacing(6)
        self.combined_card.layout().addLayout(self.combined_l)
        self.add_content(self.combined_card)
        # Career
        self.career_card=lcard(T('expert.career_title'))
        self.career_l=QVBoxLayout(); self.career_l.setSpacing(8)
        self.career_card.layout().addLayout(self.career_l)
        self.add_content(self.career_card)
        # Learning style
        self.learning_card=lcard(T('expert.learning_title'))
        self.learning_l=QVBoxLayout(); self.learning_l.setSpacing(6)
        self.learning_card.layout().addLayout(self.learning_l)
        self.add_content(self.learning_card)
        # Blind spots
        self.blind_card=lcard(T('expert.blindspot_title'))
        self.blind_l=QVBoxLayout(); self.blind_l.setSpacing(8)
        self.blind_card.layout().addLayout(self.blind_l)
        self.add_content(self.blind_card)
        # Roadmap
        self.roadmap_card=lcard(T('expert.roadmap_title'))
        self.roadmap_l=QVBoxLayout(); self.roadmap_l.setSpacing(8)
        self.roadmap_card.layout().addLayout(self.roadmap_l)
        self.add_content(self.roadmap_card)
        # Insight
        self.insight_card=lcard()
        self.insight_card.setStyleSheet(f'background:{GOLD_LIGHT};border:1px solid #f5d88a;border-radius:12px;')
        il=self.insight_card.layout()
        il.addWidget(QLabel(f'⚡  {T("bf_result.insight_title")}', styleSheet=f'color:{GOLD};font-size:10px;font-weight:700;letter-spacing:2px;background:transparent;'))
        self.insight_lbl=QLabel(); self.insight_lbl.setWordWrap(True)
        self.insight_lbl.setStyleSheet(f'color:#7a5200;font-size:13px;line-height:1.8;background:transparent;')
        il.addWidget(self.insight_lbl)
        self.add_content(self.insight_card)
        self.add_content_stretch()

    def load(self, answers, session):
        self._bf_answers=answers; self._bf_session=session
        lang=get_lang()
        scores=compute_bf_scores(answers,session)
        pcts={t:get_percentile_bf(t,scores[t]) for t in TRAITS}

        # Try to get IQ data for full analysis
        iq_data = self.get_iq_data_fn() if self.get_iq_data_fn else None
        if iq_data:
            self._analysis = run_full_analysis(
                iq_data['answers'], iq_data['session'], scores)
        else:
            # BF only — run partial engine
            from engine.expert_rules import (get_archetype, get_combined_profile,
                get_career_recommendations, get_learning_style, get_blind_spots, get_roadmap)
            from engine.scoring import build_cognitive_profile
            mock_cog = {d:{'score_pct':50,'level':'Average','rank':i,'questions':8}
                        for i,d in enumerate(['fluid','crystallized','abstract','quantitative','spatial'],1)}
            arch  = get_archetype(scores, lang)
            comb  = get_combined_profile(100, scores, lang)
            cars  = get_career_recommendations(100, scores, lang, top_n=5)
            sname,sdet = get_learning_style(scores, mock_cog, lang)
            bs    = get_blind_spots(100, scores, lang)
            rm    = get_roadmap(100, scores, mock_cog, cars, lang)
            self._analysis = {
                'iq':100,'label':'Average','color':PURPLE,'percentile':50,
                'correct':0,'total':0,'weighted_pct':0,
                'n_population':2051,'cognitive':mock_cog,
                'archetype':arch,'combined':comb,'careers':cars,
                'learning_style_name':sname,'learning_style_detail':sdet,
                'blind_spots':bs,'roadmap':rm,
                'bf_scores':scores,'bf_pcts':pcts,
                'lang':lang,'n_bf_pop':NORMS_DATA.get('n_population',874434),
            }

        arch = self._analysis['archetype']
        self.side_tag.setText(arch.get('tag',''))
        self.side_name.setText(arch.get('name',''))
        for t in TRAITS: self.pct_labels[t].setText(f"{round(pcts[t])}th")

        # Radar
        while self.radar_container.count():
            item=self.radar_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.radar_container.addWidget(RadarWidget(scores,POP_STAT))

        # Trait bars
        self._clear_layout(self.bars_l)
        self.bars={}
        trait_names=_I18N[lang]['trait_names']
        trait_low  =_I18N[lang]['trait_low']
        trait_high =_I18N[lang]['trait_high']
        for t in TRAITS:
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            nl=QLabel(trait_names.get(t,t)); nl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-weight:600;font-size:13px;background:transparent;')
            pb=QLabel(f'{round(pcts[t])}th')
            pb.setStyleSheet(f'color:{GOLD};background:{GOLD_LIGHT};border:1px solid #f5d88a;padding:1px 8px;border-radius:4px;font-size:10px;font-weight:700;')
            sl2=QLabel(f'{scores[t]}/100'); sl2.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:17px;font-weight:600;background:transparent;')
            hl.addWidget(nl); hl.addWidget(pb); hl.addStretch(); hl.addWidget(sl2)
            rl.addWidget(hdr)
            sub=QLabel(f'{trait_low.get(t,"")} \u2194 {trait_high.get(t,"")}  ·  Pop: {round(POP_STAT[t]["mean"])}')
            sub.setStyleSheet(f'color:{L_MUTED};font-size:10px;background:transparent;')
            rl.addWidget(sub)
            bar=AnimatedBar(TRAIT_COLORS[t],POP_STAT[t]['mean']); rl.addWidget(bar)
            self.bars_l.addWidget(row); self.bars[t]=(bar,scores[t])

        # Combined profile
        self._clear_layout(self.combined_l)
        comb=self._analysis['combined']
        cn=QLabel(f'<b>{comb.get("name","")}</b>')
        cn.setStyleSheet(f'color:{L_TEXT};font-size:14px;background:transparent;')
        cd=QLabel(comb.get('desc','')); cd.setWordWrap(True)
        cd.setStyleSheet(f'color:{L_MUTED};font-size:12px;background:transparent;')
        ca=QLabel(f'→  {comb.get("action","")}'); ca.setWordWrap(True)
        ca.setStyleSheet(f'color:{BLUE};font-size:12px;font-weight:600;background:transparent;')
        self.combined_l.addWidget(cn); self.combined_l.addWidget(cd); self.combined_l.addWidget(ca)

        # Career
        self._clear_layout(self.career_l)
        sub_c=QLabel(T('expert.career_subtitle')); sub_c.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;')
        self.career_l.addWidget(sub_c)
        career_colors=['#27ae60','#3b82f6','#8b5cf6','#f97316','#e74c3c']
        for i,c in enumerate(self._analysis['careers']):
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,2); rl.setSpacing(3)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            rank=['🥇','🥈','🥉','4.','5.'][i]
            nl=QLabel(f'{rank}  {c["name"]}'); nl.setStyleSheet(f'color:{L_TEXT};font-size:13px;font-weight:600;background:transparent;')
            cl2=QLabel(f'{c["confidence"]}%'); cl2.setStyleSheet(f'color:{career_colors[i]};font-size:13px;font-weight:700;background:transparent;')
            hl.addWidget(nl); hl.addStretch(); hl.addWidget(cl2)
            rl.addWidget(hdr)
            bar=AnimatedBar(career_colors[i]); rl.addWidget(bar)
            self.career_l.addWidget(row)
            QTimer.singleShot(400+i*80, lambda b=bar,v=c['confidence']: b.animate_to(v))

        # Learning style
        self._clear_layout(self.learning_l)
        sname=self._analysis['learning_style_name']
        sdet=self._analysis['learning_style_detail']
        sn=QLabel(f'<b>{sname}</b>'); sn.setStyleSheet(f'color:{BLUE};font-size:15px;background:transparent;')
        sd=QLabel(sdet.get('desc','')); sd.setWordWrap(True)
        sd.setStyleSheet(f'color:{L_MUTED};font-size:12px;background:transparent;')
        self.learning_l.addWidget(sn); self.learning_l.addWidget(sd)
        tips=sdet.get('tips',[])
        if tips:
            tips_lbl='Tips:' if lang=='id' else 'Tips:'
            self.learning_l.addWidget(QLabel(f'<b>{tips_lbl}</b>', styleSheet=f'color:{L_TEXT};font-size:12px;background:transparent;'))
            for tip in tips:
                tl2=QLabel(f'• {tip}'); tl2.setWordWrap(True)
                tl2.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;padding-left:8px;')
                self.learning_l.addWidget(tl2)
        env=sdet.get('environment','')
        if env:
            env_lbl='Lingkungan ideal:' if lang=='id' else 'Ideal environment:'
            el=QLabel(f'<b>{env_lbl}</b> {env}'); el.setWordWrap(True)
            el.setStyleSheet(f'color:{L_TEXT};font-size:11px;background:transparent;')
            self.learning_l.addWidget(el)

        # Blind spots
        self._clear_layout(self.blind_l)
        for bs in self._analysis['blind_spots']:
            card=QFrame(); card.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl2=QVBoxLayout(card); cl2.setContentsMargins(14,12,14,12); cl2.setSpacing(4)
            tl3=QLabel(f'⚠  {bs["title"]}'); tl3.setStyleSheet(f'color:{RED};font-size:12px;font-weight:700;background:transparent;')
            dl=QLabel(bs['desc']); dl.setWordWrap(True); dl.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;')
            mit_lbl='Mitigasi:' if lang=='id' else 'Mitigation:'
            ml=QLabel(f'<b>{mit_lbl}</b> {bs["mitigation"]}'); ml.setWordWrap(True)
            ml.setStyleSheet(f'color:#1a4731;font-size:11px;background:#e8f8f0;padding:4px 8px;border-radius:4px;')
            cl2.addWidget(tl3); cl2.addWidget(dl); cl2.addWidget(ml)
            self.blind_l.addWidget(card)

        # Roadmap
        self._clear_layout(self.roadmap_l)
        month_colors=[BLUE,GREEN,GOLD]
        month_lbl=T('expert.roadmap_month') if hasattr(T,'__call__') else 'Bulan'
        for i,month in enumerate(self._analysis['roadmap']):
            card=QFrame(); card.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl2=QVBoxLayout(card); cl2.setContentsMargins(14,12,14,12); cl2.setSpacing(6)
            col_m=month_colors[i%len(month_colors)]
            hdr_lbl=QLabel(f'<b>{T("expert.roadmap_month")} {month["month"]}  —  {month["focus"]}</b>')
            hdr_lbl.setStyleSheet(f'color:{col_m};font-size:13px;background:transparent;')
            cl2.addWidget(hdr_lbl)
            sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f'background:{L_BORDER};')
            cl2.addWidget(sep)
            for act in month.get('actions',[]):
                al=QLabel(f'☐  {act}'); al.setWordWrap(True)
                al.setStyleSheet(f'color:{L_TEXT};font-size:11px;background:transparent;padding:2px 0;')
                cl2.addWidget(al)
            self.roadmap_l.addWidget(card)

        # Insight
        top_trait=max(TRAITS,key=lambda k:pcts[k])
        trait_names2=_I18N[lang]['trait_names']
        if lang=='id':
            ins=f"Dimensi {trait_names2.get(top_trait,top_trait)}-mu berada di persentil ke-{round(pcts[top_trait])}, " \
                f"lebih tinggi dari {round(pcts[top_trait])}% dari {NORMS_DATA['n_population']:,} responden dataset. " \
                f"Profil kombinasimu: {self._analysis['archetype'].get('name','')}."
        else:
            ins=f"Your {trait_names2.get(top_trait,top_trait)} dimension is at the {round(pcts[top_trait])}th percentile, " \
                f"higher than {round(pcts[top_trait])}% of {NORMS_DATA['n_population']:,} dataset respondents. " \
                f"Your combined profile: {self._analysis['archetype'].get('name','')}."
        self.insight_lbl.setText(ins)

        QTimer.singleShot(300, self._anim_bars)
        self.scroll_to_top()

    def _clear_layout(self,lay):
        while lay.count():
            item=lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _anim_bars(self):
        for t,(bar,score) in self.bars.items(): bar.animate_to(score)

    def get_data(self):
        """Return {answers, session} untuk dipakai IQ result page."""
        if self._bf_answers and self._bf_session:
            return {'answers':self._bf_answers,'session':self._bf_session}
        return None

    def get_bf_scores(self):
        if self._bf_answers and self._bf_session:
            return compute_bf_scores(self._bf_answers, self._bf_session)
        return None

    def _export(self):
        if not self._analysis:
            QMessageBox.warning(self,'','Selesaikan tes dulu.' if get_lang()=='id' else 'Complete the test first.')
            return
        path,_=QFileDialog.getSaveFileName(self,'Save PDF','hasil_assessment.pdf','PDF Files (*.pdf)')
        if not path: return
        try:
            from report.pdf_generator import generate_pdf
            txt=_I18N[get_lang()]
            generate_pdf(path, self._analysis, txt)
            QMessageBox.information(self,'OK',f'PDF saved:\n{path}')
        except Exception as ex:
            QMessageBox.warning(self,'Error',str(ex))

    def on_lang_changed(self,lang):
        self.lang_btn.setText('EN' if lang=='id' else 'ID')
        self.side_title.setText(T('bf_result.sidebar_title'))
        self.restart_btn.setText(T('bf_result.restart_btn'))
        self.home_btn.setText(T('bf_result.home_btn'))
        if self._bf_answers: self.load(self._bf_answers, self._bf_session)

# ══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T('app_title'))
        self.setMinimumSize(1020,660)
        self.setStyleSheet(f'QMainWindow{{background:{D_BG};}}')
        pal=self.palette(); pal.setColor(QPalette.Window,QColor(L_BG)); self.setPalette(pal)
        QApplication.setStyle('Fusion')

        self.stack=QStackedWidget(); self.setCentralWidget(self.stack)

        # IQ data store (untuk full analysis saat BF selesai)
        self._iq_store = {'answers':None,'session':None}

        self.home  = HomePage(on_iq=self._go_iq, on_bigfive=self._go_bf)
        self.iq_q  = IQQuestionPage(on_finish=self._iq_done, on_home=self._go_home)
        self.iq_r  = IQResultPage(on_restart=self._iq_restart, on_home=self._go_home)
        self.bf_q  = BFQuestionPage(on_finish=self._bf_done, on_home=self._go_home)
        self.bf_r  = BFResultPage(on_restart=self._bf_restart, on_home=self._go_home,
                                   get_iq_data_fn=self._get_iq_store)

        for w in [self.home,self.iq_q,self.iq_r,self.bf_q,self.bf_r]:
            self.stack.addWidget(w)

        LANG_BUS.changed.connect(self._on_lang_changed)

    def _get_iq_store(self):
        if self._iq_store['answers'] is not None:
            return self._iq_store
        return None

    def _go_home(self):  self.stack.setCurrentIndex(0)
    def _go_iq(self):    self.iq_q.start_session(); self.stack.setCurrentIndex(1)
    def _go_bf(self):    self.bf_q.start_session(); self.stack.setCurrentIndex(3)

    def _iq_done(self, ans, ses):
        self._iq_store = {'answers':ans,'session':ses}
        bf_scores = self.bf_r.get_bf_scores()
        self.iq_r.load(ans, ses, bf_scores=bf_scores)
        self.stack.setCurrentIndex(2)

    def _iq_restart(self): self.iq_q.start_session(); self.stack.setCurrentIndex(1)

    def _bf_done(self, ans, ses):
        self.bf_r.load(ans, ses)
        self.stack.setCurrentIndex(4)
        # Also refresh IQ result if available
        if self._iq_store['answers'] is not None:
            bf_scores = compute_bf_scores(ans, ses)
            self.iq_r.load(self._iq_store['answers'], self._iq_store['session'],
                           bf_scores=bf_scores)

    def _bf_restart(self): self.bf_q.start_session(); self.stack.setCurrentIndex(3)

    def _on_lang_changed(self, lang):
        self.setWindowTitle(T('app_title'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    _init_lang_bus()   # buat LANG_BUS setelah QApplication
    _import_engine()   # safe to import now — QApplication exists
    w = MainWindow(); w.show()
    sys.exit(app.exec_())