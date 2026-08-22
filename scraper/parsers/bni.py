from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): bni.co.mz/en/about-bni/careers/ é uma
# página de candidatura espontânea ("Send us your CV telling us about
# your potential to be part of our candidate database") - não expõe uma
# lista estruturada de vagas com páginas de detalhe individuais. Não há,
# por isso, um padrão de URL de "detalhe de vaga" fiável para usar como
# evidência estrutural nesta página.
#
# A decisão de incluir ou não cada candidato passa a ser feita pelo
# JobValidator central, que exige evidência positiva de cargo/vaga.
# Esta fonte pode legitimamente devolver 0 resultados - o que é o
# comportamento correcto quando não há vagas estruturadas publicadas.


def parse_bni(html, source_url):
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
            "company": "BNI - Banco Nacional de Investimento",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "bni"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
