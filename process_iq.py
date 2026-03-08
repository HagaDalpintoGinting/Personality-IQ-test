import pandas as pd
import numpy as np
import json
import os

os.makedirs('processed', exist_ok=True)

# ══════════════════════════════════════════════════════
# DATASET 1 — IQ Alpha Fullscale
# Kolom: VQ1s-VQ7s (Verbal), RQ1s-RQ6s (Reasoning), MQ1s-MQ6s (Math)
# Skor per soal: 1-4 (benar = nilai tertinggi sesuai soal)
# ══════════════════════════════════════════════════════
print("Loading Dataset 1 — IQ Alpha Fullscale...")
df1 = pd.read_csv('data/data-iq-alpha.csv')
print(f"Raw: {len(df1):,} responden")

# Ambil kolom skor saja
vq_cols = [f'VQ{i}s' for i in range(1, 8)]   # 7 soal verbal
rq_cols = [f'RQ{i}s' for i in range(1, 7)]   # 6 soal reasoning
mq_cols = [f'MQ{i}s' for i in range(1, 7)]   # 6 soal math
all_score_cols = vq_cols + rq_cols + mq_cols  # 19 soal total

df1 = df1[all_score_cols].copy()

# Bersihkan — hapus nilai negatif dan NaN (nilai -1, -2 = tidak valid)
df1 = df1.dropna()
for col in all_score_cols:
    df1 = df1[df1[col] >= 0]
print(f"Setelah bersih: {len(df1):,} responden")

# Tiap soal punya max skor berbeda — normalisasi ke 0-1 dulu
# VQ: max=4, RQ: max=4, MQ: max=4 (berdasarkan statistik: max=4)
max_scores = {col: 4 for col in all_score_cols}

# Hitung total skor (0-100)
df1['total_raw']  = df1[all_score_cols].sum(axis=1)
df1['total_max']  = len(all_score_cols) * 4
df1['pct_correct'] = (df1['total_raw'] / df1['total_max'] * 100).round(2)

# Hitung skor per kategori (0-100)
df1['verbal_pct']    = (df1[vq_cols].sum(axis=1) / (len(vq_cols)*4) * 100).round(2)
df1['reasoning_pct'] = (df1[rq_cols].sum(axis=1) / (len(rq_cols)*4) * 100).round(2)
df1['math_pct']      = (df1[mq_cols].sum(axis=1) / (len(mq_cols)*4) * 100).round(2)

print(f"\nStatistik skor Dataset 1 (skala 0-100):")
print(f"  Total:     mean={df1['pct_correct'].mean():.1f}  std={df1['pct_correct'].std():.1f}")
print(f"  Verbal:    mean={df1['verbal_pct'].mean():.1f}  std={df1['verbal_pct'].std():.1f}")
print(f"  Reasoning: mean={df1['reasoning_pct'].mean():.1f}  std={df1['reasoning_pct'].std():.1f}")
print(f"  Math:      mean={df1['math_pct'].mean():.1f}  std={df1['math_pct'].std():.1f}")

# ══════════════════════════════════════════════════════
# DATASET 2 — Vocabulary IQ Test (fix separator)
# ══════════════════════════════════════════════════════
print("\nLoading Dataset 2 — Vocabulary IQ Test...")
df2 = pd.read_csv('data/VIQT_data.csv', sep='\t')
print(f"Raw: {len(df2):,} responden")
print(f"Kolom tersedia: {df2.columns.tolist()[:10]}...")

# Dataset ini sudah punya kolom score_right, score_wrong, score_full
# Kita pakai score_full sebagai skor utama
if 'score_full' in df2.columns:
    df2 = df2[['score_full', 'score_right', 'score_wrong']].dropna()
    # score_full bisa negatif (penalti salah), normalisasi ke 0-100
    # Max teoretis = 45 soal semua benar
    df2 = df2[df2['score_right'] >= 0]
    df2['pct_correct'] = (df2['score_right'] / 45 * 100).round(2)
    print(f"Setelah bersih: {len(df2):,} responden")
    print(f"\nStatistik skor Dataset 2 (skala 0-100):")
    print(f"  Vocabulary: mean={df2['pct_correct'].mean():.1f}  std={df2['pct_correct'].std():.1f}")
else:
    print("Kolom score_full tidak ditemukan — cek kolom:", df2.columns.tolist())
    df2 = None

# ══════════════════════════════════════════════════════
# BUILD IQ NORM TABLE
# Gabungkan kedua dataset untuk norm populasi
# ══════════════════════════════════════════════════════
print("\nMembangun IQ norm table...")

# Gunakan dataset 1 sebagai basis norm (lebih banyak kategori)
arr = df1['pct_correct'].values

# Percentile lookup: skor 0-100 → persentil
iq_norms = {}
for score in range(0, 101):
    pct = float(np.mean(arr <= score) * 100)
    iq_norms[str(score)] = round(pct, 1)

# Statistik per kategori
iq_stats = {
    'total': {
        'mean': round(float(df1['pct_correct'].mean()), 2),
        'std':  round(float(df1['pct_correct'].std()), 2),
        'p25':  round(float(np.percentile(arr, 25)), 2),
        'p50':  round(float(np.percentile(arr, 50)), 2),
        'p75':  round(float(np.percentile(arr, 75)), 2),
    },
    'verbal': {
        'mean': round(float(df1['verbal_pct'].mean()), 2),
        'std':  round(float(df1['verbal_pct'].std()), 2),
    },
    'reasoning': {
        'mean': round(float(df1['reasoning_pct'].mean()), 2),
        'std':  round(float(df1['reasoning_pct'].std()), 2),
    },
    'math': {
        'mean': round(float(df1['math_pct'].mean()), 2),
        'std':  round(float(df1['math_pct'].std()), 2),
    },
}

# Tambahkan vocab stats dari dataset 2
if df2 is not None:
    iq_stats['vocabulary'] = {
        'mean': round(float(df2['pct_correct'].mean()), 2),
        'std':  round(float(df2['pct_correct'].std()), 2),
    }

# ── IQ Score mapping (konversi persentil → estimasi IQ) ──
# Berdasarkan distribusi normal: mean=100, sd=15
iq_score_map = []
for pct in range(0, 101):
    from scipy.stats import norm
    z   = norm.ppf(max(0.001, min(0.999, pct/100)))
    iq  = round(100 + 15 * z)
    iq_score_map.append(iq)

output = {
    'norms':         iq_norms,
    'stats':         iq_stats,
    'iq_score_map':  iq_score_map,
    'n_population':  len(df1),
    'source':        'Open Psychometrics IQ Alpha + VIQT via Kaggle',
}

with open('processed/iq_norms.json', 'w') as f:
    json.dump(output, f)

print(f"\nSelesai! iq_norms.json tersimpan.")
print(f"Total responden valid (Dataset 1): {len(df1):,}")
if df2 is not None:
    print(f"Total responden valid (Dataset 2): {len(df2):,}")

# Print percentile landmarks
print(f"\nLandmark persentil skor:")
for p in [25, 50, 75, 90]:
    val = np.percentile(arr, p)
    print(f"  p{p} = {val:.1f}% benar → IQ estimasi {iq_score_map[int(val)]}")