# 🧠 Assessment IQ & Kepribadian

Aplikasi desktop Python untuk mengukur **estimasi IQ** dan **profil kepribadian Big Five (OCEAN)** — semua hasil dibandingkan dengan data populasi riil dari dataset akademik tervalidasi.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Struktur Proyek](#-struktur-proyek)
- [Dataset](#-dataset)
- [Cara Install & Menjalankan](#-cara-install--menjalankan)
- [Alur Penggunaan Aplikasi](#-alur-penggunaan-aplikasi)
- [Metodologi Penilaian](#-metodologi-penilaian)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)

---

## ✨ Fitur

| Fitur | Detail |
|---|---|
| 🧠 **Tes IQ** | 40 soal standar Mensa-style: deret angka, analogi verbal, logika, numerik, pola visual |
| 🎭 **Tes Kepribadian** | 50 soal Big Five IPIP standar (10 per trait OCEAN) |
| ⏱️ **Timer IQ** | Countdown 20 menit — sesuai standar tes IQ internasional |
| 🔀 **Soal Diacak** | Urutan soal berbeda setiap sesi |
| 📊 **Percentile Populasi** | Hasil dibandingkan dengan 874.434+ responden dataset riil |
| 🔍 **Review Jawaban** | Accordion review setiap soal IQ beserta penjelasan |
| 📄 **Export PDF** | Laporan lengkap: skor IQ, review jawaban, profil OCEAN |
| 🎨 **UI Dual-Tone** | Sidebar gelap + konten terang, animasi fade antar soal |

---

## 📁 Struktur Proyek

```
BigFive/
│
├── app.py                  ← Aplikasi utama (entry point)
│
├── data/                   ← Dataset mentah (perlu didownload, lihat bawah)
│   ├── data-final.csv      ← Tunguz Big Five (Kaggle) — 1.015.341 baris
│   ├── data-iq-alpha.csv   ← Open Psychometrics IQ Alpha — 3.194 baris
│   └── VIQT_data.csv       ← Vocabulary IQ Test — 12.173 baris
│
├── processed/              ← File hasil preprocessing (di-generate otomatis)
│   ├── norms.json          ← Tabel percentile Big Five per skor
│   ├── clusters.json       ← Centroid KMeans + label archetype
│   ├── scaler.json         ← Parameter StandardScaler
│   └── iq_norms.json       ← Tabel norma IQ dari dataset riil
│
├── explore.py              ← Eksplorasi dataset Big Five
├── process.py              ← Generate norms.json dari dataset
├── model.py                ← KMeans clustering (k=3)
├── label.py                ← Labeling cluster archetype
├── explore_iq.py           ← Eksplorasi dataset IQ
└── process_iq.py           ← Generate iq_norms.json dari dataset
```

---

## 📊 Dataset

Proyek ini menggunakan tiga dataset publik. **Download sebelum menjalankan aplikasi.**

### 1. Tunguz Big Five Personality (Kaggle)
- **File:** `data/data-final.csv`
- **Sumber:** https://www.kaggle.com/datasets/tunguz/big-five-personality-test
- **Ukuran:** ~1 juta responden, 163 kolom
- **Digunakan untuk:** Tabel norma percentile OCEAN, clustering archetype

### 2. Open Psychometrics IQ Alpha
- **File:** `data/data-iq-alpha.csv`
- **Sumber:** https://openpsychometrics.org/_rawdata/ → "IQ Test Alpha"
- **Ukuran:** 3.194 responden, 61 kolom
- **Digunakan untuk:** Norma IQ populasi riil (mean, std, percentile mapping)

### 3. Vocabulary IQ Test (VIQT)
- **File:** `data/VIQT_data.csv`
- **Sumber:** https://openpsychometrics.org/_rawdata/ → "Vocabulary IQ Test"
- **Format:** Tab-separated (TSV)
- **Digunakan untuk:** Validasi dan normalisasi skor verbal

---

## 🚀 Cara Install & Menjalankan

### Persyaratan Sistem
- Python **3.8** atau lebih baru
- OS: Windows 10/11, macOS, atau Linux
- RAM: minimal 4 GB (untuk loading dataset saat preprocessing)

---

### Langkah 1 — Clone / Download Proyek

```bash
# Kalau pakai git
git clone <url-repo-kamu>
cd BigFive

# Atau extract ZIP ke folder BigFive/
```

---

### Langkah 2 — Buat Virtual Environment (Direkomendasikan)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Langkah 3 — Install Dependencies

```bash
pip install PyQt5 pandas numpy scipy scikit-learn matplotlib reportlab
```

Atau kalau ada file `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Daftar library yang dibutuhkan:**

| Library | Versi minimum | Fungsi |
|---|---|---|
| `PyQt5` | 5.15 | GUI desktop |
| `pandas` | 1.3 | Baca & proses dataset CSV |
| `numpy` | 1.21 | Komputasi numerik |
| `scipy` | 1.7 | Distribusi normal (IQ norma) |
| `scikit-learn` | 0.24 | KMeans clustering |
| `matplotlib` | 3.4 | Visualisasi (opsional, untuk explore.py) |
| `reportlab` | 3.6 | Export hasil ke PDF |

---

### Langkah 4 — Download Dataset

Buat folder `data/` di root proyek, lalu download ketiga file dataset:

```bash
mkdir data
```

1. **Big Five** → Download dari Kaggle (butuh akun):
   https://www.kaggle.com/datasets/tunguz/big-five-personality-test
   Simpan sebagai `data/data-final.csv`

2. **IQ Alpha** → Download dari Open Psychometrics:
   https://openpsychometrics.org/_rawdata/
   Cari "IQ Test Alpha", extract, simpan sebagai `data/data-iq-alpha.csv`

3. **VIQT** → Dari situs yang sama, cari "Vocabulary IQ Test",
   simpan sebagai `data/VIQT_data.csv`

---

### Langkah 5 — Generate File Processed

Jalankan pipeline preprocessing secara berurutan. Ini hanya perlu dilakukan **satu kali**.

```bash
# 1. Eksplorasi dan validasi dataset Big Five (opsional)
python explore.py

# 2. Generate tabel norma percentile OCEAN
python process.py

# 3. Jalankan KMeans clustering (k=3 archetype)
python model.py

# 4. Labeling archetype cluster
python label.py

# 5. Eksplorasi dataset IQ (opsional)
python explore_iq.py

# 6. Generate tabel norma IQ
python process_iq.py
```

Setelah selesai, folder `processed/` akan berisi 4 file:

```
processed/
├── norms.json       ✓
├── clusters.json    ✓
├── scaler.json      ✓
└── iq_norms.json    ✓
```

---

### Langkah 6 — Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan terbuka. Pilih **Tes IQ** atau **Tes Kepribadian** dari halaman utama.

---

## 🎮 Alur Penggunaan Aplikasi

```
Halaman Utama
├── [Mulai Tes IQ]
│   ├── 40 soal (8 per kategori, diacak tiap sesi)
│   ├── Timer countdown 20 menit di sidebar
│   ├── Navigasi bebas ← →
│   └── Halaman Hasil IQ
│       ├── Estimasi IQ + kategori + percentile
│       ├── Breakdown skor per kategori
│       ├── Review jawaban (accordion, klik untuk expand)
│       ├── Penjelasan tiap soal
│       └── [Export PDF] → file .pdf lengkap
│
└── [Mulai Tes Kepribadian]
    ├── 50 soal Likert 1–5 (diacak tiap sesi)
    ├── Indikator trait aktif di sidebar
    └── Halaman Hasil Kepribadian
        ├── Archetype label (The Flourisher / The Sensitive / The Reserved)
        ├── Percentile card per trait OCEAN
        ├── Radar chart kamu vs populasi
        ├── Progress bar skor per trait
        └── Insight personal berbasis kombinasi skor
```

---

## 📐 Metodologi Penilaian

### IQ
- **Skoring:** Jumlah jawaban benar → persentase benar → lookup ke tabel norma populasi → estimasi IQ (mean=100, SD=15 via distribusi normal invers)
- **Norma:** Diambil dari dataset Open Psychometrics IQ Alpha (N=2.051 valid responden setelah cleaning)
- **Standarisasi:** IQ dikalkulasi via `scipy.stats.norm.ppf(percentile)` sehingga distribusi mengikuti kurva bell internasional
- **Kategori IQ:** Very Superior (≥130), Superior (≥120), High Average (≥110), Average (90–109), Low Average (80–89), Below Average (70–79), Well Below Avg (<70)

### Big Five OCEAN
- **Skoring:** Skala Likert 1–5, item reverse-scored dibalik, skor dinormalisasi ke 0–100
- **Norma:** Percentile dihitung dari 874.434 responden valid dataset Tunguz (setelah cleaning NaN & skor out-of-range)
- **Clustering:** KMeans k=3 pada skor OCEAN yang di-StandardScaler, menghasilkan 3 archetype kepribadian
- **Reverse scoring:** Item yang memiliki flag `reverse=True` dihitung sebagai `6 - nilai`

---

## 🛠 Teknologi yang Digunakan

| Komponen | Teknologi |
|---|---|
| GUI | PyQt5 (QStackedWidget, custom widgets, QPropertyAnimation) |
| Data Processing | pandas, numpy |
| Machine Learning | scikit-learn (KMeans, StandardScaler) |
| Statistik | scipy.stats (norm.ppf untuk IQ norma) |
| PDF Export | ReportLab (Platypus flowables) |
| Visualisasi | QPainter custom (RadarWidget, AnimatedBar, CountdownTimer) |

---

## 📝 Catatan

- File `processed/` **tidak perlu** di-generate ulang setelah pertama kali, kecuali kamu mengubah dataset atau parameter clustering.
- Soal IQ dan Big Five **diacak tiap sesi** — urutan akan berbeda setiap kamu mulai tes baru.
- Timer IQ mengikuti standar internasional: **total waktu** (bukan per soal). Saat waktu habis, jawaban yang sudah diisi akan otomatis di-submit.
- Export PDF mencakup hasil IQ **dan** Big Five jika keduanya sudah dikerjakan dalam sesi yang sama.

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