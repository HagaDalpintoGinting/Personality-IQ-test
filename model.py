import pandas as pd
import numpy as np
import json
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ── Load & proses ulang dataset (sama seperti step2) ──
print("Loading dataset...")
df = pd.read_csv('data/data-final.csv', sep='\t')

trait_cols = {
    'O': ['OPN1','OPN2','OPN3','OPN4','OPN5','OPN6','OPN7','OPN8','OPN9','OPN10'],
    'C': ['CSN1','CSN2','CSN3','CSN4','CSN5','CSN6','CSN7','CSN8','CSN9','CSN10'],
    'E': ['EXT1','EXT2','EXT3','EXT4','EXT5','EXT6','EXT7','EXT8','EXT9','EXT10'],
    'A': ['AGR1','AGR2','AGR3','AGR4','AGR5','AGR6','AGR7','AGR8','AGR9','AGR10'],
    'N': ['EST1','EST2','EST3','EST4','EST5','EST6','EST7','EST8','EST9','EST10'],
}
reverse_items = {
    'O': ['OPN2','OPN4','OPN6','OPN8'],
    'C': ['CSN2','CSN4','CSN6','CSN8'],
    'E': ['EXT2','EXT4','EXT6','EXT8','EXT10'],
    'A': ['AGR1','AGR3','AGR5','AGR7'],
    'N': ['EST2','EST4'],
}

all_cols = [c for cols in trait_cols.values() for c in cols]
df = df[all_cols].dropna()
for col in all_cols:
    df = df[df[col] != 0]

for trait, cols in trait_cols.items():
    df_trait = df[cols].copy()
    for col in reverse_items[trait]:
        df_trait[col] = 6 - df_trait[col]
    df[f'score_{trait}'] = ((df_trait.mean(axis=1) - 1) / 4 * 100).round(2)

print(f"Data siap: {len(df):,} responden")

# ── Ambil fitur & sample ──
features = df[['score_O','score_C','score_E','score_A','score_N']].dropna()

# Sample 80.000 agar tidak terlalu lama tapi tetap representatif
print("Sampling 80,000 responden...")
sample = features.sample(80000, random_state=42)

# ── Standarisasi fitur ──
scaler = StandardScaler()
X = scaler.fit_transform(sample)

# ── Elbow method — cari k optimal ──
print("\nMenjalankan Elbow Method (k=2 sampai 10)...")
inertias = []
for k in range(2, 11):
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    km.fit(X)
    inertias.append(km.inertia_)
    print(f"  k={k}  inertia={km.inertia_:,.0f}")

# ── Pilih k terbaik otomatis (metode kneepoint sederhana) ──
diffs      = [inertias[i-1] - inertias[i] for i in range(1, len(inertias))]
diffs2     = [diffs[i-1] - diffs[i] for i in range(1, len(diffs))]
best_k     = diffs2.index(max(diffs2)) + 3   # offset karena mulai dari k=2
print(f"\nK optimal terdeteksi: {best_k}")

# ── Fit model final ──
print(f"Fitting KMeans dengan k={best_k}...")
km_final = KMeans(n_clusters=best_k, random_state=42, n_init=20, max_iter=500)
km_final.fit(X)

# ── Konversi centroid ke skala 0-100 ──
centroids = scaler.inverse_transform(km_final.cluster_centers_)

# ── Hitung ukuran tiap cluster ──
labels     = km_final.labels_
sizes      = [(labels == i).sum() for i in range(best_k)]
pcts       = [round(s / len(sample) * 100, 1) for s in sizes]

print("\nHasil Cluster Centroid (skala 0-100):")
print(f"{'Cluster':>8} {'O':>6} {'C':>6} {'E':>6} {'A':>6} {'N':>6} {'Size%':>7}")
print("-" * 50)

clusters = []
for i, c in enumerate(centroids):
    print(f"  {i:>6}  {c[0]:>5.1f}  {c[1]:>5.1f}  {c[2]:>5.1f}  {c[3]:>5.1f}  {c[4]:>5.1f}  {pcts[i]:>6}%")
    clusters.append({
        'cluster_id': i,
        'O': round(float(c[0]), 1),
        'C': round(float(c[1]), 1),
        'E': round(float(c[2]), 1),
        'A': round(float(c[3]), 1),
        'N': round(float(c[4]), 1),
        'size_pct': pcts[i],
        # Nama & deskripsi akan kita assign manual di step berikutnya
        'name': f'Cluster {i}',
        'tag':  'TBD',
        'desc': 'TBD',
    })

# ── Simpan model & clusters ──
os.makedirs('processed', exist_ok=True)

with open('processed/clusters.json', 'w') as f:
    json.dump(clusters, f, indent=2)

# Simpan juga scaler params untuk dipakai di app nanti
scaler_params = {
    'mean': scaler.mean_.tolist(),
    'scale': scaler.scale_.tolist(),
    'features': ['score_O','score_C','score_E','score_A','score_N'],
}
with open('processed/scaler.json', 'w') as f:
    json.dump(scaler_params, f, indent=2)

print(f"\nSelesai! File tersimpan:")
print(f"  processed/clusters.json")
print(f"  processed/scaler.json")