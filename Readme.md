# 🧠 Assessment IQ & Kepribadian

Aplikasi desktop Python untuk mengukur **estimasi IQ** dan **profil kepribadian Big Five (OCEAN)** — semua hasil dibandingkan dengan data populasi riil dari dataset akademik tervalidasi.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green) ![Version](https://img.shields.io/badge/Version-4.0-purple) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Struktur Proyek](#-struktur-proyek)
- [Dataset](#-dataset)
- [Cara Install & Menjalankan](#-cara-install--menjalankan)
- [Alur Penggunaan Aplikasi](#-alur-penggunaan-aplikasi)
- [Metodologi Penilaian](#-metodologi-penilaian)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Changelog](#-changelog)

---

## ✨ Fitur

| Fitur | Detail |
|---|---|
| 🧠 **Tes IQ** | 40 soal: deret angka, analogi verbal, logika, numerik, pola visual |
| 🎭 **Tes Kepribadian** | 50 soal Big Five IPIP standar (10 per trait OCEAN) |
| 🌐 **Bilingual EN/ID** | Toggle bahasa di setiap halaman — soal, opsi, penjelasan, dan seluruh UI ikut berubah |
| ⚖️ **Weighted IQ Scoring** | Soal difficulty 1–7 dipakai sebagai bobot — lebih akurat dari % benar biasa |
| 🧩 **Cognitive Profile** | Breakdown 5 domain kognitif: Fluid, Crystallized, Abstract, Quantitative, Spatial |
| 🏷️ **Expert Archetype** | 14 tipe kepribadian dari kombinasi skor OCEAN |
| 🔗 **Combined IQ × Personality** | 7 profil gabungan IQ dan kepribadian (misal: "Architect of Ideas") |
| 💼 **Career Recommendations** | Top 5 karir dengan confidence bar berdasarkan profil lengkap |
| 📚 **Learning Style** | Visual / Auditory / Reading-Writing / Kinesthetic + tips praktis |
| ⚠️ **Blind Spots** | Hingga 4 risiko personal dengan saran mitigasi konkret |
| 🗓️ **Development Roadmap** | Rencana pengembangan diri 3 bulan yang dipersonalisasi |
| ⏱️ **Timer IQ** | Countdown 20 menit — sesuai standar tes IQ internasional |
| 📊 **Percentile Populasi** | Hasil dibandingkan dengan 874.434+ responden dataset riil |
| 🔍 **Review Jawaban** | Accordion per soal IQ + penjelasan bilingual |
| 📄 **PDF 2-in-1** | Executive Summary (2 hal) + Full Report 7 seksi |
| 🎨 **UI Dual-Tone** | Sidebar gelap + konten terang, animasi fade antar soal |

---

## 📁 Struktur Proyek

```
BigFive/
│
├── app.py                    ← Aplikasi utama (entry point)
│
├── engine/                   ← Expert rule engine
│   ├── __init__.py
│   ├── scoring.py            ← Weighted IQ scoring + cognitive profile
│   └── expert_rules.py       ← 6-layer expert engine (archetype → roadmap)
│
├── i18n/                     ← File teks bilingual
│   ├── id.json               ← Semua teks UI Bahasa Indonesia
│   └── en.json               ← Semua teks UI English
│
├── report/                   ← PDF generator
│   ├── __init__.py
│   └── pdf_generator.py      ← ReportLab 2-in-1 PDF builder
│
├── data/                     ← Dataset mentah (perlu didownload)
│   ├── data-final.csv        ← Tunguz Big Five (Kaggle) — 1.015.341 baris
│   ├── data-iq-alpha.csv     ← Open Psychometrics IQ Alpha — 3.194 baris
│   └── VIQT_data.csv         ← Vocabulary IQ Test — 12.173 baris
│
├── processed/                ← File hasil preprocessing (di-generate otomatis)
│   ├── norms.json
│   ├── clusters.json
│   ├── scaler.json
│   └── iq_norms.json
│
├── explore.py
├── process.py
├── model.py
├── label.py
├── explore_iq.py
└── process_iq.py
```

---

## 📊 Dataset

### 1. Tunguz Big Five Personality (Kaggle)
- **File:** `data/data-final.csv`
- **Sumber:** https://www.kaggle.com/datasets/tunguz/big-five-personality-test
- **Digunakan untuk:** Tabel norma percentile OCEAN, clustering archetype

### 2. Open Psychometrics IQ Alpha
- **File:** `data/data-iq-alpha.csv`
- **Sumber:** https://openpsychometrics.org/_rawdata/ → "IQ Test Alpha"
- **Digunakan untuk:** Norma IQ populasi riil

### 3. Vocabulary IQ Test (VIQT)
- **File:** `data/VIQT_data.csv`
- **Sumber:** https://openpsychometrics.org/_rawdata/ → "Vocabulary IQ Test"
- **Digunakan untuk:** Validasi dan normalisasi skor verbal

---

## 🚀 Cara Install & Menjalankan

### Persyaratan Sistem
- Python **3.8** atau lebih baru
- OS: Windows 10/11, macOS, atau Linux

### Langkah 1 — Clone Proyek

```bash
git clone <url repo ini>
cd BigFive
```

### Langkah 2 — Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Langkah 3 — Install Dependencies

```bash
pip install PyQt5 pandas numpy scipy scikit-learn matplotlib reportlab
```

| Library | Versi minimum | Fungsi |
|---|---|---|
| `PyQt5` | 5.15 | GUI desktop |
| `pandas` | 1.3 | Baca & proses dataset CSV |
| `numpy` | 1.21 | Komputasi numerik |
| `scipy` | 1.7 | Distribusi normal (IQ norma) |
| `scikit-learn` | 0.24 | KMeans clustering |
| `matplotlib` | 3.4 | Visualisasi (opsional) |
| `reportlab` | 3.6 | Export hasil ke PDF |

### Langkah 4 — Download Dataset

```bash
mkdir data
```

1. **Big Five** → https://www.kaggle.com/datasets/tunguz/big-five-personality-test → `data/data-final.csv`
2. **IQ Alpha** → https://openpsychometrics.org/_rawdata/ → "IQ Test Alpha" → `data/data-iq-alpha.csv`
3. **VIQT** → situs yang sama → "Vocabulary IQ Test" → `data/VIQT_data.csv`

### Langkah 5 — Generate File Processed

Jalankan **satu kali** secara berurutan:

```bash
python process.py
python model.py
python label.py
python process_iq.py
```

### Langkah 6 — Jalankan Aplikasi

```bash
python app.py
```

---

## 🎮 Alur Penggunaan Aplikasi

```
Halaman Utama  [toggle EN/ID]
├── [Mulai Tes IQ]
│   ├── 40 soal bilingual (8 per kategori, diacak tiap sesi)
│   ├── Timer countdown 20 menit
│   └── Halaman Hasil IQ
│       ├── Estimasi IQ + kategori + percentile
│       ├── Cognitive Profile (5 domain)
│       ├── Breakdown per kategori + review jawaban
│       └── [Export PDF 2-in-1]
│
└── [Mulai Tes Kepribadian]
    ├── 50 soal Likert bilingual (diacak tiap sesi)
    └── Halaman Hasil Kepribadian
        ├── Archetype + Combined IQ×Personality Profile
        ├── Radar chart kamu vs populasi
        ├── Career Recommendations (top 5)
        ├── Learning Style + tips
        ├── Blind Spots & mitigasi
        ├── Development Roadmap 3 bulan
        └── [Export PDF 2-in-1]
```

---

## 📄 Format PDF 2-in-1

| Halaman | Konten |
|---|---|
| 1 | Cover — IQ score, kategori, archetype |
| 2 | Executive Summary — snapshot semua skor |
| 3+ | Full Report — 7 seksi lengkap + Appendix |

**7 Seksi:** Cognitive Assessment · Personality Profile · Combined Analysis · Career Recommendations · Learning Style · Blind Spots · 3-Month Roadmap

---

## 📐 Metodologi Penilaian

### IQ
- **Weighted Scoring:** Difficulty soal (1–7) sebagai bobot — soal sulit berkontribusi lebih besar
- **Norma:** Open Psychometrics IQ Alpha (N=2.051 valid responden)
- **Standarisasi:** `scipy.stats.norm.ppf(percentile)` → distribusi bell internasional (mean=100, SD=15)
- **Kategori:** Very Superior (≥130) · Superior (≥120) · High Average (≥110) · Average (90–109) · Low Average (80–89) · Below Average (70–79) · Well Below Avg (<70)

### Cognitive Profile
5 domain dipetakan dari kategori soal: Fluid (Deret Angka) · Crystallized (Analogi Verbal) · Abstract (Logika) · Quantitative (Numerik) · Spatial (Pola Visual)

### Big Five OCEAN
- **Skoring:** Likert 1–5, reverse-scored item dibalik, dinormalisasi ke 0–100
- **Norma:** 874.434 responden valid dataset Tunguz

### Expert Engine (6 Layer)
1. **Archetype** — 14 tipe dari kombinasi OCEAN
2. **Combined Profile** — 7 profil IQ × Personality
3. **Career** — 15 karir dengan weighted confidence score
4. **Learning Style** — VARK inferred dari OCEAN + cognitive
5. **Blind Spots** — 11 rule → max 4 per user
6. **Roadmap** — 3 bulan aksi dipersonalisasi

---

## 🛠 Teknologi yang Digunakan

| Komponen | Teknologi |
|---|---|
| GUI | PyQt5 (QStackedWidget, custom widgets, QPropertyAnimation) |
| Expert Engine | Pure Python rule-based (6 layer) |
| Bilingual | JSON i18n (id.json / en.json) |
| Data Processing | pandas, numpy |
| Machine Learning | scikit-learn (KMeans, StandardScaler) |
| Statistik | scipy.stats |
| PDF Export | ReportLab Platypus (2-in-1) |
| Visualisasi | QPainter custom (RadarWidget, AnimatedBar, CountdownTimer) |

---

## 📌 Changelog

### v4.0
- Bilingual EN/ID — semua soal, opsi, penjelasan, dan UI teks
- Weighted IQ scoring berdasarkan difficulty soal
- Cognitive Profile 5 domain
- Expert Rule Engine 6 layer
- PDF 2-in-1: Executive Summary + Full Report 7 seksi
- Fix: crash saat toggle bahasa di halaman utama
- Fix: `QWidget: Must construct a QApplication before a QWidget`

### v3.0
- Dual-tone UI, animated bars, radar chart
- Accordion review jawaban IQ
- Export PDF dasar

### v2.0
- Integrasi tes IQ + Big Five dalam satu aplikasi
- Percentile berbasis dataset riil

### v1.0
- Tes Big Five OCEAN dengan norma Kaggle Tunguz

---

## 👤 Credits

### Creator
**Haga Dalpinto Ginting** (Hagz)
> Desain konsep, arsitektur proyek, pipeline data, dan pengembangan aplikasi.

### Built With Help From
**Claude AI** by Anthropic
> AI assistant yang membantu dalam penulisan kode, debugging, desain UI, pemilihan metodologi statistik, dan penyusunan dokumentasi sepanjang proyek ini.

---

*Dataset: Tunguz Big Five (Kaggle) · Open Psychometrics IQ Alpha · VIQT*  
*Aplikasi ini bersifat edukatif dan bukan pengganti asesmen psikologis profesional.*