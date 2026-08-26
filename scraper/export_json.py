import json
from datetime import datetime, timezone
from database import get_connection
from job_category import categorize


def _to_iso8601(sqlite_timestamp):
    """
    Converte o formato do SQLite ("YYYY-MM-DD HH:MM:SS", em UTC) para
    ISO 8601 ("YYYY-MM-DDTHH:MM:SSZ"), que é o formato que o
    JavaScript (new Date(...)) e a generalidade das APIs/frontends
    conseguem interpretar directamente sem ambiguidade de fuso horário.
    """
    if not sqlite_timestamp:
        return None
    return sqlite_timestamp.replace(" ", "T") + "Z"


def _days_since(sqlite_timestamp):
    """
    Calcula há quantos dias completos uma vaga foi vista pela primeira
    vez (created_at), para o site poder mostrar por exemplo "Publicada
    há 5 dias" sem ter de fazer essa conta no frontend.
    """
    if not sqlite_timestamp:
        return None
    try:
        seen = datetime.strptime(sqlite_timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    delta = datetime.now(timezone.utc) - seen
    return max(delta.days, 0)


def export_jobs_to_json():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            job_id,
            title,
            company,
            location,
            description,
            url,
            source,
            score,
            created_at,
            last_seen_at
        FROM jobs
        ORDER BY score DESC, created_at DESC
    """)

    rows = cursor.fetchall()

    jobs = []

    for row in rows:
        job = dict(row)

        title = job.get("title") or ""
        description = job.get("description") or ""
        location = job.get("location") or "Moçambique"

        # Se a descrição for apenas uma repetição do título (comum nas
        # fontes que não fornecem descrição própria), não faz sentido
        # expor o mesmo texto duas vezes no site - fica a null, para o
        # frontend saber que não há descrição adicional a mostrar.
        clean_description = description if description.strip() != title.strip() else None

        # Localização como lista, além da string original, para o site
        # poder filtrar por província/cidade sem ter de reprocessar o
        # texto (ex.: "Cabo Delgado, Pemba" -> ["Cabo Delgado", "Pemba"]).
        locations_list = [loc.strip() for loc in location.split(",") if loc.strip()]

        jobs.append({
            "job_id": job.get("job_id"),
            "title": title,
            "company": job.get("company") or "Desconhecida",
            "location": location,
            "locations": locations_list,
            "category": categorize(title, description),
            "description": clean_description,
            "url": job.get("url"),
            "source": job.get("source"),
            "score": job.get("score", 0),
            "scraped_at": _to_iso8601(job.get("created_at")),
            # Mantido por compatibilidade com integrações já existentes
            # que possam estar a ler o campo "created_at" directamente.
            "created_at": job.get("created_at"),
            # Novos campos, só significativos desde que a base de dados
            # passou a ser "semeada" com o histórico entre execuções
            # (ver database.seed_from_previous_export): antes disso,
            # first_seen_at e last_seen_at eram sempre iguais a
            # scraped_at, porque cada execução começava do zero.
            "first_seen_at": _to_iso8601(job.get("created_at")),
            "last_seen_at": _to_iso8601(job.get("last_seen_at")),
            "days_since_first_seen": _days_since(job.get("created_at")),
        })

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
