from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): bci.co.mz/recrutamento/ é sobretudo uma
# página de "candidatura espontânea" (banco de talentos), sem uma lista
# estruturada de vagas com páginas de detalhe individuais. Não existe,
# por isso, um padrão de URL de "detalhe de vaga" fiável para usar como
# evidência estrutural nesta página.
#
# Tal como em millennium_bim.py, a decisão de incluir ou não cada
# candidato passa a ser feita pelo JobValidator central, que exige
# evidência positiva de cargo/vaga. Esta fonte pode legitimamente
# devolver 0 resultados quando não há vagas com título reconhecível
# publicadas nesta página - o que é o comportamento correcto.


def parse_bci(html, source_url):
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
            "company": "BCI",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "bci"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
