import json

with open('processed/clusters.json') as f:
    clusters = json.load(f)

# Assign nama, tag, dan deskripsi berdasarkan pola centroid
labels = [
    {
        'name': 'The Flourisher',
        'tag':  'STABIL · SOSIAL · TERORGANISIR',
        'desc': 'Kamu adalah tipe yang berkembang dengan baik secara psikologis. '
                'Stabil secara emosional, terorganisir, hangat, dan nyaman berinteraksi sosial. '
                'Kamu cenderung optimistis dan mampu menjaga keseimbangan hidup dengan baik.',
    },
    {
        'name': 'The Sensitive',
        'tag':  'EMPATIK · KREATIF · INTENS',
        'desc': 'Kamu memiliki kepekaan emosional yang tinggi dan empati yang dalam. '
                'Kreativitas dan keterbukaan pikiranmu adalah kekuatan besar, '
                'meski intensitas perasaanmu kadang bisa menjadi tantangan tersendiri.',
    },
    {
        'name': 'The Reserved',
        'tag':  'MANDIRI · REFLEKTIF · SELEKTIF',
        'desc': 'Kamu adalah tipe yang lebih memilih kedalaman daripada keluasan. '
                'Introvert dan selektif dalam hubungan sosial, kamu memproses dunia '
                'dengan cara yang tenang dan penuh pertimbangan.',
    },
]

for i, cluster in enumerate(clusters):
    cluster['name'] = labels[i]['name']
    cluster['tag']  = labels[i]['tag']
    cluster['desc'] = labels[i]['desc']

with open('processed/clusters.json', 'w') as f:
    json.dump(clusters, f, indent=2, ensure_ascii=False)

print("Label berhasil ditambahkan!")
for c in clusters:
    print(f"  Cluster {c['cluster_id']}: {c['name']} ({c['size_pct']}% populasi)")