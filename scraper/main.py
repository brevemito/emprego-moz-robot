# Robô de recolha de empregos - Moçambique

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

# ========================
# TAREFA 6: Rejeitar anúncios de concursos públicos / procurement / RFP
# ========================
# Estes anúncios aparecem frequentemente em fontes como ReliefWeb, UNjobs ou
# páginas institucionais, mas não são vagas de emprego - são convites para
# empresas apresentarem propostas de fornecimento de bens/serviços.
# Usamos frases compostas (não palavras isoladas como "procurement" ou
# "tender", que também aparecem em títulos de cargos legítimos, ex.:
# "Procurement Officer", "Tender Manager") para não gerar falsos positivos.

# Padrões compostos (strings simples, comparação directa).
PROCUREMENT_PATTERNS = [
    "concurso público para fornecimento",
    "concurso público para aquisição",
    "anúncio de concurso",
    "aviso de concurso",
    "convite à apresentação de propostas",
    "convite a apresentação de propostas",
    "convite para apresentação de propostas",
    "request for proposal",
    "request for proposals",
    "request for quotation",
    "request for quotations",
    "invitation to bid",
    "invitation for bid",
    "invitation for bids",
    "tender notice",
    "tender document",
    "tender for the supply",
    "notice of tender",
    "expression of interest",
    "manifestação de interesse",
    "aquisição de bens e serviços",
    "aquisição de bens",
    "fornecimento de equipamentos",
    "fornecimento de bens",
    "fornecimento de material",
    "fornecimento de materiais",
    "solicitação de cotação",
    "pedido de cotação",
    "solicitação de propostas",
    "consultoria institucional",
    "caderno de encargos",
    "termos de referência para aquisição",
    "termos de referência para contratação de fornecedor"
]

# Padrões com regex: cobrem singular/plural ("concurso"/"concursos") e as
# várias formas de escrever o número do concurso ("nº", "n°", "no.", "n.o"),
# incluindo quando "concurso(s)" e o número aparecem separados por outras
# palavras (ex.: "Concurso Público nº13", "Concursos Nº 10").
PROCUREMENT_REGEX_PATTERNS = [
    r"concursos?\s*(público)?\s*n[ºo°.]*\s*\d",
    r"\brfp\b",
    r"\brfq\b",
    r"\(rfp\)",
    r"\(rfq\)",
]


def is_procurement_notice(text):
    if any(pattern in text for pattern in PROCUREMENT_PATTERNS):
        return True

    if any(re.search(pattern, text) for pattern in PROCUREMENT_REGEX_PATTERNS):
        return True

    return False


def is_real_job(job):
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()

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

    # Verificamos tanto o título como a descrição: alguns anúncios de
    # concursos têm um título curto/genérico, mas revelam-se pelo conteúdo
    # da descrição (ex.: "Convite à Apresentação de Propostas...").
    if is_procurement_notice(title) or is_procurement_notice(description):
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
            "rejected": 0,
            "inserted": 0,
            "duplicated": 0,
            "status": "ok"
        }

        print(f"\nA recolher de: {name}")

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
                    print(f"  ✅ {len(parsed_jobs)} vagas recolhidas de {name}")
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

    return jobs, source_stats


# =========================
# RELATÓRIO FINAL (por fonte)
# =========================
def print_source_report(source_stats):
    """
    Mostra uma tabela com o desempenho de cada fonte: quantas vagas brutas
    foram encontradas, quantas passaram o filtro de qualidade, quantas
    foram novas na base de dados e quantas já existiam (duplicadas).
    Isto facilita ver de imediato quais as fontes mais produtivas e quais
    precisam de atenção (parser desactualizado, bloqueio, etc.).
    """

    headers = ("Fonte", "Brutas", "Válidas", "Rejeit.", "Novas", "Duplic.", "Estado")
    col_widths = (20, 8, 9, 9, 7, 9, 14)

    def fmt_row(values):
        return "".join(f"{str(v):<{w}}" for v, w in zip(values, col_widths))

    print("\n" + "=" * sum(col_widths))
    print("RELATÓRIO POR FONTE")
    print("=" * sum(col_widths))
    print(fmt_row(headers))
    print("-" * sum(col_widths))

    status_labels = {
        "ok": "OK",
        "zero_results": "SEM VAGAS",
        "no_parser": "SEM PARSER",
        "network_error": "ERRO REDE",
        "error": "ERRO"
    }

    totals = {"raw": 0, "valid": 0, "rejected": 0, "inserted": 0, "duplicated": 0}

    # Ordena por número de vagas novas (as fontes mais produtivas primeiro)
    ordered = sorted(
        source_stats.items(),
        key=lambda kv: kv[1]["inserted"],
        reverse=True
    )

    for name, stats in ordered:
        status = status_labels.get(stats["status"], stats["status"])

        print(fmt_row((
            name,
            stats["raw"],
            stats["valid"],
            stats["rejected"],
            stats["inserted"],
            stats["duplicated"],
            status
        )))

        totals["raw"] += stats["raw"]
        totals["valid"] += stats["valid"]
        totals["rejected"] += stats["rejected"]
        totals["inserted"] += stats["inserted"]
        totals["duplicated"] += stats["duplicated"]

    print("-" * sum(col_widths))
    print(fmt_row((
        "TOTAL",
        totals["raw"],
        totals["valid"],
        totals["rejected"],
        totals["inserted"],
        totals["duplicated"],
        ""
    )))
    print("=" * sum(col_widths))


def print_top_jobs(jobs, limit=5):
    """
    Mostra rapidamente as vagas com melhor pontuação, para dar uma ideia
    imediata da qualidade do que foi recolhido nesta execução.
    """
    if not jobs:
        return

    print(f"\nTOP {min(limit, len(jobs))} VAGAS COM MELHOR PONTUAÇÃO")
    print("-" * 60)

    for job in jobs[:limit]:
        print(f"  ⭐ [{job['score']:>4}] {job['title']}")
        print(f"          {job.get('company', 'Desconhecida')} | {job.get('source', '')}")

    print("-" * 60)


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
if __name__ == "__main__":

    start_time = time.time()

    # Inicializar a base de dados
    initialize_database()

    # Recolher vagas
    jobs, source_stats = fetch_jobs()

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
        source_name = job.get("source", "desconhecida")

        if not is_real_job(job):
            source_stats.setdefault(source_name, {}).setdefault("rejected", 0)
            source_stats[source_name]["rejected"] += 1
            continue

        job["score"] = score_job(job)
        cleaned_jobs.append(job)

        source_stats.setdefault(source_name, {}).setdefault("valid", 0)
        source_stats[source_name]["valid"] += 1

    # Ordenar por score
    jobs = sorted(
        cleaned_jobs,
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n========================")
    print(f"TOTAL LIMPO: {len(jobs)}")
    print("========================")

    # Guardar todas as vagas
    inserted = 0
    duplicated = 0

    for job in jobs:

        source_name = job.get("source", "desconhecida")

        if insert_job(job):
            inserted += 1
            source_stats[source_name]["inserted"] += 1
            print("🟢 Inserido:", job["title"])
        else:
            duplicated += 1
            source_stats[source_name]["duplicated"] += 1
            print("🟡 Duplicado:", job["title"])

    # ========================
    # RELATÓRIO FINAL
    # ========================
    print_source_report(source_stats)
    print_top_jobs(jobs)

    elapsed = time.time() - start_time

    print("\n" + "=" * 40)
    print("RESUMO GERAL DA EXECUÇÃO")
    print("=" * 40)
    print(f"  Vagas brutas recolhidas : {sum(s['raw'] for s in source_stats.values())}")
    print(f"  Vagas válidas (após filtro): {len(jobs)}")
    print(f"  Novas vagas guardadas   : {inserted}")
    print(f"  Já existiam (duplicadas): {duplicated}")
    print(f"  Tempo de execução       : {elapsed:.1f}s")
    print("=" * 40)

    # Exportar para JSON
    print("\nExportando JSON...")
    export_jobs_to_json()

    print("✅ Concluído com sucesso.")
