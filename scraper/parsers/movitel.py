from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): movitel.co.mz não expõe um portal de
# vagas próprio com páginas de detalhe individuais - as vagas da Movitel
# são tipicamente anunciadas por email/candidatura directa ou em portais
# de terceiros (ex.: sovagas.co.mz, mmo.co.mz), não no próprio site
# institucional. Não existe, por isso, um padrão de URL de "detalhe de
# vaga" fiável nesta página para usar como evidência estrutural.
#
# A decisão de incluir ou não cada candidato passa a ser feita pelo
# JobValidator central, que exige evidência positiva de cargo/vaga.
# Esta fonte pode legitimamente devolver 0 resultados - o que é o
# comportamento correcto quando o site não lista vagas estruturadas.


def parse_movitel(html, source_url):
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
            "company": "Movitel",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "movitel"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
