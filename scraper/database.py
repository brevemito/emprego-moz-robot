import sqlite3
from pathlib import Path
import hashlib
from typing import Dict, List, Optional

# =========================
# CONFIGURAÇÃO DA BASE DE DADOS
# =========================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "jobs.db"


# =========================
# CONEXÃO
# =========================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# INICIALIZAÇÃO
# =========================

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            url TEXT NOT NULL,
            source TEXT,
            score INTEGER DEFAULT 0,
            hash TEXT UNIQUE,
            published INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(hash)
    """)

    conn.commit()
    conn.close()

    print("Base de dados inicializada com sucesso.")


# =========================
# HASH DA VAGA
# =========================

def generate_job_hash(job: Dict) -> str:
    raw = (
        (job.get("title") or "") +
        (job.get("company") or "") +
        (job.get("url") or "")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# =========================
# INSERIR VAGA (ANTI-DUPLICADOS)
# =========================

def insert_job(job: Dict) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    job_hash = generate_job_hash(job)

    try:
        cursor.execute("""
            INSERT INTO jobs (
                title,
                company,
                location,
                description,
                url,
                source,
                score,
                hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("description"),
            job.get("url"),
            job.get("source"),
            job.get("score", 0),
            job_hash
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        # duplicado (hash ou url repetido)
        return False

    finally:
        conn.close()


# =========================
# BUSCAR VAGAS NÃO PUBLICADAS
# =========================

def get_unpublished_jobs(limit: int = 20) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM jobs
        WHERE published = 0
        ORDER BY score DESC, created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =========================
# MARCAR COMO PUBLICADO
# =========================

def mark_as_published(job_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET published = 1
        WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()


# =========================
# ESTATÍSTICAS (OPCIONAL)
# =========================

def count_jobs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM jobs")
    total = cursor.fetchone()["total"]

    conn.close()
    return total
