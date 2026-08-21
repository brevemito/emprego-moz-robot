# Robô de recolha de empregos - Moçambique

import json
import re
import sys
import time
import requests
from requests.exceptions import ConnectionError, Timeout

from parsers import PARSERS
from sources import SOURCES
from scoring import score_job
from database import initialize_database, insert_job
from export_json import export_jobs_to_json
import job_validator


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
# VALIDAÇÃO ESTRUTURAL (JobValidator)
# =========================
# A validação de "isto é mesmo uma vaga?" (JOB_VALIDITY_SCORE) foi
# centralizada em scraper/job_validator.py, para ser partilhada por todos
# os parsers e por este pipeline central, evitando termos várias listas
# de blacklist divergentes espalhadas pelo código. Ver esse módulo para o
# detalhe da lógica estrutural (evidência positiva de cargo, padrões de
# URL de detalhe de vaga, categorias de rejeição, etc.).
#
# JOB_RELEVANCE_SCORE (quão boa/relevante é a vaga para Moçambique e para
# os utilizadores do Brevemito) continua a ser calculado à parte, em
# scoring.py, e só é aplicado a itens que já passaram nesta validação.
def is_real_job(job):
    """
    Mantido por compatibilidade com o resto do código (nome antigo),
    mas agora é apenas uma fina camada sobre job_validator.classify().
    Devolve True/False; para o motivo de rejeição e o validity_score,
    usar job_validator.classify() directamente (é o que o pipeline
    principal abaixo faz).
    """
    result = job_validator.classify(
        job.get("title"),
        job.get("description"),
        job.get("url")
    )
    return result["is_valid"]


# =========================
# SCRAPING CORE
# =========================
def fetch_jobs():
    jobs = []

    # Estatísticas por fonte (para o relatório final)
    source_stats = {}

    failed_sources = {
        "no_parser": [],
        "network_error": [],
        "zero_results": []
    }

    for source in SOURCES:

        name = source["name"]
        source_stats[name] = {
            "raw": 0,
            "valid": 0,
            "inserted": 0,
            "duplicated": 0,
            "status": "ok",
            # Contagem de rejeições por categoria estrutural (Requisito 15)
            "rejected_navigation": 0,
            "rejected_search_filter": 0,
            "rejected_location_filter": 0,
            "rejected_institutional_page": 0,
            "rejected_procurement": 0,
            "rejected_category": 0,
            "rejected_organization": 0,
            "rejected_insufficient_evidence": 0,
        }

        print(f"\nA recolher de: {name}")

        # Duas tentativas: a primeira falha por lentidão de rede é comum
        # em CI (GitHub Actions), sobretudo para sites moçambicanos mais
        # lentos a responder a partir de datacenters fora de África.
        # Isto NÃO resolve bloqueios de IP feitos de propósito pelo site
        # (nesse caso, ambas as tentativas falham da mesma forma) - só
        # ajuda em casos de lentidão/instabilidade pontual.
        response = None
        last_error = None

        for attempt in range(2):
            try:
                response = requests.get(
                    source["url"],
                    timeout=25,
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
                last_error = None
                break
            except (ConnectionError, Timeout) as e:
                last_error = e
                if attempt == 0:
                    print(f"  ⏳ 1ª tentativa falhou ({type(e).__name__}), a tentar de novo...")
                    time.sleep(3)
                continue

        try:
            if last_error is not None:
                raise last_error

            parser = PARSERS.get(name)

            if parser:
                parsed_jobs = parser(response.text, source["url"])

                # Anotamos a fonte em cada vaga já aqui, para o relatório
                # final conseguir agrupar correctamente mais abaixo.
                for job in parsed_jobs:
                    job.setdefault("source", name)

                jobs.extend(parsed_jobs)
                source_stats[name]["raw"] = len(parsed_jobs)

                if len(parsed_jobs) == 0:
                    print(f"  ⚠️ Nenhuma vaga extraída de {name}")
                    source_stats[name]["status"] = "zero_results"
                    failed_sources["zero_results"].append(name)
                else:
                    print(f"  ✅ {len(parsed_jobs)} candidatos extraídos de {name}")
            else:
                print(f"  ⚠️ Sem parser definido para {name}")
                source_stats[name]["status"] = "no_parser"
                failed_sources["no_parser"].append(name)

        except (ConnectionError, Timeout) as e:
            print(f"  ❌ Erro de rede em {name}: {type(e).__name__}")
            source_stats[name]["status"] = "network_error"
            failed_sources["network_error"].append(name)
        except Exception as e:
            print(f"  ❌ Erro inesperado em {name}: {e}")
            source_stats[name]["status"] = "error"

    # ========================
    # Relatório de falhas
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
            print(f"\n⚠️ Sem candidatos extraídos ({len(failed_sources['zero_results'])}):")
            for source_name in failed_sources["zero_results"]:
                print(f"   - {source_name}")

        print("=" * 60)

    return jobs, source_stats


# =========================
# RELATÓRIO FINAL (por fonte)
# =========================
REASON_TO_STAT_KEY = {
    "navigation": "rejected_navigation",
    "search_filter": "rejected_search_filter",
    "location_filter": "rejected_location_filter",
    "institutional_page": "rejected_institutional_page",
    "procurement": "rejected_procurement",
    "category": "rejected_category",
    "organization": "rejected_organization",
    "insufficient_job_evidence": "rejected_insufficient_evidence",
}

REASON_LABELS = {
    "navigation": "Navegação/template",
    "search_filter": "Filtro de pesquisa",
    "location_filter": "Filtro de localização",
    "institutional_page": "Página institucional",
    "procurement": "Concurso/RFP",
    "category": "Categoria genérica",
    "organization": "Organização sem cargo",
    "insufficient_job_evidence": "Evidência insuficiente",
}


def print_source_report(source_stats):
    """
    Mostra uma tabela com o desempenho de cada fonte: quantos candidatos
    brutos foram encontrados, quantos são vagas válidas, quantos foram
    rejeitados por categoria estrutural (navegação, filtros, páginas
    institucionais, concursos, etc.), quantos são novos na base de dados
    e quantos já existiam (duplicados). Isto facilita ver de imediato
    quais fontes estão saudáveis e quais precisam de atenção.
    """

    headers = ("Fonte", "Brutas", "Válidas", "Nav.", "Filtro", "Instit.", "Concurso", "Outros", "Novas", "Duplic.", "Estado")
    col_widths = (16, 7, 8, 6, 7, 8, 9, 7, 6, 8, 12)

    def fmt_row(values):
        return "".join(f"{str(v):<{w}}" for v, w in zip(values, col_widths))

    total_width = sum(col_widths)

    print("\n" + "=" * total_width)
    print("RELATÓRIO POR FONTE")
    print("=" * total_width)
    print(fmt_row(headers))
    print("-" * total_width)

    status_labels = {
        "ok": "OK",
        "zero_results": "SEM VAGAS",
        "no_parser": "SEM PARSER",
        "network_error": "ERRO REDE",
        "error": "ERRO"
    }

    totals = {
        "raw": 0, "valid": 0, "inserted": 0, "duplicated": 0,
        "rejected_navigation": 0, "rejected_search_filter": 0,
        "rejected_location_filter": 0, "rejected_institutional_page": 0,
        "rejected_procurement": 0, "rejected_category": 0,
        "rejected_organization": 0, "rejected_insufficient_evidence": 0,
    }

    # Ordena por número de vagas novas (as fontes mais produtivas primeiro)
    ordered = sorted(
        source_stats.items(),
        key=lambda kv: kv[1].get("inserted", 0),
        reverse=True
    )

    for name, stats in ordered:
        status = status_labels.get(stats.get("status"), stats.get("status", ""))

        # "Outros" agrupa categoria + organização + filtro de localização,
        # para caber a tabela sem ficar demasiado larga; concurso e
        # institucional (as categorias mais frequentes/graves reportadas)
        # ficam em colunas próprias.
        outros = (
            stats.get("rejected_category", 0)
            + stats.get("rejected_organization", 0)
            + stats.get("rejected_location_filter", 0)
            + stats.get("rejected_insufficient_evidence", 0)
        )

        print(fmt_row((
            name,
            stats.get("raw", 0),
            stats.get("valid", 0),
            stats.get("rejected_navigation", 0),
            stats.get("rejected_search_filter", 0),
            stats.get("rejected_institutional_page", 0),
            stats.get("rejected_procurement", 0),
            outros,
            stats.get("inserted", 0),
            stats.get("duplicated", 0),
            status
        )))

        for key in totals:
            totals[key] += stats.get(key, 0)

    total_outros = (
        totals["rejected_category"] + totals["rejected_organization"]
        + totals["rejected_location_filter"] + totals["rejected_insufficient_evidence"]
    )

    print("-" * total_width)
    print(fmt_row((
        "TOTAL",
        totals["raw"],
        totals["valid"],
        totals["rejected_navigation"],
        totals["rejected_search_filter"],
        totals["rejected_institutional_page"],
        totals["rejected_procurement"],
        total_outros,
        totals["inserted"],
        totals["duplicated"],
        ""
    )))
    print("=" * total_width)
    print(
        "Legenda: Nav.=artefactos técnicos/menus | Filtro=chips de pesquisa | "
        "Instit.=páginas institucionais | Concurso=procurement/RFP | "
        "Outros=categoria+organização+localização+evidência insuficiente"
    )


def print_top_jobs(jobs, limit=5):
    """
    Mostra rapidamente as vagas com melhor pontuação de relevância
    (JOB_RELEVANCE_SCORE), para dar uma ideia imediata da qualidade do
    que foi recolhido nesta execução.
    """
    if not jobs:
        return

    print(f"\nTOP {min(limit, len(jobs))} VAGAS COM MELHOR PONTUAÇÃO (relevância)")
    print("-" * 70)

    for job in jobs[:limit]:
        validity = job.get("validity_score", "-")
        print(f"  ⭐ relevância={job['score']:>4}  validade={validity:>4}  {job['title']}")
        print(f"          {job.get('company', 'Desconhecida')} | {job.get('source', '')}")

    print("-" * 70)


def print_rejected_examples(rejected_items, limit=8):
    """
    Mostra alguns exemplos de itens rejeitados e o respectivo motivo,
    para permitir uma auditoria rápida da qualidade do filtro sem ter de
    abrir o ficheiro de log completo.
    """
    if not rejected_items:
        return

    print(f"\nEXEMPLOS DE ITENS REJEITADOS (até {limit})")
    print("-" * 70)

    for item in rejected_items[:limit]:
        label = REASON_LABELS.get(item["reason"], item["reason"])
        print(f"  🚫 [{item['source']:<16}] ({label}) {item['title']}")

    print("-" * 70)


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
if __name__ == "__main__":

    start_time = time.time()

    # Inicializar a base de dados
    initialize_database()

    # Recolher candidatos a vaga (ainda não validados)
    jobs, source_stats = fetch_jobs()

    # ========================
    # VERIFICAÇÃO CRÍTICA: falha se nenhum candidato foi recolhido
    # ========================
    if len(jobs) == 0:
        print("\n" + "=" * 50)
        print("❌ ERRO CRÍTICO: Nenhum candidato foi recolhido!")
        print("=" * 50)
        print("\nVerificar:")
        print("  - Conectividade de rede")
        print("  - Status das fontes (bloqueios, mudanças de URL)")
        print("  - Parsers em scraper/parsers/")
        sys.exit(1)

    print(f"\n✅ Total de candidatos recolhidos (bruto): {len(jobs)}")

    cleaned_jobs = []
    rejected_items = []  # Requisito 14: guardar motivo de rejeição

    # Normalizar, validar estruturalmente (JobValidator) e classificar
    # por relevância (scoring.py) apenas quem passou na validação.
    for job in jobs:

        job = normalize_job(job)
        source_name = job.get("source", "desconhecida")
        source_stats.setdefault(source_name, {})

        result = job_validator.classify(job.get("title"), job.get("description"), job.get("url"))

        if not result["is_valid"]:
            reason = result["reason"] or "insufficient_job_evidence"
            stat_key = REASON_TO_STAT_KEY.get(reason, "rejected_insufficient_evidence")
            source_stats[source_name][stat_key] = source_stats[source_name].get(stat_key, 0) + 1

            rejected_items.append({
                "title": job["title"],
                "source": source_name,
                "reason": reason,
                "url": job.get("url", "")
            })
            continue

        # JOB_VALIDITY_SCORE (estrutural) fica guardado para transparência
        job["validity_score"] = result["validity_score"]

        # JOB_RELEVANCE_SCORE (scoring.py) só é calculado depois de
        # confirmada a validade estrutural do item.
        job["score"] = score_job(job)
        cleaned_jobs.append(job)

        source_stats[source_name]["valid"] = source_stats[source_name].get("valid", 0) + 1

    # Ordenar por relevância
    jobs = sorted(
        cleaned_jobs,
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n========================")
    print(f"TOTAL DE VAGAS VÁLIDAS: {len(jobs)}")
    print(f"TOTAL REJEITADO: {len(rejected_items)}")
    print("========================")

    # Guardar todas as vagas válidas
    inserted = 0
    duplicated = 0

    for job in jobs:

        source_name = job.get("source", "desconhecida")

        if insert_job(job):
            inserted += 1
            source_stats[source_name]["inserted"] = source_stats[source_name].get("inserted", 0) + 1
            print("🟢 Inserido:", job["title"])
        else:
            duplicated += 1
            source_stats[source_name]["duplicated"] = source_stats[source_name].get("duplicated", 0) + 1
            print("🟡 Duplicado:", job["title"])

    # ========================
    # RELATÓRIO FINAL
    # ========================
    print_source_report(source_stats)
    print_top_jobs(jobs)
    print_rejected_examples(rejected_items)

    elapsed = time.time() - start_time

    print("\n" + "=" * 40)
    print("RESUMO GERAL DA EXECUÇÃO")
    print("=" * 40)
    print(f"  Candidatos brutos recolhidos : {sum(s.get('raw', 0) for s in source_stats.values())}")
    print(f"  Vagas válidas (após filtro)  : {len(jobs)}")
    print(f"  Rejeitados no total          : {len(rejected_items)}")
    print(f"  Novas vagas guardadas        : {inserted}")
    print(f"  Já existiam (duplicadas)     : {duplicated}")
    print(f"  Tempo de execução            : {elapsed:.1f}s")
    print("=" * 40)

    # Requisito 14: guardar o motivo de rejeição em ficheiro, para
    # auditoria posterior sem depender apenas do log da consola.
    try:
        with open("data/rejected_items.json", "w", encoding="utf-8") as f:
            json.dump(rejected_items, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Motivos de rejeição guardados em data/rejected_items.json ({len(rejected_items)} itens)")
    except OSError as e:
        print(f"\n⚠️ Não foi possível guardar data/rejected_items.json: {e}")

    # Exportar para JSON
    print("\nExportando JSON...")
    export_jobs_to_json()

    print("✅ Concluído com sucesso.")
