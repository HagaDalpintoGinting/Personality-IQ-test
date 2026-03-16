"""
core/database.py
────────────────────────────────────────────────────────────
SQLite data layer.

Schema:
  users          — profil pengguna (nama, PIN hash)
  test_sessions  — setiap kali user ambil tes
  answers        — jawaban per soal per sesi
  scores         — skor akhir per dimensi per sesi

Semua fungsi mengembalikan dict / list of dict, bukan Row object,
sehingga mudah dipakai di seluruh app tanpa import sqlite3.
────────────────────────────────────────────────────────────
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path('data/assessment.db')


# ══════════════════════════════════════════════════════════════
# KONEKSI & INISIALISASI
# ══════════════════════════════════════════════════════════════
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def init_db():
    """Buat semua tabel jika belum ada. Dipanggil satu kali saat startup."""
    con = _connect()
    cur = con.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        pin_hash    TEXT    NOT NULL,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS test_sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        test_type   TEXT    NOT NULL,   -- 'iq' | 'bigfive' | 'combined'
        lang        TEXT    NOT NULL DEFAULT 'id',
        taken_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        duration_s  INTEGER             -- detik pengerjaan
    );

    CREATE TABLE IF NOT EXISTS answers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER NOT NULL REFERENCES test_sessions(id),
        question_id TEXT    NOT NULL,   -- e.g. 'O_01', 'IQ_DA_1'
        dimension   TEXT,               -- 'O','C','E','A','N' atau kategori IQ
        value       INTEGER NOT NULL,   -- jawaban mentah user (1-5 atau 0-3)
        is_correct  INTEGER,            -- NULL untuk BF, 0/1 untuk IQ
        difficulty  INTEGER             -- untuk IQ weighted scoring
    );

    CREATE TABLE IF NOT EXISTS scores (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id      INTEGER NOT NULL REFERENCES test_sessions(id),
        dimension       TEXT    NOT NULL,  -- 'O','C','E','A','N' atau 'IQ','fluid',dll
        raw_score       REAL    NOT NULL,
        normalized      REAL    NOT NULL,  -- 0-100
        percentile      REAL    NOT NULL,
        level           TEXT               -- label kategori
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_user ON test_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);
    CREATE INDEX IF NOT EXISTS idx_scores_session  ON scores(session_id);
    CREATE INDEX IF NOT EXISTS idx_scores_dim      ON scores(dimension);
    """)

    con.commit()
    con.close()


# ══════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════
def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.strip().encode()).hexdigest()


def register_user(name: str, pin: str) -> dict | None:
    """
    Buat user baru. Return dict user jika berhasil, None jika nama sudah ada.
    """
    con = _connect()
    try:
        cur = con.execute(
            'INSERT INTO users (name, pin_hash) VALUES (?, ?)',
            (name.strip(), _hash_pin(pin))
        )
        con.commit()
        user = dict(con.execute(
            'SELECT * FROM users WHERE id = ?', (cur.lastrowid,)
        ).fetchone())
        return user
    except sqlite3.IntegrityError:
        return None
    finally:
        con.close()


def login_user(name: str, pin: str) -> dict | None:
    """Return dict user jika nama+PIN cocok, None jika tidak."""
    con = _connect()
    row = con.execute(
        'SELECT * FROM users WHERE name = ? AND pin_hash = ?',
        (name.strip(), _hash_pin(pin))
    ).fetchone()
    con.close()
    return dict(row) if row else None


def get_user(user_id: int) -> dict | None:
    con = _connect()
    row = con.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def user_exists(name: str) -> bool:
    con = _connect()
    row = con.execute('SELECT id FROM users WHERE name = ?', (name.strip(),)).fetchone()
    con.close()
    return row is not None


def list_users() -> list[dict]:
    """Return semua user — untuk dropdown login."""
    con = _connect()
    rows = con.execute('SELECT id, name, created_at FROM users ORDER BY name').fetchall()
    con.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
# TEST SESSIONS
# ══════════════════════════════════════════════════════════════
def create_session(user_id: int, test_type: str, lang: str = 'id') -> int:
    """Buat sesi baru, return session_id."""
    con = _connect()
    cur = con.execute(
        'INSERT INTO test_sessions (user_id, test_type, lang) VALUES (?, ?, ?)',
        (user_id, test_type, lang)
    )
    con.commit()
    sid = cur.lastrowid
    con.close()
    return sid


def finish_session(session_id: int, duration_s: int):
    """Update durasi pengerjaan."""
    con = _connect()
    con.execute(
        'UPDATE test_sessions SET duration_s = ? WHERE id = ?',
        (duration_s, session_id)
    )
    con.commit()
    con.close()


def get_sessions(user_id: int, test_type: str = None, limit: int = 50) -> list[dict]:
    """
    Return riwayat sesi user, urut terbaru.
    Filter test_type jika diisi.
    """
    con = _connect()
    if test_type:
        rows = con.execute(
            '''SELECT ts.*, u.name as user_name
               FROM test_sessions ts JOIN users u ON u.id = ts.user_id
               WHERE ts.user_id = ? AND ts.test_type = ?
               ORDER BY ts.taken_at DESC LIMIT ?''',
            (user_id, test_type, limit)
        ).fetchall()
    else:
        rows = con.execute(
            '''SELECT ts.*, u.name as user_name
               FROM test_sessions ts JOIN users u ON u.id = ts.user_id
               WHERE ts.user_id = ?
               ORDER BY ts.taken_at DESC LIMIT ?''',
            (user_id, limit)
        ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_session(session_id: int) -> dict | None:
    con = _connect()
    row = con.execute(
        'SELECT * FROM test_sessions WHERE id = ?', (session_id,)
    ).fetchone()
    con.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════
# ANSWERS
# ══════════════════════════════════════════════════════════════
def save_answers(session_id: int, answer_rows: list[dict]):
    """
    answer_rows: list of dict dengan keys:
      question_id, dimension, value, is_correct (opsional), difficulty (opsional)
    """
    con = _connect()
    con.executemany(
        '''INSERT INTO answers (session_id, question_id, dimension, value, is_correct, difficulty)
           VALUES (:session_id, :question_id, :dimension, :value, :is_correct, :difficulty)''',
        [{**r, 'session_id': session_id,
          'is_correct': r.get('is_correct'),
          'difficulty': r.get('difficulty')} for r in answer_rows]
    )
    con.commit()
    con.close()


def get_answers(session_id: int) -> list[dict]:
    con = _connect()
    rows = con.execute(
        'SELECT * FROM answers WHERE session_id = ? ORDER BY id', (session_id,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
# SCORES
# ══════════════════════════════════════════════════════════════
def save_scores(session_id: int, score_rows: list[dict]):
    """
    score_rows: list of dict:
      dimension, raw_score, normalized, percentile, level
    """
    con = _connect()
    con.executemany(
        '''INSERT INTO scores (session_id, dimension, raw_score, normalized, percentile, level)
           VALUES (:session_id, :dimension, :raw_score, :normalized, :percentile, :level)''',
        [{**r, 'session_id': session_id, 'level': r.get('level', '')} for r in score_rows]
    )
    con.commit()
    con.close()


def get_scores(session_id: int) -> dict[str, dict]:
    """Return {dimension: {raw, normalized, percentile, level}}"""
    con = _connect()
    rows = con.execute(
        'SELECT * FROM scores WHERE session_id = ?', (session_id,)
    ).fetchall()
    con.close()
    return {r['dimension']: dict(r) for r in rows}


def get_score_history(user_id: int, dimension: str, test_type: str = 'bigfive', limit: int = 20) -> list[dict]:
    """
    Return riwayat skor satu dimensi untuk chart trend.
    [{'taken_at': ..., 'normalized': ..., 'percentile': ...}, ...]
    """
    con = _connect()
    rows = con.execute(
        '''SELECT ts.taken_at, s.normalized, s.percentile, s.level
           FROM scores s
           JOIN test_sessions ts ON ts.id = s.session_id
           WHERE ts.user_id = ? AND s.dimension = ? AND ts.test_type = ?
           ORDER BY ts.taken_at ASC LIMIT ?''',
        (user_id, dimension, test_type, limit)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
# STATISTIK POPULASI (dari semua user)
# ══════════════════════════════════════════════════════════════
def get_population_stats(dimension: str, test_type: str = 'bigfive') -> dict:
    """
    Return {mean, std, count} dari semua skor dimensi tertentu.
    Dipakai untuk perbandingan "vs pengguna lain".
    """
    con = _connect()
    row = con.execute(
        '''SELECT AVG(s.normalized) as mean,
                  COUNT(*) as count
           FROM scores s
           JOIN test_sessions ts ON ts.id = s.session_id
           WHERE s.dimension = ? AND ts.test_type = ?''',
        (dimension, test_type)
    ).fetchone()
    con.close()
    if row and row['count'] > 0:
        return {'mean': row['mean'], 'count': row['count']}
    return {'mean': 50.0, 'count': 0}


def get_all_population_stats(test_type: str = 'bigfive') -> dict[str, dict]:
    """Return stats untuk semua dimensi sekaligus."""
    con = _connect()
    rows = con.execute(
        '''SELECT s.dimension, AVG(s.normalized) as mean, COUNT(*) as count
           FROM scores s
           JOIN test_sessions ts ON ts.id = s.session_id
           WHERE ts.test_type = ?
           GROUP BY s.dimension''',
        (test_type,)
    ).fetchall()
    con.close()
    return {r['dimension']: {'mean': r['mean'], 'count': r['count']} for r in rows}


def get_total_users() -> int:
    con = _connect()
    n = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    con.close()
    return n


def get_total_sessions() -> int:
    con = _connect()
    n = con.execute('SELECT COUNT(*) FROM test_sessions').fetchone()[0]
    con.close()
    return n


# ══════════════════════════════════════════════════════════════
# FULL SESSION DATA (untuk load hasil & PDF)
# ══════════════════════════════════════════════════════════════
def get_full_session(session_id: int) -> dict | None:
    """
    Return semua data satu sesi:
    {session, user, answers, scores}
    """
    session = get_session(session_id)
    if not session:
        return None
    user    = get_user(session['user_id'])
    answers = get_answers(session_id)
    scores  = get_scores(session_id)
    return {
        'session': session,
        'user':    user,
        'answers': answers,
        'scores':  scores,
    }


def get_latest_session(user_id: int, test_type: str) -> dict | None:
    """Return sesi terakhir user untuk test_type tertentu."""
    sessions = get_sessions(user_id, test_type=test_type, limit=1)
    if not sessions:
        return None
    return get_full_session(sessions[0]['id'])


# ══════════════════════════════════════════════════════════════
# ADMIN FUNCTIONS
# ══════════════════════════════════════════════════════════════
_ADMIN_PASSWORD_HASH = None

def set_admin_password(password: str):
    """Set admin password (hashed). Dipanggil saat setup."""
    global _ADMIN_PASSWORD_HASH
    _ADMIN_PASSWORD_HASH = hashlib.sha256(password.strip().encode()).hexdigest()

def verify_admin(password: str) -> bool:
    """Verifikasi password admin."""
    if _ADMIN_PASSWORD_HASH is None:
        # Default password: 'admin123' kalau belum diset
        default = hashlib.sha256('admin123'.encode()).hexdigest()
        return hashlib.sha256(password.strip().encode()).hexdigest() == default
    return hashlib.sha256(password.strip().encode()).hexdigest() == _ADMIN_PASSWORD_HASH

def get_all_users() -> list:
    """Return semua user dengan summary stats."""
    con = _connect()
    rows = con.execute('''
        SELECT u.id, u.name, u.created_at,
               COUNT(DISTINCT s.id) as total_sessions,
               MAX(s.taken_at) as last_session
        FROM users u
        LEFT JOIN test_sessions s ON s.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''').fetchall()
    con.close()
    return [dict(r) for r in rows]

def get_user_summary(user_id: int) -> dict:
    """Return ringkasan lengkap satu user: sessions + latest scores."""
    con = _connect()
    sessions = con.execute('''
        SELECT s.id, s.test_type, s.lang, s.taken_at, s.duration_s,
               GROUP_CONCAT(sc.dimension || ':' || ROUND(sc.normalized,1), '|') as scores_str
        FROM test_sessions s
        LEFT JOIN scores sc ON sc.session_id = s.id
        WHERE s.user_id = ?
        GROUP BY s.id
        ORDER BY s.taken_at DESC
    ''', (user_id,)).fetchall()
    con.close()
    return [dict(s) for s in sessions]

def get_admin_stats() -> dict:
    """Return statistik global untuk dashboard admin."""
    con = _connect()
    total_users    = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_sessions = con.execute('SELECT COUNT(*) FROM test_sessions').fetchone()[0]
    iq_sessions    = con.execute("SELECT COUNT(*) FROM test_sessions WHERE test_type='iq'").fetchone()[0]
    bf_sessions    = con.execute("SELECT COUNT(*) FROM test_sessions WHERE test_type='bigfive'").fetchone()[0]

    # Rata-rata IQ
    avg_iq = con.execute('''
        SELECT AVG(normalized) FROM scores
        WHERE dimension='IQ'
    ''').fetchone()[0]

    # Distribusi IQ
    iq_dist = con.execute('''
        SELECT level, COUNT(*) as cnt FROM scores
        WHERE dimension='IQ'
        GROUP BY level ORDER BY cnt DESC
    ''').fetchall()

    # Rata-rata OCEAN
    ocean_avgs = {}
    for t in 'OCEAN':
        row = con.execute(
            'SELECT AVG(normalized) FROM scores WHERE dimension=?', (t,)
        ).fetchone()
        ocean_avgs[t] = round(row[0], 1) if row[0] else 0

    # Sesi per hari (7 hari terakhir)
    daily = con.execute('''
        SELECT DATE(taken_at) as day, COUNT(*) as cnt
        FROM test_sessions
        WHERE taken_at >= DATE('now', '-7 days')
        GROUP BY day ORDER BY day
    ''').fetchall()

    con.close()
    return {
        'total_users':    total_users,
        'total_sessions': total_sessions,
        'iq_sessions':    iq_sessions,
        'bf_sessions':    bf_sessions,
        'avg_iq':         round(avg_iq, 1) if avg_iq else 0,
        'iq_dist':        [dict(r) for r in iq_dist],
        'ocean_avgs':     ocean_avgs,
        'daily_sessions': [dict(r) for r in daily],
    }

def delete_user(user_id: int) -> bool:
    """Hapus user beserta semua data terkait."""
    con = _connect()
    try:
        # Hapus dalam urutan: answers → scores → sessions → user
        session_ids = [r[0] for r in con.execute(
            'SELECT id FROM test_sessions WHERE user_id=?', (user_id,)
        ).fetchall()]
        for sid in session_ids:
            con.execute('DELETE FROM answers WHERE session_id=?', (sid,))
            con.execute('DELETE FROM scores   WHERE session_id=?', (sid,))
        con.execute('DELETE FROM test_sessions WHERE user_id=?', (user_id,))
        con.execute('DELETE FROM users WHERE id=?', (user_id,))
        con.commit()
        return True
    except Exception:
        con.rollback()
        return False
    finally:
        con.close()

def reset_user_data(user_id: int) -> bool:
    """Hapus semua sesi user tapi pertahankan akun."""
    con = _connect()
    try:
        session_ids = [r[0] for r in con.execute(
            'SELECT id FROM test_sessions WHERE user_id=?', (user_id,)
        ).fetchall()]
        for sid in session_ids:
            con.execute('DELETE FROM answers WHERE session_id=?', (sid,))
            con.execute('DELETE FROM scores   WHERE session_id=?', (sid,))
        con.execute('DELETE FROM test_sessions WHERE user_id=?', (user_id,))
        con.commit()
        return True
    except Exception:
        con.rollback()
        return False
    finally:
        con.close()

def export_all_data() -> list:
    """Return semua data untuk export Excel."""
    con = _connect()
    rows = con.execute('''
        SELECT
            u.name as user_name, u.created_at as user_created,
            s.test_type, s.lang, s.taken_at, s.duration_s,
            sc.dimension, sc.raw_score, sc.normalized, sc.percentile, sc.level
        FROM users u
        JOIN test_sessions s ON s.user_id = u.id
        JOIN scores sc ON sc.session_id = s.id
        ORDER BY u.name, s.taken_at, sc.dimension
    ''').fetchall()
    con.close()
    return [dict(r) for r in rows]