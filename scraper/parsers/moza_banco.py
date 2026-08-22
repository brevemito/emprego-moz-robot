from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): a página institucional genérica de
# careers do Moza Banco tem uma subpágina dedicada a vagas activas
# ("/vacancies"), que é a que configurámos em sources.py. Ainda assim,
# não foi possível confirmar um padrão de URL de "detalhe de vaga"
# estável (o banco pode publicar vagas como PDF para download, ou como
# texto directamente na própria página, consoante a vaga).
#
# A decisão de incluir ou não cada candidato passa a ser feita pelo
# JobValidator central, que exige evidência positiva de cargo/vaga.


def parse_moza_banco(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a"):

        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "Moza Banco",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "moza_banco"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
