from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA (investigação): "CIM" é a Cimentos de Moçambique. O domínio
# originalmente configurado (cim.co.mz) não corresponde à empresa real
# e não expõe vagas próprias. A CIM publica as suas vagas através do
# emprego.co.mz (página de empregador dedicada), por isso reaproveitamos
# aqui o mesmo padrão de URL de detalhe de vaga confirmado em
# parsers/emprego_co_mz.py ("/vaga/").
JOB_DETAIL_URL_HINT = "/vaga/"


def parse_cim(html, source_url):
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
            continue

        if JOB_DETAIL_URL_HINT not in link:
            continue

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "CIM - Cimentos de Moçambique",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "cim"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
