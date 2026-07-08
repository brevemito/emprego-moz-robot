# Robô de recolha de empregos - Moçambique

import re
import sys
import requests
from requests.exceptions import ConnectionError, Timeout

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

    # ========================
    # TAREFA 1: Rejeitar artefactos de template não renderizado
    # ========================
    # Vue.js, Angular, e outras frameworks deixam {{ }}, v-, ng- quando não renderizam
    if "{{" in title or "}}" in title:
        return False
    if title.startswith("v-") or " v-" in title:
        return False
    if "ng-" in title:
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

    # ========================
    # TAREFA 5: Rastreamento de falhas por categoria
    # ========================
    failed_sources = {
        "no_parser": [],
        "network_error": [],
        "zero_results": []
    }

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
                
                if len(parsed_jobs) == 0:
                    print(f"  ⚠️ Nenhuma vaga extraída de {source['name']}")
                    failed_sources["zero_results"].append(source['name'])
                else:
                    print(f"  ✅ {len(parsed_jobs)} vagas recolhidas de {source['name']}")
            else:
                print(f"  ⚠️ Sem parser definido para {source['name']}")
                failed_sources["no_parser"].append(source['name'])

        except (ConnectionError, Timeout) as e:
            print(f"  ❌ Erro de rede em {source['name']}: {type(e).__name__}")
            failed_sources["network_error"].append(source['name'])
        except Exception as e:
            print(f"  ❌ Erro inesperado em {source['name']}: {e}")

    # ========================
    # Relatório de falhas (Tarefa 5)
    # ========================
    if any(failed_sources.values()):
        print("\n" + "=" * 60)
        print("RESUMO DE FALHAS")
        print("=" * 60)
        
        if failed_sources["no_parser"]:
            print(f"\n⚠️ Sem parser definido ({len(failed_sources['no_parser'])}):")
            for source_name in failed_sources["no_parser"]:
                print(f"   - {source_name}")
        
        if failed_sources["network_error"]:
            print(f"\n❌ Erro de rede ({len(failed_sources['network_error'])}):")
            for source_name in failed_sources["network_error"]:
                print(f"   - {source_name}")
        
        if failed_sources["zero_results"]:
            print(f"\n⚠️ Sem vagas extraídas ({len(failed_sources['zero_results'])}):")
            for source_name in failed_sources["zero_results"]:
                print(f"   - {source_name}")
        
        print("=" * 60)

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

    print(f"\n✅ Total de vagas recolhidas (bruto): {len(jobs)}")

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
