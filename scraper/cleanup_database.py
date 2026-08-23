# Script de manutenção - Limpeza e reformatação retroactiva
#
# Este script tem dois objectivos sobre a base de dados já existente
# (vagas guardadas ANTES das melhorias mais recentes):
#
#   1. REMOVER vagas que já não passam no JobValidator actual (concursos,
#      páginas institucionais, filtros de menu, etc. que foram inseridos
#      antes de o filtro existir ou ser melhorado).
#
#   2. REFORMATAR as vagas válidas que restam: título em Title Case
#      (preservando siglas como M/F, HSE, QHSE, TI) e localização mais
#      específica quando encontrada no texto (ex.: "Moçambique" ->
#      "Cabo Delgado, Pemba"), usando exactamente a mesma lógica que já
#      se aplica a vagas novas em main.py.
#
# Como o hash de deduplicação (ver database.generate_job_hash) inclui o
# título, sempre que o título é reformatado o hash também é recalculado
# e actualizado na base de dados - caso contrário, futuras execuções do
# scraper poderiam inserir a MESMA vaga em duplicado, porque o hash
# guardado (calculado a partir do título antigo) deixaria de bater
# certo com o hash calculado a partir do título novo já limpo.
#
# No final, volta a exportar o jobs.json já limpo e reformatado.
#
# Uso:
#   cd scraper
#   python3 cleanup_database.py

from database import get_connection, generate_job_hash
from export_json import export_jobs_to_json
from main import is_real_job
from text_cleanup import smart_title_case, improve_location


def cleanup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, company, location, description, url, source, hash FROM jobs")
    rows = cursor.fetchall()

    to_delete = []
    to_reformat = []

    for row in rows:
        job = dict(row)

        if not is_real_job(job):
            to_delete.append((job["id"], job["title"]))
            continue

        original_title = job["title"] or ""
        original_location = job["location"] or ""

        new_title = smart_title_case(original_title)
        new_location = improve_location(original_location, new_title, job.get("description"))

        if new_title != original_title or new_location != original_location:
            new_hash = job["hash"]
            if new_title != original_title:
                # O título mudou, por isso o hash de deduplicação (que
                # inclui o título) tem de ser recalculado, para não
                # ficar dessincronizado com o que futuras execuções do
                # scraper vão calcular para a mesma vaga.
                new_hash = generate_job_hash({
                    "title": new_title,
                    "company": job.get("company"),
                    "url": job.get("url")
                })

            to_reformat.append((job["id"], original_title, new_title, original_location, new_location, new_hash))

    # ---- Remoção de vagas inválidas ----
    if not to_delete:
        print("Nenhum registo antigo para remover. Base de dados já está limpa.")
    else:
        print(f"A remover {len(to_delete)} registo(s) que já não passam o filtro actual:\n")
        for job_id, title in to_delete:
            print(f"  🗑️  [{job_id}] {title}")

        ids = [job_id for job_id, _ in to_delete]
        cursor.executemany("DELETE FROM jobs WHERE id = ?", [(i,) for i in ids])
        conn.commit()

        print(f"\n✅ Removidos {len(to_delete)} registo(s).")

    # ---- Reformatação de título/localização ----
    if not to_reformat:
        print("\nNenhum registo a reformatar (títulos e localizações já estão bons).")
    else:
        print(f"\nA reformatar {len(to_reformat)} registo(s):\n")
        for job_id, old_title, new_title, old_location, new_location, _ in to_reformat:
            if old_title != new_title:
                print(f"  ✏️  [{job_id}] título: \"{old_title}\" -> \"{new_title}\"")
            if old_location != new_location:
                print(f"  📍  [{job_id}] localização: \"{old_location}\" -> \"{new_location}\"")

        cursor.executemany(
            """
            UPDATE jobs
            SET title = ?, location = ?, hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
                (new_title, new_location, new_hash, job_id)
                for job_id, _, new_title, _, new_location, new_hash in to_reformat
            ]
        )
        conn.commit()

        print(f"\n✅ Reformatados {len(to_reformat)} registo(s).")

    conn.close()

    print("\nReexportando jobs.json...")
    export_jobs_to_json()


if __name__ == "__main__":
    cleanup_database()
