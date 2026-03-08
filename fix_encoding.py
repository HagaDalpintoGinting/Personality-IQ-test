# fix_encoding.py
import json

# Baca dengan encoding latin-1
with open('processed/clusters.json', encoding='latin-1') as f:
    data = json.load(f)

# Tulis ulang dengan utf-8
with open('processed/clusters.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Fixed! Isi clusters.json:")
for c in data:
    print(f"  {c['cluster_id']}: {c['name']} — {c['tag']}")