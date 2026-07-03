import json
from database import get_connection


def export_jobs_to_json():

    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            title,
            company,
            location,
            description,
            url,
            source,
            score,
            created_at
        FROM jobs
        ORDER BY score DESC, created_at DESC
    """)

    rows = cursor.fetchall()

    jobs = [dict(row) for row in rows]

    with open(
        "data/jobs.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=4
        )

    conn.close()

    print(f"JSON exportado com {len(jobs)} vagas.")
