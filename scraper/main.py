# Robô de recolha de empregos - Moçambique

import requests
import re

from parsers import PARSERS
from sources import SOURCES
from scoring import score_job
from database import initialize_database, insert_job


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
# FILTRO DE QUALIDADE (CRÍTICO)
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

    return not any(b in title for b in bad_patterns)


# =========================
# SCRAPING CORE
# =========================
def fetch_jobs():
    jobs = []

    for source in SOURCES:
        print(f"\nA recolher de: {source['name']}")

        try:
            r = requests.get(
                source["url"],
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            parser = PARSERS.get(source["name"])

            if parser:
                parsed_jobs = parser(r.text, source["url"])
                jobs.extend(parsed_jobs)
            else:
                print(f"Sem parser definido para {source['name']}")

        except Exception as e:
            print(f"Erro em {source['name']}: {e}")

    return jobs


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
if __name__ == "__main__":

    # 1. inicializar base de dados
    initialize_database()

    # 2. recolher vagas
    jobs = fetch_jobs()

    cleaned_jobs = []

    # 3. normalização + filtro + scoring
    for job in jobs:

        job = normalize_job(job)

        # 🔥 FILTRO CRÍTICO AQUI
        if not is_real_job(job):
            continue

        job["score"] = score_job(job)
        cleaned_jobs.append(job)

    jobs = cleaned_jobs

    # 4. ordenar por relevância
    jobs = sorted(jobs, key=lambda x: x["score"], reverse=True)

    print("\n========================")
    print("TOTAL LIMPO:", len(jobs))
    print("========================\n")

    # 5. inserir na base de dados
    for job in jobs[:20]:
        inserted = insert_job(job)

        if inserted:
            print("🟢 Inserido:", job["title"])
        else:
            print("🟡 Duplicado:", job["title"])
