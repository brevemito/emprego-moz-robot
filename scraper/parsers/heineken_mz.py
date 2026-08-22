from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: o portal de carreiras da Heineken (SuccessFactors
# Career Site Builder) tem uma página de listagem filtrada por empresa
# operacional ("operatings_company") que É renderizada no servidor.
# Cada vaga individual tem uma página de detalhe cujo URL contém "/job/"
# (ex.: .../Portugues/job/Maputo-Sales-Representative/12345/).
JOB_DETAIL_URL_HINT = "/job/"

# Links de navegação que também contêm "/job/" mas não são vagas
# individuais (ex.: a própria página de pesquisa/listagem).
EXCLUDED_URL_FRAGMENTS = ["job-listing", "job-search", "job-alert"]


def parse_heineken_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):

        link = a["href"]
        link_lower = link.lower()

        if JOB_DETAIL_URL_HINT not in link_lower:
            continue

        if any(fragment in link_lower for fragment in EXCLUDED_URL_FRAGMENTS):
            continue

        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        link = urljoin(source_url, link)

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "Heineken Moçambique (Cervejas de Moçambique)",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "heineken_mz"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
