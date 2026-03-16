"""
core/ai_explainer.py
────────────────────────────────────────────────────────────
AI Explainer menggunakan Google Gemini API
Thread-safe: pakai QThread + Signal untuk update UI
────────────────────────────────────────────────────────────
"""

import os
import json
import urllib.request
import urllib.error

# ── Hardcoded key — ganti dengan key kamu ──────────────────
_HARDCODED_KEY = 'MASUKAN API KEY KAMU DISNI'  # Ganti dengan key kamu atau kosongkan untuk pakai env var
_API_KEY: str  = _HARDCODED_KEY or os.environ.get('GEMINI_API_KEY', '')

# Model dengan prefix 'models/' yang benar
GEMINI_MODELS = [
    'models/gemini-2.0-flash',
    'models/gemini-2.0-flash-lite',
    'models/gemini-flash-latest',
]
GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={key}'


# ══════════════════════════════════════════════════════════════
# API KEY
# ══════════════════════════════════════════════════════════════
def set_api_key(key: str):
    global _API_KEY
    _API_KEY = key.strip()

def get_api_key() -> str:
    return _API_KEY

def has_api_key() -> bool:
    return bool(_API_KEY and _API_KEY != 'MASUKKAN_API_KEY_KAMU_DISINI')


# ══════════════════════════════════════════════════════════════
# PROMPT BUILDERS
# ══════════════════════════════════════════════════════════════
def _bf_prompt(analysis: dict, lang: str) -> str:
    bf      = analysis.get('bf_scores', {})
    arch    = analysis.get('archetype', {})
    careers = [c['name'] for c in analysis.get('careers', [])[:3]]
    user    = analysis.get('user', {})
    name    = user.get('name', 'pengguna') if user else 'pengguna'

    TRAIT_NAMES_ID = {'O': 'Keterbukaan', 'C': 'Ketelitian', 'E': 'Ekstraversi',
                      'A': 'Keramahan', 'N': 'Neurotisisme'}
    TRAIT_NAMES_EN = {'O': 'Openness', 'C': 'Conscientiousness', 'E': 'Extraversion',
                      'A': 'Agreeableness', 'N': 'Neuroticism'}

    def score_label_id(v):
        if v >= 75: return 'sangat tinggi'
        if v >= 60: return 'tinggi'
        if v >= 40: return 'sedang'
        if v >= 25: return 'rendah'
        return 'sangat rendah'

    def score_label_en(v):
        if v >= 75: return 'very high'
        if v >= 60: return 'high'
        if v >= 40: return 'moderate'
        if v >= 25: return 'low'
        return 'very low'

    if lang == 'id':
        scores_detail = ', '.join(
            f"{TRAIT_NAMES_ID[t]} ({score_label_id(bf.get(t,50))})"
            for t in 'OCEAN'
        )
        return (
            f"Kamu adalah psikolog profesional yang hangat dan empatik.\n\n"
            f"Berikan interpretasi kepribadian mendalam untuk {name} berdasarkan Big Five:\n"
            f"- Profil: {scores_detail}\n"
            f"- Arketipe kepribadian: {arch.get('name', '')}\n"
            f"- Rekomendasi karir: {', '.join(careers)}\n\n"
            f"Tulis interpretasi dalam 4 paragraf Bahasa Indonesia:\n"
            f"1. Paragraf 1: Gambarkan kepribadian {name} secara keseluruhan berdasarkan arketipe\n"
            f"2. Paragraf 2: Kekuatan kepribadian dan bagaimana itu membantu dalam kehidupan\n"
            f"3. Paragraf 3: Area yang bisa dikembangkan dan tips praktis\n"
            f"4. Paragraf 4: Kesesuaian karir dan motivasi ke depan\n\n"
            f"Gunakan bahasa yang hangat, personal, dan memotivasi. Jangan gunakan bullet points atau heading. "
            f"Tulis langsung paragrafnya."
        )

    scores_detail = ', '.join(
        f"{TRAIT_NAMES_EN[t]} ({score_label_en(bf.get(t,50))})"
        for t in 'OCEAN'
    )
    return (
        f"You are a warm and empathetic professional psychologist.\n\n"
        f"Provide an in-depth personality interpretation for {name} based on Big Five:\n"
        f"- Profile: {scores_detail}\n"
        f"- Personality archetype: {arch.get('name', '')}\n"
        f"- Career recommendations: {', '.join(careers)}\n\n"
        f"Write an interpretation in 4 paragraphs:\n"
        f"1. Describe {name}\'s overall personality based on the archetype\n"
        f"2. Personality strengths and how they help in life\n"
        f"3. Areas to develop and practical tips\n"
        f"4. Career fit and motivation going forward\n\n"
        f"Use warm, personal, and motivating language. No bullet points or headings. "
        f"Write the paragraphs directly."
    )


def _iq_prompt(analysis: dict, lang: str) -> str:
    iq      = analysis.get('iq', 0)
    label   = analysis.get('label', '')
    pct     = analysis.get('percentile', 0)
    correct = analysis.get('correct', 0)
    total   = analysis.get('total', 40)
    user    = analysis.get('user', {})
    name    = user.get('name', 'pengguna') if user else 'pengguna'

    cog     = analysis.get('cognitive', {})
    sorted_cog = sorted(cog.items(), key=lambda x: x[1].get('score_pct', 0), reverse=True)
    top2    = [d for d, _ in sorted_cog[:2]]
    bottom2 = [d for d, _ in sorted_cog[-2:]]
    top_str    = ', '.join(top2)
    bottom_str = ', '.join(bottom2)

    if lang == 'id':
        return (
            f"Kamu adalah psikolog kognitif profesional yang hangat dan empatik.\n\n"
            f"Berikan interpretasi mendalam hasil tes IQ untuk {name} dengan data berikut:\n"
            f"- Skor IQ: {iq} (kategori: {label})\n"
            f"- Persentil: {pct} (lebih tinggi dari {pct}% populasi)\n"
            f"- Jawaban benar: {correct} dari {total} soal\n"
            f"- Domain kognitif terkuat: {top_str}\n"
            f"- Domain yang perlu dikembangkan: {bottom_str}\n\n"
            f"Tulis interpretasi dalam 4 paragraf Bahasa Indonesia:\n"
            f"1. Paragraf 1: Sambut {name} dan jelaskan makna skor IQ-nya secara positif\n"
            f"2. Paragraf 2: Analisis kekuatan kognitif berdasarkan domain terkuat\n"
            f"3. Paragraf 3: Saran konkret untuk mengembangkan domain yang masih lemah\n"
            f"4. Paragraf 4: Motivasi dan langkah ke depan yang bisa dilakukan\n\n"
            f"Gunakan bahasa yang hangat, personal, dan memotivasi. Jangan gunakan bullet points atau heading. "
            f"Tulis langsung paragrafnya."
        )
    return (
        f"You are a warm and empathetic professional cognitive psychologist.\n\n"
        f"Provide an in-depth interpretation of {name}\'s IQ test results:\n"
        f"- IQ Score: {iq} (category: {label})\n"
        f"- Percentile: {pct} (higher than {pct}% of the population)\n"
        f"- Correct answers: {correct} out of {total}\n"
        f"- Strongest cognitive domains: {top_str}\n"
        f"- Domains to develop: {bottom_str}\n\n"
        f"Write an interpretation in 4 paragraphs:\n"
        f"1. Welcome {name} and explain the meaning of their IQ score positively\n"
        f"2. Analyze cognitive strengths based on the strongest domains\n"
        f"3. Concrete suggestions to develop weaker domains\n"
        f"4. Motivation and actionable next steps\n\n"
        f"Use warm, personal, and motivating language. No bullet points or headings. "
        f"Write the paragraphs directly."
    )


# ══════════════════════════════════════════════════════════════
# API CALL (synchronous, dipakai dari thread)
# ══════════════════════════════════════════════════════════════
def _call_gemini(prompt: str) -> str:
    if not _API_KEY or _API_KEY == 'MASUKKAN_API_KEY_KAMU_DISINI':
        raise ValueError('API key belum diisi.')

    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.75, 'maxOutputTokens': 1500},
    }).encode('utf-8')

    last_err = None
    for model in GEMINI_MODELS:
        url = GEMINI_BASE.format(model=model, key=_API_KEY)
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data       = json.loads(resp.read().decode('utf-8'))
            candidates = data.get('candidates', [])
            if not candidates:
                raise ValueError('Tidak ada respons.')
            parts = candidates[0].get('content', {}).get('parts', [])
            if not parts:
                raise ValueError('Respons kosong.')
            return parts[0].get('text', '').strip()
        except urllib.error.HTTPError as e:
            last_err = f'HTTP {e.code} ({model})'
            continue
        except Exception as e:
            last_err = str(e)
            break

    raise ValueError(f'Semua model gagal. Error: {last_err}')


# ══════════════════════════════════════════════════════════════
# QTHREAD WORKER — thread-safe UI update
# ══════════════════════════════════════════════════════════════
def _run_async(prompt: str, on_done, on_error):
    """
    Jalankan Gemini di QThread, callback on_done/on_error
    dipanggil di main thread via Qt Signal.
    """
    from PyQt5.QtCore import QThread, pyqtSignal, QObject

    class _Worker(QObject):
        done  = pyqtSignal(str)
        error = pyqtSignal(str)

        def __init__(self, prompt):
            super().__init__()
            self._prompt = prompt

        def run(self):
            try:
                text = _call_gemini(self._prompt)
                self.done.emit(text)
            except Exception as e:
                self.error.emit(str(e))

    # Simpan referensi supaya tidak di-GC
    thread = QThread()
    worker = _Worker(prompt)
    worker.moveToThread(thread)

    # Connect signals
    thread.started.connect(worker.run)
    if on_done:
        worker.done.connect(on_done)
    if on_error:
        worker.error.connect(on_error)

    # Cleanup setelah selesai
    worker.done.connect(thread.quit)
    worker.error.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)

    # Simpan di module level supaya tidak di-GC sebelum selesai
    _active_threads.append(thread)
    worker.done.connect(lambda _: _cleanup(thread))
    worker.error.connect(lambda _: _cleanup(thread))

    thread.start()
    # Simpan worker juga
    thread._worker = worker


_active_threads = []

def _cleanup(thread):
    try:
        _active_threads.remove(thread)
    except ValueError:
        pass


# ══════════════════════════════════════════════════════════════
# PUBLIC ASYNC API
# ══════════════════════════════════════════════════════════════
def explain_bigfive_async(analysis: dict, lang: str, on_done=None, on_error=None):
    _run_async(_bf_prompt(analysis, lang), on_done, on_error)

def explain_iq_async(analysis: dict, lang: str, on_done=None, on_error=None):
    _run_async(_iq_prompt(analysis, lang), on_done, on_error)

def explain_combined_async(analysis: dict, lang: str, on_done=None, on_error=None):
    _run_async(_bf_prompt(analysis, lang), on_done, on_error)


# ══════════════════════════════════════════════════════════════
# SYNC API (untuk PDF export)
# ══════════════════════════════════════════════════════════════
def explain_bigfive(analysis: dict, lang: str) -> str:
    return _call_gemini(_bf_prompt(analysis, lang))

def explain_iq(analysis: dict, lang: str) -> str:
    return _call_gemini(_iq_prompt(analysis, lang))

def explain_combined(analysis: dict, lang: str) -> str:
    return _call_gemini(_bf_prompt(analysis, lang))