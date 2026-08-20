from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: no contact.co.mz, cada oferta de emprego individual
# tem uma página de detalhe em /recrutamento/oferta-de-emprego/<hash>/<slug>
# (ex.: https://www.contact.co.mz/pt/recrutamento/oferta-de-emprego/
# BAAC58F553/motorista-m-f-1-vaga). Páginas institucionais como
# "/pt/vaga-nao-se-paga" (aviso anti-fraude) NÃO seguem este padrão, por
# isso exigir "oferta-de-emprego" no URL elimina-as estruturalmente, sem
# depender de listas de palavras.
JOB_DETAIL_URL_HINT = "oferta-de-emprego"


def parse_contact_mz(html, source_url):
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
            "company": "Contact",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "contact_mz"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
