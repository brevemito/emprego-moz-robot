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

            -- Última vez que esta vaga foi vista/confirmada activa numa
            -- execução do scraper (seja porque foi inserida agora, seja
            -- porque já existia e voltou a aparecer). Usado para detectar
            -- vagas que já desapareceram da fonte original (ver
            -- remove_stale_jobs) e para expor "há quanto tempo está
            -- aberta" ao site.
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

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

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at
        ON jobs(last_seen_at)
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
    """
    Insere uma vaga nova. Se já existir (mesmo hash título+empresa+URL),
    NÃO insere duplicado - em vez disso, actualiza last_seen_at (e
    score/localização/descrição, que podem ter melhorado) na linha já
    existente, para registar que a vaga continua confirmada como activa
    nesta execução. Devolve True se foi uma inserção nova, False se já
    existia (e foi apenas actualizada).
    """

    conn = get_connection()
    cursor = conn.cursor()

    job_hash = generate_job_hash(job)
    job_id = generate_job_id(job)

    try:

        cursor.execute("""
            INSERT INTO jobs(
                job_id, title, company, location, description,
                url, source, score, hash, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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

        # Já existe uma vaga com este hash - actualizamos apenas
        # last_seen_at (confirma que continua activa) e alguns campos
        # que podem ter melhorado entretanto (score, localização,
        # descrição), sem tocar em created_at (mantém a data em que foi
        # vista pela primeira vez).
        cursor.execute("""
            UPDATE jobs
            SET last_seen_at = CURRENT_TIMESTAMP,
                score = ?,
                location = ?,
                description = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE hash = ?
        """, (
            job.get("score", 0),
            job.get("location"),
            job.get("description"),
            job_hash
        ))

        conn.commit()
        return False

    finally:

        conn.close()


# =========================
# SEMENTEIRA A PARTIR DE data/jobs.json (histórico entre execuções)
# =========================
#
# Como a base de dados SQLite é recriada do zero em cada execução do
# GitHub Actions (não há ficheiro persistente entre execuções), usamos
# o próprio data/jobs.json - que ESSE sim fica commitado no repositório
# a cada execução - como fonte de histórico. No início de cada
# execução, "semeamos" a base de dados fresca com o conteúdo do último
# jobs.json exportado, preservando a data original em que cada vaga foi
# vista pela primeira vez (created_at). Isto dá:
#   - deduplicação real entre dias (não só dentro da mesma execução)
#   - possibilidade de saber há quanto tempo uma vaga está aberta
#   - detecção de vagas que desapareceram da fonte (ver remove_stale_jobs)

def seed_from_previous_export(jobs: List[Dict]):
    """
    Recebe a lista de vagas do jobs.json anterior (já parseado) e
    insere cada uma na base de dados fresca, preservando o created_at
    original. Vagas cujo hash já exista (não deve acontecer numa base
    de dados recém-criada, mas por segurança) são ignoradas.

    Devolve o número de vagas semeadas com sucesso.
    """
    if not jobs:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    seeded = 0

    for job in jobs:

        job_hash = generate_job_hash(job)
        job_id = job.get("job_id") or generate_job_id(job)

        # Preferimos o campo "created_at" (formato SQLite original); se
        # só existir "scraped_at" (ISO 8601), convertê-lo de volta.
        original_created_at = job.get("created_at")
        if not original_created_at and job.get("scraped_at"):
            original_created_at = job["scraped_at"].replace("T", " ").rstrip("Z")

        last_seen_at = original_created_at

        try:
            cursor.execute("""
                INSERT INTO jobs(
                    job_id, title, company, location, description,
                    url, source, score, hash, created_at, last_seen_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,
                        COALESCE(?, CURRENT_TIMESTAMP),
                        COALESCE(?, CURRENT_TIMESTAMP))
            """, (
                job_id,
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("description"),
                job.get("url"),
                job.get("source"),
                job.get("score", 0),
                job_hash,
                original_created_at,
                last_seen_at
            ))
            seeded += 1

        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()

    return seeded


# =========================
# EXPIRAÇÃO DE VAGAS DESAPARECIDAS DA FONTE
# =========================

def remove_stale_jobs(cutoff_days=21):
    """
    Remove vagas cujo last_seen_at é mais antigo do que cutoff_days -
    ou seja, vagas que já não foram encontradas na fonte original há
    mais desse número de dias (provavelmente já preenchidas ou
    retiradas). Devolve a lista das vagas removidas (para reporting).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, company, source, last_seen_at
        FROM jobs
        WHERE last_seen_at < datetime('now', ?)
    """, (f"-{cutoff_days} days",))

    stale = [dict(r) for r in cursor.fetchall()]

    if stale:
        ids = [row["id"] for row in stale]
        cursor.executemany("DELETE FROM jobs WHERE id = ?", [(i,) for i in ids])
        conn.commit()

    conn.close()

    return stale


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
