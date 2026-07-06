import sqlite3
from pathlib import Path
import hashlib
import uuid
from typing import Dict, List

# =========================
# CONFIGURAÇÃO
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

            job_id TEXT UNIQUE,

            title TEXT NOT NULL,

            company TEXT,

            location TEXT,

            description TEXT,

            url TEXT NOT NULL,

            source TEXT,

            score INTEGER DEFAULT 0,

            hash TEXT UNIQUE,

            published INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_hash
        ON jobs(hash)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_job_id
        ON jobs(job_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_source
        ON jobs(source)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_score
        ON jobs(score)
    """)

    conn.commit()
    conn.close()

    print("Base de dados inicializada com sucesso.")


# =========================
# ID PÚBLICO
# =========================

def generate_job_id(job: Dict) -> str:

    base = (
        (job.get("source") or "") +
        (job.get("title") or "") +
        (job.get("company") or "")
    )

    short = hashlib.sha1(base.encode()).hexdigest()[:12]

    return f"{job.get('source','job')}_{short}"


# =========================
# HASH ANTI-DUPLICADOS
# =========================

def generate_job_hash(job: Dict) -> str:

    raw = (
        (job.get("title") or "") +
        (job.get("company") or "") +
        (job.get("url") or "")
    )

    return hashlib.sha256(raw.encode()).hexdigest()


# =========================
# INSERÇÃO
# =========================

def insert_job(job: Dict):

    conn = get_connection()
    cursor = conn.cursor()

    job_hash = generate_job_hash(job)
    job_id = generate_job_id(job)

    try:

        cursor.execute("""

            INSERT INTO jobs(

                job_id,

                title,

                company,

                location,

                description,

                url,

                source,

                score,

                hash

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            job_id,

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

        return False

    finally:

        conn.close()


# =========================
# VAGAS NÃO PUBLICADAS
# =========================

def get_unpublished_jobs(limit=20):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM jobs

        WHERE published = 0

        ORDER BY score DESC, created_at DESC

        LIMIT ?

    """, (limit,))

    jobs = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jobs


# =========================
# PUBLICAR
# =========================

def mark_as_published(job_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        UPDATE jobs

        SET published = 1,

            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?

    """, (job_id,))

    conn.commit()

    conn.close()


# =========================
# CONTAGEM
# =========================

def count_jobs():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")

    total = cursor.fetchone()[0]

    conn.close()

    return total


# =========================
# LISTAR TODAS
# =========================

def get_all_jobs():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM jobs

        ORDER BY score DESC, created_at DESC

    """)

    jobs = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jobs
