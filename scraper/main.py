# Robô de recolha de empregos - Moçambique

import requests

from parsers import PARSERS
from sources import SOURCES
from scoring import score_job
from database import initialize_database, insert_job


import re


# =========================
# NORMALIZAÇÃO (CAMADA FINAL)
# =========================
def normalize_job(job):
    title = job.get("title", "")

    # limpar espaços duplicados
    title = re.sub(r"\s+", " ", title).strip()

    # normalizar separadores
    title = re.sub(r"[|•–—]", "-", title)

    job["title"] = title

    # garantir company padrão
    if not job.get("company"):
        job["company"] = "Desconhecida"

    return job


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

    # 3. normalização + scoring
    for job in jobs:
        job = normalize_job(job)
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
