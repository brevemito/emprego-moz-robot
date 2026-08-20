from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: no emprego.co.mz, cada vaga individual tem uma
# página de detalhe em /vaga/<slug>/ (ex.: https://www.emprego.co.mz/vaga/
# tecnico-de-manutencao-de-dados-e-insercao-de-informacao-de-cliente-m-f-2/).
# Qualquer outro link (menu, footer, páginas institucionais, FAQ, perfil de
# candidato, etc.) NÃO segue este padrão, por isso exigir "/vaga/" no URL é
# uma evidência estrutural muito mais forte do que qualquer lista de
# palavras a filtrar.
JOB_DETAIL_URL_HINT = "/vaga/"


def parse_emprego_co_mz(html, source_url):
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
            continue  # sem link não há como confirmar que é uma vaga

        # Evidência estrutural: só continuamos se o URL for mesmo uma
        # página de detalhe de vaga.
        if JOB_DETAIL_URL_HINT not in link:
            continue

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "emprego_co_mz"
        }

        # Validação estrutural centralizada (JobValidator): mesmo com o
        # URL a bater certo, confirmamos que o título tem evidência de
        # ser mesmo um cargo, para apanhar casos raros de links de
        # partilha/redes sociais que por acaso reutilizem o padrão de URL.
        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
