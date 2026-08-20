from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: no unjobs.org, cada vaga individual tem uma página
# de detalhe em /vacancies/<id> (ex.: https://unjobs.org/vacancies/
# 1771597297607). Os chips de filtro do menu lateral ("Duty Stations",
# "Organizations", "Closing Soon", etc.) e os links para páginas de
# organizações NÃO seguem este padrão, por isso exigir "/vacancies/" no
# URL elimina-os estruturalmente.
JOB_DETAIL_URL_HINT = "/vacancies/"


def parse_unjobs(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a"):

        title = a.get_text(separator=" ", strip=True)

        if not title or len(title) < 10:
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            continue

        if JOB_DETAIL_URL_HINT not in link:
            continue

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "UN Jobs",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "unjobs"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
