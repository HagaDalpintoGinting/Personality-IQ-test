import pandas as pd
import numpy as np
import json
import os

# ── Load dataset ──
print("Loading dataset...")
df = pd.read_csv('data/data-final.csv', sep='\t')
print(f"Raw: {len(df):,} responden")

# ── Definisi kolom per trait ──
trait_cols = {
    'O': ['OPN1','OPN2','OPN3','OPN4','OPN5','OPN6','OPN7','OPN8','OPN9','OPN10'],
    'C': ['CSN1','CSN2','CSN3','CSN4','CSN5','CSN6','CSN7','CSN8','CSN9','CSN10'],
    'E': ['EXT1','EXT2','EXT3','EXT4','EXT5','EXT6','EXT7','EXT8','EXT9','EXT10'],
    'A': ['AGR1','AGR2','AGR3','AGR4','AGR5','AGR6','AGR7','AGR8','AGR9','AGR10'],
    'N': ['EST1','EST2','EST3','EST4','EST5','EST6','EST7','EST8','EST9','EST10'],
}

# ── Item reverse-scored ──
# Sumber: IPIP scoring key resmi
reverse_items = {
    'O': ['OPN2','OPN4','OPN6','OPN8'],
    'C': ['CSN2','CSN4','CSN6','CSN8'],
    'E': ['EXT2','EXT4','EXT6','EXT8','EXT10'],
    'A': ['AGR1','AGR3','AGR5','AGR7'],
    'N': ['EST2','EST4'],
}

# ── Ambil hanya kolom yang dibutuhkan ──
all_cols = [c for cols in trait_cols.values() for c in cols]
df = df[all_cols].copy()

# ── Bersihkan data ──
# 1. Hapus baris dengan missing values
df = df.dropna()
print(f"Setelah hapus NaN: {len(df):,} responden")

# 2. Hapus baris dengan nilai 0 (tidak valid di skala 1-5)
for col in all_cols:
    df = df[df[col] != 0]
print(f"Setelah hapus nilai 0: {len(df):,} responden")

# ── Hitung skor per trait (skala 0-100) ──
print("\nMenghitung skor per trait...")
for trait, cols in trait_cols.items():
    df_trait = df[cols].copy()
    # Reverse scoring
    for col in reverse_items[trait]:
        df_trait[col] = 6 - df_trait[col]
    # Mean → konversi ke 0-100
    df[f'score_{trait}'] = ((df_trait.mean(axis=1) - 1) / 4 * 100).round(2)

# Tampilkan statistik skor
print("\nStatistik skor (skala 0-100):")
for trait in ['O','C','E','A','N']:
    col = f'score_{trait}'
    arr = df[col].values
    print(f"  {trait}: mean={arr.mean():.1f}  std={arr.std():.1f}  "
          f"min={arr.min():.1f}  max={arr.max():.1f}")

# ── Build percentile lookup table ──
print("\nMembangun norm table...")
norms = {}
stats = {}
for trait in ['O','C','E','A','N']:
    arr = df[f'score_{trait}'].values
    table = {}
    for score in range(0, 101):
        pct = float(np.mean(arr <= score) * 100)
        table[str(score)] = round(pct, 1)
    norms[trait] = table
    stats[trait] = {
        'mean': round(float(arr.mean()), 2),
        'std':  round(float(arr.std()), 2),
        'p25':  round(float(np.percentile(arr, 25)), 2),
        'p50':  round(float(np.percentile(arr, 50)), 2),
        'p75':  round(float(np.percentile(arr, 75)), 2),
        'p90':  round(float(np.percentile(arr, 90)), 2),
    }
    print(f"  {trait}: p25={stats[trait]['p25']}  "
          f"p50={stats[trait]['p50']}  p75={stats[trait]['p75']}")

# ── Simpan hasil ──
os.makedirs('processed', exist_ok=True)
output = {
    'norms':        norms,
    'stats':        stats,
    'n_population': len(df),
    'source':       'Tunguz Big Five dataset via Kaggle (IPIP)',
}
with open('processed/norms.json', 'w') as f:
    json.dump(output, f)

print(f"\nSelesai! norms.json tersimpan.")
print(f"Total responden valid: {len(df):,}")