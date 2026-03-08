import pandas as pd
import numpy as np

# Load dataset
# Dataset Tunguz pakai separator TAB, bukan koma
df = pd.read_csv('data/data-final.csv', sep='\t')

# Lihat struktur data
print("Shape:", df.shape)
print("\nKolom:", df.columns.tolist())
print("\nSample 5 baris:")
print(df.head())

print("\nCek missing values:")
print(df.isnull().sum())

print("\nStatistik deskriptif:")
print(df.describe())