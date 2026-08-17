import requests
from urllib.parse import urljoin

# O portal de carreiras da Absa (https://absa.wd3.myworkdayjobs.com/ABSAcareersite)
# é uma aplicação Workday renderizada em JavaScript: o HTML devolvido por um
# simples GET não contém as vagas. As vagas só ficam disponíveis através da
# API interna do Workday (endpoint "CXS"), que exige um pedido POST com um
# corpo JSON. Por isso este parser ignora o "html" recebido de main.py
# (resultado do GET inicial) e faz o seu próprio pedido POST à API.

API_URL = "https://absa.wd3.myworkdayjobs.com/wday/cxs/absa/ABSAcareersite/jobs"
CAREERS_BASE = "https://absa.wd3.myworkdayjobs.com/ABSAcareersite"


def parse_absa(html, source_url):
    jobs = []
    seen_urls = set()  # Deduplicação dentro da resposta

    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "Mozambique"
    }

    try:
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
        data = response.json()
    except (requests.exceptions.RequestException, ValueError):
        return jobs

    postings = data.get("jobPostings", [])

    for posting in postings:

        title = (posting.get("title") or "").strip()

        if not title or len(title) < 10:
            continue

        location = (posting.get("locationsText") or "Moçambique").strip()

        # Filtro de segurança extra: a pesquisa já foi feita por "Mozambique",
        # mas confirmamos que o texto de localização também o refere, para
        # evitar vagas de outros países que só correspondam no título.
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
            "location": location,
            "description": title,
            "url": link,
            "source": "absa"
        })

    return jobs
