import requests
from urllib.parse import urljoin

# O portal de carreiras da Absa (https://absa.wd3.myworkdayjobs.com/ABSAcareersite)
# é uma aplicação Workday renderizada em JavaScript: o HTML devolvido por um
# simples GET não contém as vagas. As vagas só ficam disponíveis através da
# API interna do Workday (endpoint "CXS"), que exige um pedido POST com um
# corpo JSON. Por isso este parser ignora o "html" recebido de main.py
# (resultado do GET inicial) e faz o seu próprio pedido POST à API.
#
# MELHORIA: a versão anterior usava "searchText": "Mozambique", que depende
# do algoritmo de relevância textual do Workday e pode não devolver vagas
# cujo título não mencione "Mozambique" explicitamente, mesmo que a
# localização seja Moçambique. Passámos a pesquisar sem texto (todas as
# vagas abertas) e a paginar por várias páginas, filtrando sempre pelo
# campo estruturado "locationsText" - mais lento, mas muito mais completo.

API_URL = "https://absa.wd3.myworkdayjobs.com/wday/cxs/absa/ABSAcareersite/jobs"
CAREERS_BASE = "https://absa.wd3.myworkdayjobs.com/ABSAcareersite"

PAGE_SIZE = 20
MAX_PAGES = 10  # cobre até 200 vagas abertas, suficiente para o volume da Absa


def _fetch_page(offset):
    payload = {
        "appliedFacets": {},
        "limit": PAGE_SIZE,
        "offset": offset,
        "searchText": ""
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=15,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        }
    )
    response.raise_for_status()
    return response.json()


def parse_absa(html, source_url):
    jobs = []
    seen_urls = set()

    total_available = None

    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE

        try:
            data = _fetch_page(offset)
        except (requests.exceptions.RequestException, ValueError):
            break

        if total_available is None:
            total_available = data.get("total", 0)

        postings = data.get("jobPostings", [])

        if not postings:
            break

        for posting in postings:

            title = (posting.get("title") or "").strip()

            if not title:
                continue

            location = (posting.get("locationsText") or "").strip()

            if "mozambique" not in location.lower() and "moçambique" not in location.lower():
                continue

            external_path = posting.get("externalPath") or ""
            link = urljoin(CAREERS_BASE + "/", external_path.lstrip("/")) if external_path else source_url

            normalized_url = link.split("?")[0]
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            jobs.append({
                "title": title,
                "company": "Absa",
                "location": location or "Moçambique",
                "description": title,
                "url": link,
                "source": "absa"
            })

        # Já percorremos todas as vagas disponíveis - não vale a pena
        # continuar a paginar.
        if total_available is not None and offset + PAGE_SIZE >= total_available:
            break

    return jobs
