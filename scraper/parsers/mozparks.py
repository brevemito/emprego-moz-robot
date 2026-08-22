from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): mozparks.co.mz/careers/ não expõe uma
# lista estruturada de vagas com páginas de detalhe individuais. Não há,
# por isso, um padrão de URL de "detalhe de vaga" fiável para usar como
# evidência estrutural nesta página.
#
# A decisão de incluir ou não cada candidato passa a ser feita pelo
# JobValidator central. Esta fonte pode legitimamente devolver 0
# resultados sempre que não haja vagas estruturadas publicadas.


def parse_mozparks(html, source_url):
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
            "company": "MozParks",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "mozparks"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
