# Script de manutenção - Limpeza retroactiva
#
# O filtro de qualidade em main.py (job_validator.classify) só se aplica
# a vagas recolhidas a partir do momento em que o filtro foi adicionado
# ou melhorado. Vagas inseridas ANTES disso continuam na base de dados e
# continuam a aparecer no jobs.json exportado.
#
# Este script percorre a base de dados existente, aplica o JobValidator
# actual a cada registo já guardado e remove os que já não são
# considerados vagas de emprego válidas. No final, volta a exportar o
# jobs.json já limpo.
#
# Uso:
#   cd scraper
#   python3 cleanup_database.py

from database import get_connection
from export_json import export_jobs_to_json
from main import is_real_job


def cleanup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, company, location, description, url, source FROM jobs")
    rows = cursor.fetchall()

    to_delete = []

    for row in rows:
        job = dict(row)
        if not is_real_job(job):
            to_delete.append((job["id"], job["title"]))

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

    conn.close()

    print("\nReexportando jobs.json...")
    export_jobs_to_json()


if __name__ == "__main__":
    cleanup_database()
