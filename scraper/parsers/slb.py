import requests
from bs4 import BeautifulSoup

import job_validator as jv

# =========================================================================
# SLB (antiga Schlumberger) - careers.slb.com
# =========================================================================
#
# A lista de vagas (https://careers.slb.com/job-listing) é desenhada no
# navegador pelo motor de pesquisa Coveo. A própria página traz, em
# campos escondidos, a chave PÚBLICA de pesquisa que o navegador usa
# (#organizationId, #accessToken, #searchHub, #searchsource). O parser lê
# esses valores da página recebida de main.py - por isso continua a
# funcionar se a SLB trocar a chave - e faz a mesma pesquisa que o
# navegador, filtrada pelo campo estruturado "country" = Mozambique.
#
# Em Moçambique a SLB publica sobretudo vagas de entrada ("Early
# Careers": técnicos de manutenção, field specialists, estágios), muito
# relevantes para recém-formados e técnicos médios.
# =========================================================================

COMPANY = "SLB"
MAX_RESULTS = 100


def _hidden(soup, element_id):
    el = soup.find(id=element_id)
    return (el.get("value") or "").strip() if el else ""


def parse_slb(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    org = _hidden(soup, "organizationId")
    token = _hidden(soup, "accessToken")
    hub = _hidden(soup, "searchHub")
    src = _hidden(soup, "searchsource")
    if not org or not token:
        return []

    body = {
        "q": "",
        "aq": '@country=="Mozambique"',
        "searchHub": hub,
        "numberOfResults": MAX_RESULTS,
        "sortCriteria": "date descending",
    }
    if src:
        body["cq"] = f'@source=="{src}"'

    try:
        r = requests.post(
            f"https://{org}.org.coveo.com/rest/search/v2",
            json=body,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json().get("results") or []
    except (requests.exceptions.RequestException, ValueError):
        return []

    jobs = []
    seen = set()
    for item in results:
        raw = item.get("raw") or {}
        countries = raw.get("country") or []
        if isinstance(countries, str):
            countries = [countries]
        if not any("mozambique" in c.lower() for c in countries):
            continue

        title = (item.get("title") or raw.get("title") or "").strip()
        url = item.get("clickUri") or raw.get("clickableuri") or ""
        if not title or not url or url in seen:
            continue
        seen.add(url)

        city = (raw.get("city") or "").strip()
        location = city if city and city.lower() != "multi-location" else "Moçambique"
        level = raw.get("jobexperiencelevel")
        if isinstance(level, list):
            level = ", ".join(level)

        description = f"{title}. {COMPANY}, {location}." + (f" Nível: {level}." if level else "")
        job = {
            "title": title,
            "company": COMPANY,
            "location": location,
            "description": description,
            "url": url,
            "source": "slb",
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue
        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
