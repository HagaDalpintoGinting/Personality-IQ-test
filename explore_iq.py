import pandas as pd

# ── Dataset 1: IQ Alpha Fullscale ──
print("=" * 60)
print("DATASET 1 — IQ Alpha Fullscale")
print("=" * 60)

try:
    df1 = pd.read_csv('data/data-iq-alpha.csv')
except:
    try:
        df1 = pd.read_csv('data/data-iq-alpha.csv', sep='\t')
    except Exception as e:
        print(f"Error: {e}"); df1 = None

if df1 is not None:
    print(f"Shape: {df1.shape}")
    print(f"\nKolom: {df1.columns.tolist()}")
    print(f"\nSample 3 baris:\n{df1.head(3)}")
    print(f"\nMissing values:\n{df1.isnull().sum()}")
    print(f"\nStatistik:\n{df1.describe()}")

# ── Dataset 2: Vocabulary IQ ──
print("\n" + "=" * 60)
print("DATASET 2 — Vocabulary IQ Test")
print("=" * 60)

try:
    df2 = pd.read_csv('data/VIQT_data.csv')
except:
    try:
        df2 = pd.read_csv('data/VIQT_data.csv', sep='\t')
    except Exception as e:
        print(f"Error: {e}"); df2 = None

if df2 is not None:
    print(f"Shape: {df2.shape}")
    print(f"\nKolom: {df2.columns.tolist()}")
    print(f"\nSample 3 baris:\n{df2.head(3)}")
    print(f"\nMissing values:\n{df2.isnull().sum()}")
    print(f"\nStatistik:\n{df2.describe()}")