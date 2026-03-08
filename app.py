import sys, json, math, random, os, io
from datetime import datetime
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QFrame,
    QButtonGroup, QSizePolicy, QFileDialog, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty,
    QParallelAnimationGroup, QSequentialAnimationGroup, pyqtSignal
)
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QPalette, QPolygon, QLinearGradient
from PyQt5.QtCore import QPoint

# reportlab for PDF export
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
with open('processed/norms.json', encoding='utf-8') as f:
    NORMS_DATA = json.load(f)
with open('processed/clusters.json', encoding='utf-8') as f:
    CLUSTERS = json.load(f)
with open('processed/iq_norms.json', encoding='utf-8') as f:
    IQ_NORMS_DATA = json.load(f)

NORMS        = NORMS_DATA['norms']
POP_STAT     = NORMS_DATA['stats']
IQ_NORMS     = IQ_NORMS_DATA['norms']
IQ_STATS     = IQ_NORMS_DATA['stats']
IQ_SCORE_MAP = IQ_NORMS_DATA['iq_score_map']

# ══════════════════════════════════════════════════════════════
# DUAL-TONE PALETTE
# Sidebar/header: dark slate  |  Content area: warm off-white
# ══════════════════════════════════════════════════════════════
# Dark side
D_BG       = '#1e2130'   # sidebar / header bg
D_BG2      = '#262b3d'   # card on dark
D_BORDER   = '#353a52'   # border on dark
D_TEXT     = '#e8eaf2'   # text on dark
D_MUTED    = '#7b82a0'   # muted on dark

# Light side (content area)
L_BG       = '#f5f6fa'   # main content bg
L_SURFACE  = '#ffffff'   # card on light
L_BORDER   = '#e2e4ee'   # border on light
L_TEXT     = '#1e2130'   # text on light
L_MUTED    = '#8890aa'   # muted on light

# Accent
GOLD       = '#f5a623'
GOLD_LIGHT = '#fff3dc'
GREEN      = '#27ae60'
RED        = '#e74c3c'
BLUE       = '#3b82f6'
PURPLE     = '#8b5cf6'
ORANGE     = '#f97316'

# Trait colors
TRAITS       = ['O','C','E','A','N']
TRAIT_NAMES  = {'O':'Openness','C':'Conscientiousness','E':'Extraversion','A':'Agreeableness','N':'Neuroticism'}
TRAIT_COLORS = {'O':'#f97316','C':'#3b82f6','E':'#8b5cf6','A':'#27ae60','N':'#e74c3c'}
TRAIT_LOW    = {'O':'Konvensional','C':'Fleksibel','E':'Introvert','A':'Kompetitif','N':'Stabil'}
TRAIT_HIGH   = {'O':'Imajinatif','C':'Terorganisir','E':'Ekstrovert','A':'Kooperatif','N':'Sensitif'}

CAT_COLORS = {
    'Deret Angka':    '#f97316',
    'Analogi Verbal': '#8b5cf6',
    'Logika':         '#3b82f6',
    'Numerik':        '#27ae60',
    'Pola Visual':    '#f5a623',
}

IQ_CATEGORIES_LIST = ['Deret Angka','Analogi Verbal','Logika','Numerik','Pola Visual']

IQ_CATEGORY_TABLE = [
    (130, 'Very Superior',  '#f5a623'),
    (120, 'Superior',       '#27ae60'),
    (110, 'High Average',   '#3b82f6'),
    (90,  'Average',        '#8b5cf6'),
    (80,  'Low Average',    '#f97316'),
    (70,  'Below Average',  '#e74c3c'),
    (0,   'Well Below Avg', '#e74c3c'),
]

# ══════════════════════════════════════════════════════════════
# QUESTION POOLS (same as before)
# ══════════════════════════════════════════════════════════════
BF_QUESTION_POOL = [
    ('O','Saya selalu ingin tahu tentang berbagai hal dan menikmati belajar hal baru.',False),
    ('O','Saya suka berimajinasi dan memiliki kehidupan batin yang kaya.',False),
    ('O','Saya lebih suka rutinitas yang sudah terbukti daripada mencoba cara baru.',True),
    ('O','Saya mudah terpesona oleh seni, musik, atau karya kreatif.',False),
    ('O','Saya tertarik pada topik-topik abstrak dan filosofis.',False),
    ('O','Saya memiliki imajinasi yang vivid dan aktif.',False),
    ('O','Saya tidak terlalu tertarik pada seni atau sastra.',True),
    ('O','Saya menikmati memikirkan teori dan ide-ide yang kompleks.',False),
    ('O','Saya jarang mencari pengalaman baru atau tidak biasa.',True),
    ('O','Saya mudah menyadari keindahan dalam hal-hal di sekitar saya.',False),
    ('C','Saya selalu menyelesaikan tugas sesuai rencana yang telah saya buat.',False),
    ('C','Saya cenderung rapi dan terorganisir dalam keseharian.',False),
    ('C','Saya sering menunda-nunda pekerjaan yang harus diselesaikan.',True),
    ('C','Saya mempertimbangkan konsekuensi secara matang sebelum bertindak.',False),
    ('C','Saya bekerja keras untuk mencapai tujuan saya.',False),
    ('C','Saya membuat rencana dan mengikutinya dengan disiplin.',False),
    ('C','Saya sering lupa menaruh barang-barang saya.',True),
    ('C','Saya sangat teliti dalam segala hal yang saya lakukan.',False),
    ('C','Saya kadang bertindak tanpa berpikir panjang terlebih dahulu.',True),
    ('C','Saya memastikan semua tugas selesai sebelum beristirahat.',False),
    ('E','Saya merasa bersemangat dan penuh energi ketika berkumpul dengan banyak orang.',False),
    ('E','Saya mudah akrab dengan orang-orang yang baru saya temui.',False),
    ('E','Saya lebih suka menghabiskan waktu sendirian daripada di keramaian.',True),
    ('E','Saya sering menjadi pusat perhatian dalam suatu kelompok.',False),
    ('E','Saya terasa hidup dan bersemangat ketika berada di lingkungan sosial.',False),
    ('E','Saya mudah memulai percakapan dengan orang yang belum saya kenal.',False),
    ('E','Saya merasa lelah setelah terlalu banyak berinteraksi sosial.',True),
    ('E','Saya menikmati menjadi bagian dari kelompok besar.',False),
    ('E','Saya lebih suka mendengarkan daripada berbicara dalam diskusi kelompok.',True),
    ('E','Saya merasa bersemangat dan antusias dalam situasi baru.',False),
    ('A','Saya peduli dengan perasaan orang lain dan mudah berempati.',False),
    ('A','Saya suka membantu orang lain meskipun tidak ada manfaat langsung bagi saya.',False),
    ('A','Saya kadang sulit mempercayai motivasi di balik tindakan orang lain.',True),
    ('A','Saya menghindari konflik dan mencari jalan damai dalam perselisihan.',False),
    ('A','Saya bersikap lemah lembut dan penuh perhatian kepada orang di sekitar saya.',False),
    ('A','Saya percaya bahwa orang pada dasarnya memiliki niat baik.',False),
    ('A','Saya terkadang terasa dingin dan tidak peduli pada masalah orang lain.',True),
    ('A','Saya mudah memaafkan orang yang telah menyakiti saya.',False),
    ('A','Saya lebih mementingkan kepentingan diri sendiri dibanding orang lain.',True),
    ('A','Saya berusaha membuat orang lain merasa nyaman saat bersama saya.',False),
    ('N','Saya sering merasa cemas atau khawatir tanpa alasan yang jelas.',False),
    ('N','Suasana hati saya bisa berubah-ubah dengan cukup cepat.',False),
    ('N','Saya cenderung tetap tenang bahkan dalam situasi yang menegangkan.',True),
    ('N','Saya mudah merasa sedih atau tertekan.',False),
    ('N','Saya sering merasa tidak yakin dengan keputusan yang saya buat.',False),
    ('N','Saya mudah merasa frustrasi atau kesal saat segala sesuatu tidak berjalan lancar.',False),
    ('N','Saya jarang merasa sedih atau murung.',True),
    ('N','Saya sering merasa tertekan oleh tuntutan kehidupan sehari-hari.',False),
    ('N','Saya relatif stabil secara emosional dan tidak mudah terguncang.',True),
    ('N','Saya kadang merasa hidup saya tidak terkendali.',False),
]

IQ_QUESTION_POOL = [
    {'category':'Deret Angka','difficulty':1,'q':'Lanjutkan deret berikut:\n2, 4, 6, 8, __','opts':['9','10','12','14'],'ans':1,'explanation':'Deret aritmetika +2. Setelah 8 adalah 10.'},
    {'category':'Deret Angka','difficulty':2,'q':'Lanjutkan deret berikut:\n1, 4, 9, 16, 25, __','opts':['30','36','34','32'],'ans':1,'explanation':'Deret kuadrat sempurna: 1²,2²,3²,4²,5²,6²=36.'},
    {'category':'Deret Angka','difficulty':3,'q':'Lanjutkan deret berikut:\n2, 4, 8, 16, __','opts':['24','32','28','30'],'ans':1,'explanation':'Deret geometri ×2. 16×2=32.'},
    {'category':'Deret Angka','difficulty':3,'q':'Lanjutkan deret berikut:\n1, 1, 2, 3, 5, 8, __','opts':['11','12','13','14'],'ans':2,'explanation':'Fibonacci: setiap suku = jumlah dua sebelumnya. 5+8=13.'},
    {'category':'Deret Angka','difficulty':4,'q':'Lanjutkan deret berikut:\n3, 6, 11, 18, 27, __','opts':['36','38','40','35'],'ans':1,'explanation':'Selisih: +3,+5,+7,+9,+11. Jadi 27+11=38.'},
    {'category':'Deret Angka','difficulty':5,'q':'Lanjutkan deret berikut:\n2, 6, 12, 20, 30, __','opts':['40','42','44','45'],'ans':1,'explanation':'Pola: n×(n+1). Suku ke-6: 6×7=42.'},
    {'category':'Deret Angka','difficulty':6,'q':'Lanjutkan deret berikut:\n1, 3, 7, 13, 21, 31, __','opts':['40','41','43','45'],'ans':2,'explanation':'Selisih +2,+4,+6,+8,+10,+12. Jadi 31+12=43.'},
    {'category':'Deret Angka','difficulty':7,'q':'Lanjutkan deret berikut:\n2, 3, 5, 8, 13, 21, __','opts':['32','33','34','35'],'ans':2,'explanation':'Fibonacci-like: 13+21=34.'},
    {'category':'Analogi Verbal','difficulty':1,'q':'Panas adalah lawan dari dingin.\nTerang adalah lawan dari __','opts':['Siang','Gelap','Malam','Redup'],'ans':1,'explanation':'Lawan dari terang adalah gelap (antonim langsung).'},
    {'category':'Analogi Verbal','difficulty':2,'q':'Dokter : Rumah Sakit = Guru : __','opts':['Kantor','Perpustakaan','Sekolah','Studio'],'ans':2,'explanation':'Dokter bekerja di RS, Guru bekerja di Sekolah.'},
    {'category':'Analogi Verbal','difficulty':2,'q':'Burung : Terbang = Ikan : __','opts':['Berlari','Berenang','Melompat','Merayap'],'ans':1,'explanation':'Burung terbang, ikan berenang.'},
    {'category':'Analogi Verbal','difficulty':3,'q':'Buku : Perpustakaan = Lukisan : __','opts':['Toko','Museum','Galeri','Gudang'],'ans':2,'explanation':'Buku di Perpustakaan, Lukisan di Galeri.'},
    {'category':'Analogi Verbal','difficulty':4,'q':'Penulis : Novel = Komposer : __','opts':['Buku','Simfoni','Lukisan','Film'],'ans':1,'explanation':'Penulis → Novel, Komposer → Simfoni.'},
    {'category':'Analogi Verbal','difficulty':5,'q':'Roti : Tepung = Kain : __','opts':['Baju','Benang','Kapas','Jarum'],'ans':1,'explanation':'Roti dibuat dari Tepung, Kain dari Benang.'},
    {'category':'Analogi Verbal','difficulty':6,'q':'Desibel : Suara = Richter : __','opts':['Angin','Gempa bumi','Tekanan','Cahaya'],'ans':1,'explanation':'Desibel mengukur Suara, Richter mengukur Gempa.'},
    {'category':'Analogi Verbal','difficulty':7,'q':'Anemia : Darah = Osteoporosis : __','opts':['Otot','Kulit','Tulang','Saraf'],'ans':2,'explanation':'Anemia memengaruhi Darah, Osteoporosis memengaruhi Tulang.'},
    {'category':'Logika','difficulty':1,'q':'Semua kucing adalah hewan.\nBeberapa hewan adalah predator.\nKesimpulan yang PASTI benar:','opts':['Semua kucing adalah predator','Beberapa kucing mungkin adalah predator','Tidak ada kucing yang predator','Semua predator adalah kucing'],'ans':1,'explanation':'"Beberapa hewan predator" tidak menentukan apakah kucing termasuk, sehingga hanya "mungkin" yang valid.'},
    {'category':'Logika','difficulty':2,'q':'Jika hari hujan, maka jalanan basah.\nJalanan tidak basah. Kesimpulan:','opts':['Hari hujan','Hari tidak hujan','Jalanan kering karena angin','Tidak dapat disimpulkan'],'ans':1,'explanation':'Modus tollens: jika P→Q dan bukan Q, maka bukan P.'},
    {'category':'Logika','difficulty':2,'q':'A lebih tua dari B. B lebih tua dari C. D lebih muda dari C.\nSiapa yang paling tua?','opts':['B','C','A','D'],'ans':2,'explanation':'Urutan: A>B>C>D. Jadi A paling tua.'},
    {'category':'Logika','difficulty':3,'q':'Dalam 5 hari ke depan, Andi berolahraga setiap hari ganjil (hari ke-1,3,5).\nBerapa total hari ia berolahraga?','opts':['2 hari','3 hari','4 hari','5 hari'],'ans':1,'explanation':'Hari ganjil dari 1-5: hari ke-1,3,5 = 3 hari.'},
    {'category':'Logika','difficulty':4,'q':'Semua manajer adalah karyawan.\nBeberapa karyawan adalah perempuan.\nKesimpulan yang PASTI benar:','opts':['Semua manajer adalah perempuan','Beberapa manajer adalah perempuan','Tidak ada manajer yang perempuan','Beberapa karyawan adalah manajer'],'ans':3,'explanation':'Karena semua manajer adalah karyawan, beberapa karyawan (para manajer) adalah manajer.'},
    {'category':'Logika','difficulty':5,'q':'Jika semua A adalah B, dan tidak ada B yang C,\nmaka kesimpulan yang benar:','opts':['Beberapa A adalah C','Tidak ada A yang C','Semua C adalah A','Beberapa B adalah A'],'ans':1,'explanation':'Semua A adalah B, dan tidak ada B yang C → tidak ada A yang C.'},
    {'category':'Logika','difficulty':6,'q':'Dua kereta berangkat menuju satu sama lain.\nJarak 600 km, kecepatan 100 km/jam dan 50 km/jam.\nBerapa jam sampai bertemu?','opts':['3 jam','4 jam','5 jam','6 jam'],'ans':1,'explanation':'Kecepatan gabungan=150 km/jam. 600/150=4 jam.'},
    {'category':'Logika','difficulty':7,'q':'5 orang duduk berurutan. A di kiri B. C di antara D dan E.\nD paling kiri. Siapa di posisi tengah (ke-3)?','opts':['A','B','E','C'],'ans':2,'explanation':'Urutan: D,C,E,A,B. Posisi ke-3 = E.'},
    {'category':'Numerik','difficulty':1,'q':'Berapa nilai dari 15 × 4?','opts':['50','55','60','65'],'ans':2,'explanation':'15 × 4 = 60.'},
    {'category':'Numerik','difficulty':2,'q':'Sebuah persegi memiliki keliling 36 cm. Berapa luasnya?','opts':['72 cm2','81 cm2','64 cm2','49 cm2'],'ans':1,'explanation':'Sisi=36/4=9. Luas=9x9=81 cm2.'},
    {'category':'Numerik','difficulty':2,'q':'Jika 20% dari X adalah 50, maka X adalah __','opts':['200','250','300','150'],'ans':1,'explanation':'20% × X = 50 → X = 50/0.2 = 250.'},
    {'category':'Numerik','difficulty':3,'q':'Sebuah kereta menempuh 300 km dalam 4 jam.\nBerapa kecepatan rata-ratanya?','opts':['65 km/jam','70 km/jam','75 km/jam','80 km/jam'],'ans':2,'explanation':'Kecepatan = 300/4 = 75 km/jam.'},
    {'category':'Numerik','difficulty':4,'q':'Sebuah toko memberi diskon 30%. Harga asli Rp200.000.\nBerapa harga setelah diskon?','opts':['Rp130.000','Rp140.000','Rp150.000','Rp160.000'],'ans':1,'explanation':'Diskon=30%×200.000=60.000. Harga=200.000-60.000=140.000.'},
    {'category':'Numerik','difficulty':5,'q':'Rasio pria:wanita dalam kelas adalah 3:2, total 40 siswa.\nBerapa jumlah wanita?','opts':['14','16','18','20'],'ans':1,'explanation':'Wanita = 2/5 × 40 = 16.'},
    {'category':'Numerik','difficulty':6,'q':'Angka mana yang merupakan bilangan prima?','opts':['51','57','59','63'],'ans':2,'explanation':'51=3×17, 57=3×19, 63=7×9. Hanya 59 yang prima.'},
    {'category':'Numerik','difficulty':7,'q':'Pipa mengisi kolam dalam 6 jam.\nPipa lain menguras dalam 9 jam.\nJika keduanya aktif, berapa jam kolam penuh?','opts':['14 jam','16 jam','18 jam','20 jam'],'ans':2,'explanation':'Net per jam: 1/6-1/9=1/18. Total=18 jam.'},
    {'category':'Pola Visual','difficulty':1,'q':'Jika segitiga=3 sisi, segiempat=4 sisi, pentagon=5 sisi,\nmaka oktagon memiliki berapa sisi?','opts':['6','7','8','9'],'ans':2,'explanation':'Oktagon (octa=8) memiliki 8 sisi.'},
    {'category':'Pola Visual','difficulty':2,'q':'Sebuah jam menunjukkan pukul 3:00.\nBerapa derajat sudut antara jarum jam dan jarum menit?','opts':['60 derajat','75 derajat','90 derajat','120 derajat'],'ans':2,'explanation':'Pukul 3:00, jarum jam di angka 3 = 90 derajat dari angka 12.'},
    {'category':'Pola Visual','difficulty':2,'q':'Dalam pola: Lingkaran putih, Hitam, Putih,Putih, Hitam, Putih,Putih,Putih, Hitam\nBerapa lingkaran putih sebelum hitam berikutnya?','opts':['3','4','5','6'],'ans':1,'explanation':'Pola jumlah putih sebelum hitam: 1,2,3,4... Berikutnya ada 4.'},
    {'category':'Pola Visual','difficulty':3,'q':'Pola angka dalam magic square 3x3:\n2  7  6\n9  5  1\n4  3  ?\nBerapa nilai "?"','opts':['7','8','9','6'],'ans':1,'explanation':'Magic square: setiap baris/kolom berjumlah 15. Kolom kanan: 6+1+?=15 → ?=8.'},
    {'category':'Pola Visual','difficulty':4,'q':'Sebuah kubus dipotong menjadi 27 kubus kecil (3x3x3).\nBerapa kubus kecil yang tidak memiliki sisi terekspos?','opts':['0','1','2','3'],'ans':1,'explanation':'Hanya 1 kubus di tengah yang tidak terekspos di sisi manapun.'},
    {'category':'Pola Visual','difficulty':5,'q':'Urutan bentuk:\nSegitiga, Kotak, Segitiga-Segitiga, Kotak-Kotak, Segitiga x3, Kotak x3, __','opts':['Segitiga x4','Kotak x4','Segitiga-Kotak','Kotak-Segitiga'],'ans':1,'explanation':'Pola bergantian segitiga-kotak bertambah 1. Setelah Kotak x3 adalah Segitiga x4.'},
    {'category':'Pola Visual','difficulty':6,'q':'Persegi panjang 8x6 dibagi menjadi persegi-persegi kecil 2x2.\nBerapa banyak persegi kecil?','opts':['10','12','14','16'],'ans':1,'explanation':'Horizontal: 8/2=4, Vertikal: 6/2=3. Total=4x3=12.'},
    {'category':'Pola Visual','difficulty':7,'q':'Bayangan cermin dari "3 6 9" adalah __','opts':['9 6 3','6 9 3','3 9 6','E 9 E'],'ans':0,'explanation':'Bayangan cermin membalik urutan: "3 6 9" menjadi "9 6 3".'},
]

IQ_POOL_BY_CAT = {cat: sorted([q for q in IQ_QUESTION_POOL if q['category']==cat], key=lambda x: x['difficulty'])
                  for cat in IQ_CATEGORIES_LIST}

# ══════════════════════════════════════════════════════════════
# SESSION & SCORING HELPERS
# ══════════════════════════════════════════════════════════════
def make_iq_session():
    session = []
    for cat in IQ_CATEGORIES_LIST:
        pool = IQ_POOL_BY_CAT[cat][:]
        random.shuffle(pool)
        picked = sorted(pool[:8], key=lambda q: q['difficulty'])
        session.extend(picked)
    return session

def make_bf_session():
    by_trait = {t: [q for q in BF_QUESTION_POOL if q[0]==t] for t in TRAITS}
    session = []
    for t in TRAITS:
        random.shuffle(by_trait[t])
        session.extend(by_trait[t])
    random.shuffle(session)
    return session

def score_to_iq(correct, total):
    pct  = correct/total*100
    key  = str(min(100, max(0, round(pct))))
    pctile = IQ_NORMS.get(key, 50.0)
    iq   = IQ_SCORE_MAP[min(100,max(0,round(pctile)))]
    label, color = 'Average', PURPLE
    for threshold, lbl, col in IQ_CATEGORY_TABLE:
        if iq >= threshold:
            label, color = lbl, col; break
    desc_map = {
        'Very Superior': 'Kecerdasan sangat luar biasa — berada di 2% teratas populasi.',
        'Superior':      'Kecerdasan di atas rata-rata yang signifikan.',
        'High Average':  'Kecerdasan di atas rata-rata umum.',
        'Average':       'Kecerdasan rata-rata — mayoritas populasi berada di rentang ini.',
        'Low Average':   'Kecerdasan sedikit di bawah rata-rata.',
        'Below Average': 'Kecerdasan di bawah rata-rata.',
        'Well Below Avg':'Kecerdasan jauh di bawah rata-rata.',
    }
    return iq, label, color, desc_map.get(label,''), round(pctile)

def get_percentile(trait, score):
    return NORMS[trait].get(str(min(100,max(0,round(score)))), 50.0)

def compute_bf_scores(answers, session):
    raw={t:0 for t in TRAITS}; cnt={t:0 for t in TRAITS}
    for i,(trait,_,reverse) in enumerate(session):
        a=answers[i]
        if a is None: continue
        v=(6-a) if reverse else a
        raw[trait]+=v; cnt[trait]+=1
    return {t: round((raw[t]/(cnt[t]*5))*100) if cnt[t]>0 else 50 for t in TRAITS}

def get_cluster(scores):
    best,best_d=CLUSTERS[0],float('inf')
    for c in CLUSTERS:
        d=sum((scores[k]-c[k])**2 for k in TRAITS)**0.5
        if d<best_d: best_d=d; best=c
    return best

def generate_bf_insight(scores, pcts):
    top=max(TRAITS, key=lambda k: pcts[k])
    parts=[f"Dimensi {TRAIT_NAMES[top]}-mu berada di persentil ke-{round(pcts[top])}, lebih tinggi dari {round(pcts[top])}% dari {NORMS_DATA['n_population']:,} responden dataset."]
    if scores['O']>=65 and scores['C']>=55: parts.append("Gaya belajarmu exploratory-structured — kamu menikmati eksplorasi ide sambil tetap butuh kerangka yang jelas.")
    elif scores['O']>=65: parts.append("Kamu self-directed learner yang belajar terbaik melalui rasa ingin tahu mandiri.")
    elif scores['C']>=65: parts.append("Kamu systematic learner — paling efektif dengan jadwal dan target yang terstruktur.")
    if scores['E']>=65: parts.append("Produktivitasmu meningkat saat berkolaborasi — group study dan diskusi sangat cocok.")
    elif scores['E']<40: parts.append("Kamu bekerja paling baik dalam ketenangan — sesi belajar mandiri lebih efektif bagimu.")
    if scores['N']>=65: parts.append("Sensitivitas stresmu lebih tinggi dari rata-rata — mindfulness dan journaling bisa sangat membantu.")
    elif scores['N']<35: parts.append("Ketahanan emosionalmu di atas rata-rata populasi — kamu mampu mengelola tekanan dengan baik.")
    return " ".join(parts)

# ══════════════════════════════════════════════════════════════
# PDF EXPORT
# ══════════════════════════════════════════════════════════════
def export_pdf(path, iq_data, bf_data):
    """
    iq_data: {answers, session, iq, label, color_hex, percentile, correct, total}
    bf_data: {answers, session, scores, pcts, cluster}
    """
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []
    W = A4[0] - 40*mm

    def s(name, **kw):
        base = getSampleStyleSheet()
        if name in base: b = base[name]
        else: b = base['Normal']
        return ParagraphStyle(name+'_custom', parent=b, **kw)

    title_s   = s('Title',    fontSize=22, textColor=colors.HexColor('#1e2130'), spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_s     = s('Normal',   fontSize=11, textColor=colors.HexColor('#7b82a0'), spaceAfter=16, alignment=TA_CENTER)
    h1_s      = s('Heading1', fontSize=14, textColor=colors.HexColor('#1e2130'), spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold')
    h2_s      = s('Heading2', fontSize=11, textColor=colors.HexColor('#3b82f6'), spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
    body_s    = s('Normal',   fontSize=10, textColor=colors.HexColor('#2d3142'), leading=15, spaceAfter=6)
    muted_s   = s('Normal',   fontSize=9,  textColor=colors.HexColor('#8890aa'), leading=13, spaceAfter=4)
    correct_s = s('Normal',   fontSize=10, textColor=colors.HexColor('#27ae60'), leading=13)
    wrong_s   = s('Normal',   fontSize=10, textColor=colors.HexColor('#e74c3c'), leading=13)
    exp_s     = s('Normal',   fontSize=9,  textColor=colors.HexColor('#f5a623'), leading=13, spaceAfter=8)

    # ── Cover ──
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("Laporan Hasil Assessment", title_s))
    story.append(Paragraph(f"Digenerate pada {datetime.now().strftime('%d %B %Y, %H:%M')}", sub_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor('#e2e4ee'), spaceAfter=12))

    # ── IQ Summary ──
    story.append(Paragraph("A. Hasil Tes IQ", h1_s))
    iq  = iq_data['iq']
    lbl = iq_data['label']
    pct = iq_data['percentile']
    cor = iq_data['correct']
    tot = iq_data['total']

    iq_table_data = [
        ['Estimasi IQ', 'Kategori', 'Persentil', 'Skor Mentah'],
        [str(iq),       lbl,        f'{pct}th',  f'{cor}/{tot}'],
    ]
    tbl = Table(iq_table_data, colWidths=[W/4]*4)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e2130')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 10),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f6fa'), colors.white]),
        ('FONTSIZE',   (0,1), (-1,-1), 11),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e4ee')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 4*mm))

    # Category breakdown
    story.append(Paragraph("Rincian per Kategori:", h2_s))
    cats = {}
    for i,q in enumerate(iq_data['session']):
        c=q['category']
        if c not in cats: cats[c]={'correct':0,'total':0}
        cats[c]['total']+=1
        if iq_data['answers'][i]==q['ans']: cats[c]['correct']+=1

    cat_rows = [['Kategori','Benar','Total','%']]
    for cat,d in cats.items():
        cat_rows.append([cat, str(d['correct']), str(d['total']), f"{d['correct']/d['total']*100:.0f}%"])
    cat_tbl = Table(cat_rows, colWidths=[W*0.5, W*0.15, W*0.15, W*0.2])
    cat_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#262b3d')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f6fa'), colors.white]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#e2e4ee')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(cat_tbl)

    # ── IQ Answer Review ──
    story.append(PageBreak())
    story.append(Paragraph("B. Review Jawaban IQ", h1_s))

    for i, q in enumerate(iq_data['session']):
        ua  = iq_data['answers'][i]
        ca  = q['ans']
        ok  = (ua == ca)
        icon = '[BENAR]' if ok else '[SALAH]'
        col  = colors.HexColor('#27ae60') if ok else colors.HexColor('#e74c3c')

        # Question header row
        q_row = [[
            Paragraph(f"<b>{i+1}. {q['category']}</b>", muted_s),
            Paragraph(f"<b>{icon}</b>", ParagraphStyle('ic', fontSize=9, textColor=col, fontName='Helvetica-Bold')),
        ]]
        q_hdr = Table(q_row, colWidths=[W*0.85, W*0.15])
        q_hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f1f7')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (0,-1), 8),
        ]))
        story.append(q_hdr)

        story.append(Paragraph(q['q'].replace('\n',' '), body_s))

        for j, opt in enumerate(q['opts']):
            prefix = chr(65+j)
            if j == ca and j == ua:
                p = Paragraph(f"  {prefix}. {opt}  [Jawabanmu &amp; Benar]", correct_s)
            elif j == ca:
                p = Paragraph(f"  {prefix}. {opt}  [Jawaban benar]", correct_s)
            elif j == ua:
                p = Paragraph(f"  {prefix}. {opt}  [Jawabanmu]", wrong_s)
            else:
                p = Paragraph(f"  {prefix}. {opt}", muted_s)
            story.append(p)

        if 'explanation' in q:
            story.append(Paragraph(f"Penjelasan: {q['explanation']}", exp_s))
        story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor('#e2e4ee'), spaceAfter=6))

    # ── Big Five Summary ──
    if bf_data:
        story.append(PageBreak())
        story.append(Paragraph("C. Hasil Tes Kepribadian Big Five", h1_s))
        cluster = bf_data['cluster']
        story.append(Paragraph(f"<b>Archetype: {cluster['name']}</b>", h2_s))
        story.append(Paragraph(cluster.get('desc',''), body_s))
        story.append(Spacer(1,4*mm))

        trait_rows = [['Dimensi','Skor','Persentil','Posisi']]
        for t in TRAITS:
            sc = bf_data['scores'][t]
            p  = round(bf_data['pcts'][t])
            pos = 'Tinggi' if sc>=65 else ('Rendah' if sc<40 else 'Sedang')
            trait_rows.append([TRAIT_NAMES[t], f'{sc}/100', f'{p}th', pos])
        trait_tbl = Table(trait_rows, colWidths=[W*0.4, W*0.15, W*0.2, W*0.25])
        trait_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1e2130')),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 10),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.HexColor('#f5f6fa'), colors.white]),
            ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e2e4ee')),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        story.append(trait_tbl)

    story.append(Spacer(1,8*mm))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor('#e2e4ee')))
    story.append(Paragraph("Laporan ini dibuat oleh aplikasi Assessment IQ & Kepribadian berbasis dataset IPIP Big Five dan Open Psychometrics IQ Alpha.", muted_s))

    doc.build(story)

# ══════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════
class AnimatedBar(QWidget):
    def __init__(self, color, pop_pct=0, parent=None):
        super().__init__(parent)
        self.color=QColor(color); self.pop_pct=pop_pct; self._value=0
        self.setFixedHeight(8); self.setMinimumWidth(200)

    def get_value(self): return self._value
    def set_value(self,v): self._value=v; self.update()
    value=pyqtProperty(float,get_value,set_value)

    def animate_to(self,target):
        self.anim=QPropertyAnimation(self,b'value')
        self.anim.setDuration(1000); self.anim.setStartValue(0.0)
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
    """Circular countdown timer widget."""
    time_up = pyqtSignal()

    def __init__(self, total_seconds=1200, parent=None):
        super().__init__(parent)
        self.total   = total_seconds
        self.remain  = total_seconds
        self.running = False
        self.setFixedSize(80, 80)
        self._timer  = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self.remain = self.total
        self.running = True
        self._timer.start(1000)
        self.update()

    def stop(self):
        self.running = False
        self._timer.stop()

    def _tick(self):
        self.remain -= 1
        self.update()
        if self.remain <= 0:
            self.stop()
            self.time_up.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        cx, cy, R = w//2, w//2, w//2 - 6

        # Background circle
        p.setPen(QPen(QColor(L_BORDER), 5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-R, cy-R, R*2, R*2)

        # Progress arc
        pct = self.remain / self.total
        is_urgent = self.remain <= 120  # last 2 minutes = red
        arc_color = QColor(RED) if is_urgent else QColor(BLUE)
        p.setPen(QPen(arc_color, 5, Qt.SolidLine, Qt.RoundCap))
        span = int(pct * 360 * 16)
        p.drawArc(cx-R, cy-R, R*2, R*2, 90*16, span)

        # Text
        mins = self.remain // 60
        secs = self.remain % 60
        txt  = f'{mins:02d}:{secs:02d}'
        p.setPen(arc_color if is_urgent else QColor(L_TEXT))
        p.setFont(QFont('Segoe UI', 11, QFont.Bold))
        p.drawText(0, 0, w, w, Qt.AlignCenter, txt)
        p.end()


class RadarWidget(QWidget):
    def __init__(self, scores, pop_stats, parent=None):
        super().__init__(parent)
        self.scores=scores; self.pop_stats=pop_stats
        self.setFixedSize(280,280)
        self.setStyleSheet('background:transparent;')

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        cx,cy,R=140,140,105
        keys=['O','C','E','A','N']; n=len(keys)
        angles=[(math.pi*2*i/n)-math.pi/2 for i in range(n)]

        for g in range(1,6):
            r=R*g/5
            pts=[(int(cx+r*math.cos(a)),int(cy+r*math.sin(a))) for a in angles]
            p.setPen(QPen(QColor(200,205,220,160),1)); p.setBrush(Qt.NoBrush)
            for i in range(n): p.drawLine(pts[i][0],pts[i][1],pts[(i+1)%n][0],pts[(i+1)%n][1])

        p.setPen(QPen(QColor(200,205,220,120),1))
        for a in angles: p.drawLine(cx,cy,int(cx+R*math.cos(a)),int(cy+R*math.sin(a)))

        pop_pts=[QPoint(int(cx+(R*self.pop_stats[k]['mean']/100)*math.cos(angles[i])),
                        int(cy+(R*self.pop_stats[k]['mean']/100)*math.sin(angles[i])))
                 for i,k in enumerate(keys)]
        p.setPen(QPen(QColor(150,155,170,120),1,Qt.DashLine))
        p.setBrush(QColor(150,155,170,20))
        p.drawPolygon(QPolygon(pop_pts))

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

        # Header
        self._header=QFrame()
        status_color=GREEN if is_correct else RED
        self._header.setStyleSheet(
            f'background:{L_BG};border:1px solid {L_BORDER};border-radius:8px;'
        )
        hl=QHBoxLayout(self._header); hl.setContentsMargins(12,8,12,8)

        num=QLabel(f'{number}'); num.setStyleSheet(f'color:{L_MUTED};font-size:11px;min-width:22px;')
        short_q=question['q'].replace('\n',' ')
        if len(short_q)>62: short_q=short_q[:59]+'…'
        ql=QLabel(short_q); ql.setStyleSheet(f'color:{L_TEXT};font-size:12px;'); ql.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
        cat_c=CAT_COLORS.get(question['category'],GOLD)
        cl=QLabel(question['category'])
        cl.setStyleSheet(f'color:{cat_c};font-size:9px;border:1px solid {cat_c};padding:1px 6px;border-radius:3px;')
        sl=QLabel('✓' if is_correct else '✗')
        sl.setStyleSheet(f'color:{status_color};font-size:13px;font-weight:700;min-width:18px;')
        sl.setAlignment(Qt.AlignCenter)
        self._arrow=QLabel('▶'); self._arrow.setStyleSheet(f'color:{L_MUTED};font-size:9px;')

        hl.addWidget(num); hl.addWidget(ql); hl.addWidget(cl)
        hl.addWidget(sl); hl.addWidget(self._arrow)
        self._header.mousePressEvent=lambda _: self._toggle()
        outer.addWidget(self._header)

        # Body
        self._body=QFrame()
        self._body.setStyleSheet(
            f'background:{L_SURFACE};border:1px solid {L_BORDER};border-top:none;border-radius:0 0 8px 8px;'
        )
        bl=QVBoxLayout(self._body); bl.setContentsMargins(14,10,14,10); bl.setSpacing(6)

        fq=QLabel(question['q']); fq.setWordWrap(True)
        fq.setStyleSheet(f'color:{L_TEXT};font-size:13px;font-weight:500;')
        bl.addWidget(fq)

        for i,opt in enumerate(question['opts']):
            if i==correct_ans and i==user_ans: bg,fg,sfx=f'rgba(39,174,96,0.08)',GREEN,' ✓ Jawabanmu & Benar'
            elif i==correct_ans:               bg,fg,sfx=f'rgba(39,174,96,0.06)',GREEN,' ← Jawaban benar'
            elif i==user_ans:                  bg,fg,sfx=f'rgba(231,76,60,0.08)',RED,' ✗ Jawabanmu'
            else:                              bg,fg,sfx='transparent',L_MUTED,''
            ol=QLabel(f'{chr(65+i)}. {opt}{sfx}')
            ol.setWordWrap(True)
            ol.setStyleSheet(f'color:{fg};font-size:12px;background:{bg};padding:3px 8px;border-radius:4px;')
            bl.addWidget(ol)

        if 'explanation' in question:
            el=QLabel(f'💡  {question["explanation"]}')
            el.setWordWrap(True)
            el.setStyleSheet(f'color:{GOLD};font-size:11px;background:{GOLD_LIGHT};padding:6px 10px;border-radius:6px;')
            bl.addWidget(el)

        self._body.setVisible(False)
        outer.addWidget(self._body)

    def _toggle(self):
        self.expanded=not self.expanded
        self._body.setVisible(self.expanded)
        self._arrow.setText('▼' if self.expanded else '▶')
        self._header.setStyleSheet(
            f'background:{"#eef0f8" if self.expanded else L_BG};border:1px solid {L_BORDER};border-radius:{"8px 8px 0 0" if self.expanded else "8px"};'
        )


# ══════════════════════════════════════════════════════════════
# SHARED UI BUILDERS
# ══════════════════════════════════════════════════════════════
def lcard(title=''):
    """Light card."""
    f=QFrame(); f.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:12px;')
    l=QVBoxLayout(f); l.setContentsMargins(20,16,20,16)
    if title:
        h=QLabel(title.upper()); h.setStyleSheet(f'color:{L_MUTED};font-size:9px;font-weight:700;letter-spacing:2px;')
        l.addWidget(h)
    return f

def dark_btn(text, w=160, h=40):
    b=QPushButton(text); b.setFixedSize(w,h)
    b.setStyleSheet(f'QPushButton{{background:{D_BG};color:{D_TEXT};border:1px solid {D_BORDER};border-radius:6px;font-size:13px;font-weight:600;}} QPushButton:hover{{background:{D_BG2};}}')
    return b

def gold_btn(text, w=180, h=42):
    b=QPushButton(text); b.setFixedSize(w,h)
    b.setStyleSheet(f'QPushButton{{background:{GOLD};color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:700;}} QPushButton:hover{{background:#e8940a;}}')
    return b

def fade_anim(widget, start=0.0, end=1.0, duration=200):
    # Reuse existing effect to prevent GC killing opacity mid-animation
    eff = widget.graphicsEffect()
    if not isinstance(eff, QGraphicsOpacityEffect):
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
    eff.setOpacity(start)
    a = QPropertyAnimation(eff, b'opacity')
    a.setDuration(duration)
    a.setStartValue(start)
    a.setEndValue(end)
    a.setEasingCurve(QEasingCurve.InOutQuad)
    # Store refs on widget so Python GC doesn't destroy them before anim finishes
    widget._fade_anim = a
    widget._fade_eff  = eff
    return a


# ══════════════════════════════════════════════════════════════
# PAGE WRAPPER — dual-tone layout
# Each page has: left dark sidebar + right light content
# ══════════════════════════════════════════════════════════════
class DualPage(QWidget):
    """Base class: left dark panel (240px) + right light scroll area."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background:{L_BG};')
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Left sidebar
        self.sidebar=QWidget(); self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f'background:{D_BG};')
        self.sidebar_lay=QVBoxLayout(self.sidebar)
        self.sidebar_lay.setContentsMargins(24,32,24,32); self.sidebar_lay.setSpacing(0)
        root.addWidget(self.sidebar)

        # Right content
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet('border:none;background:transparent;')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.verticalScrollBar().setStyleSheet(
            f'QScrollBar:vertical{{background:{L_BG};width:6px;}} '
            f'QScrollBar::handle:vertical{{background:{L_BORDER};border-radius:3px;}} '
            f'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}'
        )
        self.content_w=QWidget(); self.content_w.setStyleSheet(f'background:{L_BG};')
        self.content_lay=QVBoxLayout(self.content_w)
        self.content_lay.setContentsMargins(36,36,36,36); self.content_lay.setSpacing(20)
        scroll.setWidget(self.content_w)
        root.addWidget(scroll, 1)

    def add_sidebar(self, widget): self.sidebar_lay.addWidget(widget)
    def add_sidebar_stretch(self): self.sidebar_lay.addStretch()
    def add_content(self, widget, **kw): self.content_lay.addWidget(widget, **kw)
    def add_content_stretch(self): self.content_lay.addStretch()

    def sidebar_label(self, text, size=11, bold=False, color=D_TEXT, spacing=0):
        l=QLabel(text); l.setWordWrap(True)
        weight='700' if bold else '400'
        l.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:{weight};letter-spacing:{spacing}px;background:transparent;')
        return l

    def content_label(self, text, size=13, bold=False, color=L_TEXT):
        l=QLabel(text); l.setWordWrap(True)
        weight='700' if bold else '400'
        l.setStyleSheet(f'color:{color};font-size:{size}px;font-weight:{weight};background:transparent;')
        return l


# ══════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════
class HomePage(DualPage):
    def __init__(self, on_iq, on_bigfive):
        super().__init__()
        # Sidebar
        logo=self.sidebar_label('ASSESSMENT\nPSIKOLOGIS', size=13, bold=True, color=GOLD, spacing=1)
        logo.setAlignment(Qt.AlignCenter)
        self.add_sidebar(logo)
        self.add_sidebar(self.sidebar_label('', size=1))
        self.add_sidebar_stretch()

        desc=self.sidebar_label(
            f'Berbasis {NORMS_DATA["n_population"]:,} responden\nIPIP Big Five · Kaggle\n\ndan Open Psychometrics\nIQ Alpha Dataset',
            size=11, color=D_MUTED
        )
        self.add_sidebar(desc)
        self.add_sidebar_stretch()

        ver=self.sidebar_label('v2.0', size=10, color=D_MUTED)
        self.add_sidebar(ver)

        # Content
        hello=self.content_label('Kenali Dirimu\nLebih Dalam', size=32, bold=True)
        hello.setStyleSheet(f'color:{L_TEXT};font-size:32px;font-weight:700;line-height:1.2;background:transparent;')
        self.add_content(hello)

        sub=self.content_label('Pilih jenis tes yang ingin kamu lakukan. Semua hasil dibandingkan\ndengan data populasi riil dari dataset akademik tervalidasi.', size=14, color=L_MUTED)
        self.add_content(sub)

        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f'background:{L_BORDER};')
        self.add_content(sep)

        # Card IQ
        iq_card=self._menu_card(
            '🧠', 'Tes IQ',
            '40 soal standar Mensa-style\nDeret angka, analogi verbal,\nlogika, numerik & pola visual',
            'Waktu: 20 menit total', BLUE, 'Mulai Tes IQ', on_iq
        )
        # Card BF
        bf_card=self._menu_card(
            '🎭', 'Tes Kepribadian',
            '50 soal Big Five IPIP standar\n10 soal per trait OCEAN\nHasil dengan percentile populasi',
            'Waktu: ~10 menit', GOLD, 'Mulai Tes Kepribadian', on_bigfive
        )
        row=QWidget(); row.setStyleSheet('background:transparent;')
        rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(16)
        rl.addWidget(iq_card); rl.addWidget(bf_card)
        self.add_content(row)
        self.add_content_stretch()

    def _menu_card(self, icon, title, desc, time_txt, color, btn_text, on_click):
        card=QFrame()
        card.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:14px;')
        cl=QVBoxLayout(card); cl.setContentsMargins(24,24,24,24); cl.setSpacing(10)

        icon_l=QLabel(icon); icon_l.setStyleSheet('font-size:32px;background:transparent;border:none;')
        title_l=QLabel(title); title_l.setStyleSheet(f'color:{L_TEXT};font-size:18px;font-weight:700;background:transparent;border:none;')
        desc_l=QLabel(desc); desc_l.setWordWrap(True)
        desc_l.setStyleSheet(f'color:{L_MUTED};font-size:12px;line-height:1.7;background:transparent;border:none;')
        time_l=QLabel(f'⏱  {time_txt}')
        time_l.setStyleSheet(f'color:{color};font-size:11px;font-weight:600;background:transparent;border:none;')

        btn=QPushButton(btn_text); btn.setFixedHeight(40)
        btn.setStyleSheet(f'QPushButton{{background:{color};color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:700;}} QPushButton:hover{{opacity:0.9;}}')
        btn.clicked.connect(on_click)

        cl.addWidget(icon_l); cl.addWidget(title_l); cl.addWidget(desc_l)
        cl.addWidget(time_l); cl.addStretch(); cl.addWidget(btn)
        return card


# ══════════════════════════════════════════════════════════════
# IQ QUESTION PAGE
# ══════════════════════════════════════════════════════════════
class IQQuestionPage(DualPage):
    def __init__(self, on_finish, on_home):
        super().__init__()
        self.on_finish=on_finish; self.on_home=on_home
        self.session=[]; self.answers=[]; self.current=0
        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        self.add_sidebar(self.sidebar_label('TES IQ', size=11, bold=True, color=GOLD, spacing=2))
        self.add_sidebar(QWidget())  # spacer

        self.timer_widget=CountdownTimer(1200)
        self.timer_widget.time_up.connect(self._time_up)
        timer_wrap=QWidget(); timer_wrap.setStyleSheet('background:transparent;')
        tw=QVBoxLayout(timer_wrap); tw.setAlignment(Qt.AlignCenter)
        tw.addWidget(self.timer_widget, alignment=Qt.AlignCenter)
        timer_lbl=self.sidebar_label('Sisa Waktu', size=10, color=D_MUTED)
        timer_lbl.setAlignment(Qt.AlignCenter)
        tw.addWidget(timer_lbl)
        self.add_sidebar(timer_wrap)
        self.add_sidebar_stretch()

        self.side_cat=self.sidebar_label('', size=10, color=D_MUTED)
        self.side_prog=self.sidebar_label('', size=22, bold=True, color=D_TEXT)
        self.add_sidebar(self.side_cat)
        self.add_sidebar(self.side_prog)
        self.add_sidebar_stretch()

        back_btn=QPushButton('← Beranda')
        back_btn.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;text-align:left;padding:0;}} QPushButton:hover{{color:{D_TEXT};}}')
        back_btn.clicked.connect(self._go_home)
        self.add_sidebar(back_btn)

    def _build_content(self):
        self.prog_bar=ProgressBar(BLUE)
        self.add_content(self.prog_bar)

        # Question card with fade container
        self.q_container=QWidget(); self.q_container.setStyleSheet('background:transparent;')
        qcl=QVBoxLayout(self.q_container); qcl.setContentsMargins(0,0,0,0); qcl.setSpacing(12)

        self.q_card=lcard()
        self.q_label=QLabel('...')
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(f'color:{L_TEXT};font-size:16px;font-weight:400;line-height:1.7;')
        self.q_card.layout().addWidget(self.q_label)
        qcl.addWidget(self.q_card)

        # Options
        self.opt_btns=[]
        for i in range(4):
            btn=QPushButton()
            btn.setCheckable(True); btn.setFixedHeight(48)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(self._opt_s(False))
            btn.clicked.connect(lambda _,idx=i: self._pick(idx))
            self.opt_btns.append(btn); qcl.addWidget(btn)

        self.add_content(self.q_container)

        # Nav buttons
        nav=QWidget(); nav.setStyleSheet('background:transparent;')
        nl=QHBoxLayout(nav); nl.setContentsMargins(0,0,0,0)
        self.btn_prev=dark_btn('← Kembali',w=130,h=40)
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next=gold_btn('Lanjut →',w=130,h=40)
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._next)
        nl.addWidget(self.btn_prev); nl.addStretch(); nl.addWidget(self.btn_next)
        self.add_content(nav)
        self.add_content_stretch()

    def _opt_s(self, selected):
        if selected:
            return f'QPushButton{{background:rgba(59,130,246,0.08);border:2px solid {BLUE};color:{BLUE};font-size:13px;font-weight:600;border-radius:10px;text-align:left;padding:0 16px;}} '
        return f'QPushButton{{background:{L_SURFACE};border:1px solid {L_BORDER};color:{L_TEXT};font-size:13px;border-radius:10px;text-align:left;padding:0 16px;}} QPushButton:hover{{border-color:{BLUE};background:rgba(59,130,246,0.04);}}'

    def start_session(self):
        self.session=make_iq_session()
        self.answers=[None]*len(self.session)
        self.current=0
        self.timer_widget.start()
        self._render()

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
        self.btn_next.setText('Lihat Hasil →' if self.current==n-1 else 'Lanjut →')
        self.btn_prev.setVisible(self.current>0)

        # Fade animation
        a=fade_anim(self.q_container); a.start()

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

    def _time_up(self):
        # Fill unanswered with None then submit
        self.on_finish(self.answers, self.session)

    def _go_home(self):
        self.timer_widget.stop(); self.on_home()


# ══════════════════════════════════════════════════════════════
# IQ RESULT PAGE
# ══════════════════════════════════════════════════════════════
class IQResultPage(DualPage):
    def __init__(self, on_restart, on_home):
        super().__init__()
        self.on_restart=on_restart; self.on_home=on_home
        self._last_iq=None; self._last_bf=None
        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        self.add_sidebar(self.sidebar_label('HASIL TES IQ', size=11, bold=True, color=GOLD, spacing=2))
        self.add_sidebar_stretch()

        self.side_iq=self.sidebar_label('—', size=48, bold=True, color=D_TEXT)
        self.side_iq.setAlignment(Qt.AlignCenter)
        self.side_label=self.sidebar_label('—', size=13, color=D_MUTED)
        self.side_label.setAlignment(Qt.AlignCenter)
        self.side_pct=self.sidebar_label('', size=11, color=D_MUTED)
        self.side_pct.setAlignment(Qt.AlignCenter)
        self.add_sidebar(self.side_iq)
        self.add_sidebar(self.side_label)
        self.add_sidebar(self.side_pct)
        self.add_sidebar_stretch()

        self.export_btn=QPushButton('Export PDF  ↓')
        self.export_btn.setFixedHeight(38)
        self.export_btn.setStyleSheet(f'QPushButton{{background:{GOLD};color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;}} QPushButton:hover{{background:#e8940a;}}')
        self.export_btn.clicked.connect(self._export)
        self.add_sidebar(self.export_btn)

        self.add_sidebar(QWidget())
        restart=QPushButton('Ulangi Tes IQ  ↺')
        restart.setFixedHeight(38)
        restart.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:1px solid {D_BORDER};border-radius:6px;font-size:12px;}} QPushButton:hover{{color:{D_TEXT};border-color:{D_TEXT};}}')
        restart.clicked.connect(self.on_restart)
        self.add_sidebar(restart)

        home=QPushButton('← Beranda')
        home.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;padding:8px 0;}} QPushButton:hover{{color:{D_TEXT};}}')
        home.clicked.connect(self.on_home)
        self.add_sidebar(home)

    def _build_content(self):
        # Summary row
        self.summary_row=QWidget(); self.summary_row.setStyleSheet('background:transparent;')
        self.summary_l=QHBoxLayout(self.summary_row); self.summary_l.setSpacing(12); self.summary_l.setContentsMargins(0,0,0,0)
        self.add_content(self.summary_row)

        # Breakdown
        self.breakdown_card=lcard('Rincian per Kategori')
        self.breakdown_l=QVBoxLayout(); self.breakdown_l.setSpacing(10)
        self.breakdown_card.layout().addLayout(self.breakdown_l)
        self.add_content(self.breakdown_card)

        # Accordion review
        self.review_card=lcard('Review Jawaban  ·  Klik soal untuk expand')
        self.review_l=QVBoxLayout(); self.review_l.setSpacing(0)
        self.review_card.layout().addLayout(self.review_l)
        self.add_content(self.review_card)

        # Insight
        self.insight_card=lcard()
        self.insight_card.setStyleSheet(f'background:{GOLD_LIGHT};border:1px solid #f5d88a;border-radius:12px;')
        il=self.insight_card.layout()
        il.addWidget(QLabel('⚡  Insight', styleSheet=f'color:{GOLD};font-size:10px;font-weight:700;letter-spacing:2px;background:transparent;'))
        self.insight_lbl=QLabel(); self.insight_lbl.setWordWrap(True)
        self.insight_lbl.setStyleSheet(f'color:#7a5200;font-size:13px;line-height:1.8;background:transparent;')
        il.addWidget(self.insight_lbl)
        self.add_content(self.insight_card)
        self.add_content_stretch()

    def load(self, answers, session, bf_data=None):
        self._last_iq={'answers':answers,'session':session}
        self._last_bf=bf_data

        correct=sum(1 for i,a in enumerate(answers) if a==session[i]['ans'])
        total=len(session)
        iq,label,color,desc,pctile=score_to_iq(correct,total)

        self.side_iq.setText(str(iq))
        self.side_iq.setStyleSheet(f'color:{color};font-size:48px;font-weight:700;background:transparent;')
        self.side_label.setText(label)
        self.side_pct.setText(f'Persentil ke-{pctile}')

        # Summary
        for i in range(self.summary_l.count()):
            item=self.summary_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        wrong=total-correct
        for val,lbl,col in [(correct,'Benar',GREEN),(wrong,'Salah',RED),(total,'Total Soal',BLUE)]:
            cell=QFrame(); cell.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl=QVBoxLayout(cell); cl.setAlignment(Qt.AlignCenter); cl.setContentsMargins(12,14,12,14)
            vl=QLabel(str(val)); vl.setStyleSheet(f'color:{col};font-size:26px;font-weight:700;background:transparent;'); vl.setAlignment(Qt.AlignCenter)
            ll=QLabel(lbl);      ll.setStyleSheet(f'color:{L_MUTED};font-size:11px;background:transparent;');             ll.setAlignment(Qt.AlignCenter)
            cl.addWidget(vl); cl.addWidget(ll)
            self.summary_l.addWidget(cell)

        # Breakdown
        for i in range(self.breakdown_l.count()):
            item=self.breakdown_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        cats={}
        for i,q in enumerate(session):
            c=q['category']
            if c not in cats: cats[c]={'correct':0,'total':0}
            cats[c]['total']+=1
            if answers[i]==q['ans']: cats[c]['correct']+=1

        for cat,d in cats.items():
            pct=d['correct']/d['total']*100; cc=CAT_COLORS.get(cat,GOLD)
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            hl.addWidget(QLabel(cat, styleSheet=f'color:{cc};font-size:12px;font-weight:600;background:transparent;'))
            hl.addStretch()
            hl.addWidget(QLabel(f'{d["correct"]}/{d["total"]} ({pct:.0f}%)', styleSheet=f'color:{L_MUTED};font-size:11px;background:transparent;'))
            rl.addWidget(hdr)
            bar=AnimatedBar(cc); rl.addWidget(bar)
            self.breakdown_l.addWidget(row)
            QTimer.singleShot(300, lambda b=bar,v=pct: b.animate_to(v))

        # Accordion
        for i in range(self.review_l.count()):
            item=self.review_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i,q in enumerate(session):
            self.review_l.addWidget(AccordionItem(i+1,q,answers[i],q['ans']))

        # Insight
        pop_mean=IQ_STATS['total']['mean']
        strong=max(cats,key=lambda c:cats[c]['correct']/cats[c]['total'])
        weak=min(cats,key=lambda c:cats[c]['correct']/cats[c]['total'])
        pct_c=correct/total*100
        if iq>=130: ins=f"IQ {iq} — Very Superior! Kamu menjawab benar {correct}/{total} ({pct_c:.0f}%), jauh di atas rata-rata dataset ({pop_mean:.0f}%). Kekuatan terbesar di {strong}."
        elif iq>=120: ins=f"IQ {iq} — Superior. Persentil ke-{pctile}. Kekuatan utama di {strong}."
        elif iq>=110: ins=f"IQ {iq} — High Average. Di atas rata-rata populasi. Tingkatkan {weak} untuk hasil lebih optimal."
        elif iq>=90: ins=f"IQ {iq} — Average. Paling kuat di {strong}, bisa ditingkatkan di {weak} dengan latihan rutin."
        else: ins=f"IQ {iq}. Benar {correct}/{total} soal. Latihan rutin di {weak} akan meningkatkan skormu secara nyata."
        self.insight_lbl.setText(ins)

    def _export(self):
        if not self._last_iq: return
        path,_=QFileDialog.getSaveFileName(self, 'Simpan PDF', 'hasil_assessment.pdf', 'PDF Files (*.pdf)')
        if not path: return
        try:
            export_pdf(path, self._last_iq, self._last_bf)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self,'Export Berhasil',f'PDF berhasil disimpan ke:\n{path}')
        except Exception as ex:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self,'Export Gagal',str(ex))


# ══════════════════════════════════════════════════════════════
# BF QUESTION PAGE
# ══════════════════════════════════════════════════════════════
class BFQuestionPage(DualPage):
    def __init__(self, on_finish, on_home):
        super().__init__()
        self.on_finish=on_finish; self.on_home=on_home
        self.session=[]; self.answers=[]; self.current=0
        self._build_sidebar(); self._build_content()

    def _build_sidebar(self):
        self.add_sidebar(self.sidebar_label('TES KEPRIBADIAN', size=11, bold=True, color=GOLD, spacing=1))
        self.add_sidebar_stretch()
        self.side_trait=self.sidebar_label('', size=13, bold=True, color=D_TEXT)
        self.side_prog=self.sidebar_label('', size=22, bold=True, color=D_TEXT)
        self.side_desc=self.sidebar_label('', size=10, color=D_MUTED)
        self.add_sidebar(self.side_trait); self.add_sidebar(self.side_prog); self.add_sidebar(self.side_desc)
        self.add_sidebar_stretch()
        back=QPushButton('← Beranda')
        back.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;text-align:left;padding:0;}} QPushButton:hover{{color:{D_TEXT};}}')
        back.clicked.connect(self.on_home)
        self.add_sidebar(back)

    def _build_content(self):
        self.prog_bar=ProgressBar(GOLD)
        self.add_content(self.prog_bar)

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
        sl.addWidget(QLabel('Sangat Tidak Setuju', styleSheet=f'color:{L_MUTED};font-size:10px;background:transparent;'))
        sl.addStretch()
        sl.addWidget(QLabel('Netral', styleSheet=f'color:{L_MUTED};font-size:10px;background:transparent;'))
        sl.addStretch()
        sl.addWidget(QLabel('Sangat Setuju', styleSheet=f'color:{L_MUTED};font-size:10px;background:transparent;'))
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
        self.btn_prev=dark_btn('← Kembali',w=130,h=40); self.btn_prev.clicked.connect(self._prev)
        self.btn_next=gold_btn('Lanjut →',w=130,h=40); self.btn_next.setEnabled(False); self.btn_next.clicked.connect(self._next)
        nl.addWidget(self.btn_prev); nl.addStretch(); nl.addWidget(self.btn_next)
        self.add_content(nav); self.add_content_stretch()

    def _btn_s(self, sel):
        if sel: return f'QPushButton{{background:rgba(245,166,35,0.10);border:2px solid {GOLD};color:{GOLD};font-size:15px;font-weight:700;border-radius:10px;}}'
        return f'QPushButton{{background:{L_SURFACE};border:1px solid {L_BORDER};color:{L_TEXT};font-size:15px;border-radius:10px;}} QPushButton:hover{{border-color:{GOLD};background:rgba(245,166,35,0.04);}}'

    def start_session(self):
        self.session=make_bf_session(); self.answers=[None]*len(self.session); self.current=0; self._render()

    def _render(self):
        if not self.session: return
        trait,text,_=self.session[self.current]; n=len(self.session)
        self.prog_bar.set_value((self.current+1)/n*100)
        tc=TRAIT_COLORS[trait]
        self.side_trait.setText(TRAIT_NAMES[trait])
        self.side_trait.setStyleSheet(f'color:{tc};font-size:13px;font-weight:700;background:transparent;')
        self.side_prog.setText(f'{self.current+1}/{n}')
        self.side_desc.setText(f'{TRAIT_LOW[trait]} ↔ {TRAIT_HIGH[trait]}')
        self.q_label.setText(text)
        cur=self.answers[self.current]
        for i,btn in enumerate(self.likert_btns):
            btn.setChecked(cur==i+1); btn.setStyleSheet(self._btn_s(cur==i+1))
        enabled=cur is not None
        self.btn_next.setEnabled(enabled)
        self.btn_next.setText('Lihat Hasil →' if self.current==n-1 else 'Lanjut →')
        self.btn_prev.setVisible(self.current>0)
        fade_anim(self.q_container).start()

    def _pick(self,val):
        self.answers[self.current]=val
        for i,btn in enumerate(self.likert_btns): btn.setStyleSheet(self._btn_s(i+1==val))
        self.btn_next.setEnabled(True)

    def _next(self):
        if self.answers[self.current] is None: return
        if self.current==len(self.session)-1:
            self.on_finish(self.answers,self.session); return
        self.current+=1; self._render()

    def _prev(self):
        if self.current==0: return
        self.current-=1; self._render()


# ══════════════════════════════════════════════════════════════
# BF RESULT PAGE
# ══════════════════════════════════════════════════════════════
class BFResultPage(DualPage):
    def __init__(self, on_restart, on_home):
        super().__init__()
        self.on_restart=on_restart; self.on_home=on_home
        self.bars={}
        self._build_sidebar(); self._build_content()

    def _build_sidebar(self):
        self.add_sidebar(self.sidebar_label('HASIL KEPRIBADIAN', size=11, bold=True, color=GOLD, spacing=1))
        self.add_sidebar_stretch()
        self.side_tag=self.sidebar_label('', size=9, color=D_MUTED, spacing=1)
        self.side_name=self.sidebar_label('', size=16, bold=True, color=D_TEXT)
        self.side_name.setWordWrap(True)
        self.add_sidebar(self.side_tag); self.add_sidebar(self.side_name)
        self.add_sidebar_stretch()
        restart=QPushButton('Ulangi Tes  ↺')
        restart.setFixedHeight(38)
        restart.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:1px solid {D_BORDER};border-radius:6px;font-size:12px;}} QPushButton:hover{{color:{D_TEXT};border-color:{D_TEXT};}}')
        restart.clicked.connect(self.on_restart)
        self.add_sidebar(restart)
        home=QPushButton('← Beranda')
        home.setStyleSheet(f'QPushButton{{background:transparent;color:{D_MUTED};border:none;font-size:12px;padding:8px 0;}} QPushButton:hover{{color:{D_TEXT};}}')
        home.clicked.connect(self.on_home)
        self.add_sidebar(home)

    def _build_content(self):
        # Percentile cards row
        self.pct_row=QWidget(); self.pct_row.setStyleSheet('background:transparent;')
        self.pct_l=QHBoxLayout(self.pct_row); self.pct_l.setSpacing(8); self.pct_l.setContentsMargins(0,0,0,0)
        self.pct_labels={}
        for t in TRAITS:
            cell=QFrame(); cell.setStyleSheet(f'background:{L_SURFACE};border:1px solid {L_BORDER};border-radius:10px;')
            cl=QVBoxLayout(cell); cl.setAlignment(Qt.AlignCenter); cl.setContentsMargins(8,12,8,12); cl.setSpacing(2)
            tl=QLabel(t); tl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:10px;font-weight:700;background:transparent;'); tl.setAlignment(Qt.AlignCenter)
            vl=QLabel('—'); vl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:20px;font-weight:700;background:transparent;'); vl.setAlignment(Qt.AlignCenter)
            sl=QLabel('persentil'); sl.setStyleSheet(f'color:{L_MUTED};font-size:9px;background:transparent;'); sl.setAlignment(Qt.AlignCenter)
            cl.addWidget(tl); cl.addWidget(vl); cl.addWidget(sl)
            self.pct_l.addWidget(cell); self.pct_labels[t]=vl
        self.add_content(self.pct_row)

        # Radar
        radar_card=lcard('Radar OCEAN — Kamu vs Populasi')
        self.radar_container=QVBoxLayout(); self.radar_container.setAlignment(Qt.AlignCenter)
        radar_card.layout().addLayout(self.radar_container)
        self.add_content(radar_card)

        # Trait bars
        bars_card=lcard('Skor & Posisi vs Populasi')
        self.bars_l=QVBoxLayout(); self.bars_l.setSpacing(14)
        bars_card.layout().addLayout(self.bars_l)
        self.add_content(bars_card)

        # Insight
        self.insight_card=lcard()
        self.insight_card.setStyleSheet(f'background:{GOLD_LIGHT};border:1px solid #f5d88a;border-radius:12px;')
        il=self.insight_card.layout()
        il.addWidget(QLabel('⚡  Insight', styleSheet=f'color:{GOLD};font-size:10px;font-weight:700;letter-spacing:2px;background:transparent;'))
        self.insight_lbl=QLabel(); self.insight_lbl.setWordWrap(True)
        self.insight_lbl.setStyleSheet(f'color:#7a5200;font-size:13px;line-height:1.8;background:transparent;')
        il.addWidget(self.insight_lbl)
        self.add_content(self.insight_card)
        self.add_content_stretch()

    def load(self, answers, session):
        scores=compute_bf_scores(answers,session)
        pcts={t:get_percentile(t,scores[t]) for t in TRAITS}
        cluster=get_cluster(scores)

        self.side_tag.setText(cluster.get('tag',''))
        self.side_name.setText(cluster['name'])
        for t in TRAITS: self.pct_labels[t].setText(f"{round(pcts[t])}th")

        while self.radar_container.count():
            self.radar_container.takeAt(0).widget().deleteLater()
        self.radar_container.addWidget(RadarWidget(scores,POP_STAT))

        for i in range(self.bars_l.count()):
            item=self.bars_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.bars={}
        for t in TRAITS:
            row=QWidget(); row.setStyleSheet('background:transparent;')
            rl=QVBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
            hdr=QWidget(); hdr.setStyleSheet('background:transparent;')
            hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,0,0)
            nl=QLabel(TRAIT_NAMES[t]); nl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-weight:600;font-size:13px;background:transparent;')
            pb=QLabel(f'{round(pcts[t])}th')
            pb.setStyleSheet(f'color:{GOLD};background:{GOLD_LIGHT};border:1px solid #f5d88a;padding:1px 8px;border-radius:4px;font-size:10px;font-weight:700;')
            sl=QLabel(f'{scores[t]}/100'); sl.setStyleSheet(f'color:{TRAIT_COLORS[t]};font-size:17px;font-weight:600;background:transparent;')
            hl.addWidget(nl); hl.addWidget(pb); hl.addStretch(); hl.addWidget(sl)
            rl.addWidget(hdr)
            sub=QLabel(f'{TRAIT_LOW[t]} \u2194 {TRAIT_HIGH[t]}  ·  Populasi: {round(POP_STAT[t]["mean"])}')
            sub.setStyleSheet(f'color:{L_MUTED};font-size:10px;background:transparent;')
            rl.addWidget(sub)
            bar=AnimatedBar(TRAIT_COLORS[t], POP_STAT[t]['mean']); rl.addWidget(bar)
            self.bars_l.addWidget(row); self.bars[t]=(bar,scores[t])

        self.insight_lbl.setText(generate_bf_insight(scores,pcts))
        QTimer.singleShot(300, self._anim_bars)

        # Store for potential combined export
        self._last={'answers':answers,'session':session,'scores':scores,'pcts':pcts,'cluster':cluster}

    def _anim_bars(self):
        for t,(bar,score) in self.bars.items(): bar.animate_to(score)

    def get_data(self):
        return getattr(self,'_last',None)


# ══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Assessment IQ & Kepribadian')
        self.setMinimumSize(960,640)
        self.setStyleSheet(f'QMainWindow{{background:{D_BG};}}')
        pal=self.palette()
        pal.setColor(QPalette.Window,QColor(L_BG))
        self.setPalette(pal)
        QApplication.setStyle('Fusion')

        self.stack=QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home  =HomePage(on_iq=self._go_iq, on_bigfive=self._go_bf)
        self.iq_q  =IQQuestionPage(on_finish=self._iq_done, on_home=self._go_home)
        self.iq_r  =IQResultPage(on_restart=self._iq_restart, on_home=self._go_home)
        self.bf_q  =BFQuestionPage(on_finish=self._bf_done, on_home=self._go_home)
        self.bf_r  =BFResultPage(on_restart=self._bf_restart, on_home=self._go_home)

        for w in [self.home,self.iq_q,self.iq_r,self.bf_q,self.bf_r]:
            self.stack.addWidget(w)

    def _go_home(self):  self.stack.setCurrentIndex(0)
    def _go_iq(self):    self.iq_q.start_session(); self.stack.setCurrentIndex(1)
    def _go_bf(self):    self.bf_q.start_session(); self.stack.setCurrentIndex(3)

    def _iq_done(self,ans,ses):
        self.iq_r.load(ans, ses, bf_data=self.bf_r.get_data())
        self.stack.setCurrentIndex(2)

    def _iq_restart(self):
        self.iq_q.start_session(); self.stack.setCurrentIndex(1)

    def _bf_done(self,ans,ses):
        self.bf_r.load(ans,ses); self.stack.setCurrentIndex(4)

    def _bf_restart(self):
        self.bf_q.start_session(); self.stack.setCurrentIndex(3)


if __name__=='__main__':
    app=QApplication(sys.argv)
    app.setFont(QFont('Segoe UI',10))
    w=MainWindow(); w.show()
    sys.exit(app.exec_())