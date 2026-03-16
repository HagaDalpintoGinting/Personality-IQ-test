"""
Jalankan: py debug_pdf.py
Untuk cari tahu persis error PDF export dari mana
"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import json
with open('i18n/id.json', encoding='utf-8') as f:
    txt = json.load(f)

# Dummy data
data = {
    'iq': 100, 'label': 'Average', 'color': '#8b5cf6',
    'percentile': 50, 'correct': 20, 'total': 40,
    'weighted_pct': 50.0, 'n_population': 2051, 'lang': 'id',
    'cognitive': {
        'fluid':        {'score_pct': 50, 'level': 'average', 'level_id': 'Rata-rata', 'rank': 1},
        'crystallized': {'score_pct': 60, 'level': 'average', 'level_id': 'Rata-rata', 'rank': 2},
        'abstract':     {'score_pct': 40, 'level': 'average', 'level_id': 'Rata-rata', 'rank': 3},
        'quantitative': {'score_pct': 55, 'level': 'average', 'level_id': 'Rata-rata', 'rank': 4},
        'spatial':      {'score_pct': 45, 'level': 'average', 'level_id': 'Rata-rata', 'rank': 5},
    },
    'archetype':   {'name': 'The Analyst', 'tag': 'ANALYTICAL', 'desc': 'Test'},
    'combined':    {'name': 'Test', 'desc': 'Test', 'action': 'Test'},
    'careers':     [{'name': 'Engineer', 'confidence': 80}],
    'bf_scores':   {'O':70,'C':60,'E':50,'A':65,'N':40},
    'bf_pcts':     {'O':70,'C':60,'E':50,'A':65,'N':40},
    'blind_spots': [], 'roadmap': [],
    'learning_style_name':   'Visual',
    'learning_style_detail': {'desc':'Visual learner','tips':['Use diagrams'],'environment':'Quiet'},
    'iq_answers': [0]*40, 'iq_session': [], 'n_bf_pop': 874434,
}

print("Testing PDF generation...")
try:
    from report.pdf_generator import generate_pdf
    generate_pdf('test_output.pdf', data, txt)
    print(f"SUCCESS! File: test_output.pdf ({os.path.getsize('test_output.pdf')//1024} KB)")
except Exception as e:
    print(f"ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()