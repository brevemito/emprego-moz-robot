from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): precrutamento.enh.co.mz/vagas é um
# portal de recrutamento próprio da ENH, mas frequentemente não tem
# nenhuma vaga aberta ("De momento, não existem vagas."). Não foi
# possível confirmar um padrão de URL estável de "detalhe de vaga" nesta
# página (varia consoante o sistema de recrutamento em uso).
#
# A decisão de incluir ou não cada candidato passa a ser feita pelo
# JobValidator central, que exige evidência positiva de cargo/vaga.
# Esta fonte devolverá 0 resultados sempre que não houver vagas abertas
# publicadas - o que é o comportamento correcto, não um erro do parser.


def parse_enh(html, source_url):
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
            "company": "ENH",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "enh"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
