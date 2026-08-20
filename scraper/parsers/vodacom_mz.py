from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# INVESTIGAÇÃO (fonte a devolver 0 resultados):
#
# O portal de carreiras da Vodafone/Vodacom (careers.vodafone.com e
# jobs.vodafone.com) corre sobre a plataforma Eightfold ("PCSX"), uma
# Single Page Application em React. Confirmámos directamente que um GET
# simples a estas páginas devolve apenas uma "shell" HTML com
# configuração de UI em JSON (temas, textos, formulários) - NENHUMA
# vaga vem no HTML inicial; as vagas só chegam depois via chamadas
# JavaScript à API interna da Eightfold.
#
# A Eightfold não disponibiliza uma API pública gratuita para consulta
# de vagas (requer token OAuth pago, ou um browser headless tipo
# Playwright/Selenium, fora do âmbito deste scraper baseado em
# requests + BeautifulSoup). Para não arriscar inventar um endpoint não
# documentado nem confirmado, mantemos aqui a extracção estrutural
# best-effort (sem blacklists manuais, delegando no JobValidator), mas
# é esperado que esta fonte continue a devolver 0 resultados até se
# adicionar suporte a renderização JavaScript ao projecto.


def parse_vodacom_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):

        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        link = urljoin(source_url, a["href"])

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "Vodacom Moçambique",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "vodacom_mz"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
