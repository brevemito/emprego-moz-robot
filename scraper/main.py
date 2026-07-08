# Robô de recolha de empregos - Moçambique

import re
import sys
import requests

from parsers import PARSERS
from sources import SOURCES
from scoring import score_job
from database import initialize_database, insert_job
from export_json import export_jobs_to_json


# =========================
# NORMALIZAÇÃO
# =========================
def normalize_job(job):
    title = job.get("title", "")

    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"[|•–—]", "-", title)

    job["title"] = title

    if not job.get("company"):
        job["company"] = "Desconhecida"

    return job


# =========================
# FILTRO DE QUALIDADE
# =========================
def is_real_job(job):
    title = (job.get("title") or "").lower()

    if len(title) < 12:
        return False

    bad_patterns = [
        "cookie",
        "política",
        "privacidade",
        "faq",
        "perguntas frequentes",
        "sobre nós",
        "contacto",
        "administração e secretariado",
        "agricultura e pescas",
        "aquisições e procurement",
        "auditoria",
        "comercial e vendas",
        "design e multimédia",
        "hotelaria e turismo",
        "informática e programação"
    ]

    return not any(pattern in title for pattern in bad_patterns)


# =========================
# SCRAPING CORE
# =========================
def fetch_jobs():
    jobs = []

    for source in SOURCES:

        print(f"\nA recolher de: {source['name']}")

        try:

            response = requests.get(
                source["url"],
                timeout=15,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/138.0 Safari/537.36"
                    )
                }
            )

            response.raise_for_status()

            parser = PARSERS.get(source["name"])

            if parser:
                parsed_jobs = parser(response.text, source["url"])
                jobs.extend(parsed_jobs)
                print(f"  → {len(parsed_jobs)} vagas recolhidas de {source['name']}")
            else:
                print(f"  ⚠️ Sem parser definido para {source['name']}")

        except Exception as e:
            print(f"  ❌ Erro em {source['name']}: {e}")

    return jobs


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
if __name__ == "__main__":

    # Inicializar a base de dados
    initialize_database()

    # Recolher vagas
    jobs = fetch_jobs()

    # ========================
    # VERIFICAÇÃO CRÍTICA: falha se nenhuma vaga foi recolhida
    # ========================
    if len(jobs) == 0:
        print("\n" + "=" * 50)
        print("❌ ERRO CRÍTICO: Nenhuma vaga foi recolhida!")
        print("=" * 50)
        print("\nVerificar:")
        print("  - Conectividade de rede")
        print("  - Status das fontes (bloqueios, mudanças de URL)")
        print("  - Parsers em scraper/parsers/")
        sys.exit(1)

    print(f"\n✅ Total de vagas recolhidas: {len(jobs)}")

    cleaned_jobs = []

    # Normalizar, filtrar e classificar
    for job in jobs:

        job = normalize_job(job)

        if not is_real_job(job):
            continue

        job["score"] = score_job(job)

        cleaned_jobs.append(job)

    # Ordenar por score
    jobs = sorted(
        cleaned_jobs,
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n========================")
    print(f"TOTAL LIMPO: {len(jobs)}")
    print("========================\n")

    # Guardar todas as vagas
    inserted = 0
    duplicated = 0

    for job in jobs:

        if insert_job(job):
            inserted += 1
            print("🟢 Inserido:", job["title"])
        else:
            duplicated += 1
            print("🟡 Duplicado:", job["title"])

    print("\n========================")
    print(f"Novas vagas: {inserted}")
    print(f"Duplicadas: {duplicated}")
    print("========================")

    # Exportar para JSON
    print("\nExportando JSON...")
    export_jobs_to_json()

    print("✅ Concluído com sucesso.")
