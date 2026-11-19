from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import job_validator as jv

# =========================================================================
# Halliburton - jobs.halliburton.com (SAP SuccessFactors, HTML no servidor)
# =========================================================================
#
# A pesquisa por país não funciona sem JavaScript, mas o site tem uma
# página por região, já renderizada no servidor. Moçambique está na
# região "Europe & Sub-Saharan Africa (ESSA)":
#   https://jobs.halliburton.com/go/Europe-&-Sub-Saharan-Africa-%28ESSA%29/8411900/
# Cada vaga é uma linha <tr class="data-row"> com o título
# (a.jobTitle-link) e o local (span.jobLocation, ex.: "Pemba, P, MZ").
# Percorremos as páginas da região (25 vagas por página) e ficamos só
# com as de Moçambique (código de país MZ no local).
# =========================================================================

COMPANY = "Halliburton"
PAGE_SIZE = 25
MAX_PAGES = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/138.0 Safari/537.36"
    )
}


def _page_url(source_url, page):
    base = source_url.split("?")[0].rstrip("/") + "/"
    if page:
        base += f"{page * PAGE_SIZE}/"
    return base + "?q=&sortColumn=referencedate&sortDirection=desc"


def _is_mozambique(location):
    parts = [p.strip().upper() for p in (location or "").split(",")]
    return "MZ" in parts or "MOZAMBIQUE" in (location or "").upper()


def _rows(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.select("tr.data-row")


def parse_halliburton(html, source_url):
    jobs = []
    seen = set()

    for page in range(MAX_PAGES):
        if page == 0:
            rows = _rows(html)
        else:
            try:
                r = requests.get(_page_url(source_url, page), headers=HEADERS, timeout=25)
                r.raise_for_status()
                rows = _rows(r.text)
            except requests.exceptions.RequestException:
                break

        if not rows:
            break

        for row in rows:
            a = row.select_one("a.jobTitle-link")
            loc = row.select_one("span.jobLocation")
            if not a or not a.get("href"):
                continue
            location_raw = loc.get_text(" ", strip=True) if loc else ""
            if not _is_mozambique(location_raw):
                continue

            url = urljoin("https://jobs.halliburton.com/", a["href"])
            if url in seen:
                continue
            seen.add(url)

            city = location_raw.split(",")[0].strip() or "Moçambique"
            title = a.get_text(" ", strip=True)
            job = {
                "title": title,
                "company": COMPANY,
                "location": city,
                "description": f"{title}. {COMPANY}, {city}.",
                "url": url,
                "source": "halliburton",
            }
            result = jv.classify(job["title"], job["description"], job["url"])
            if not result["is_valid"]:
                continue
            job["validity_score"] = result["validity_score"]
            jobs.append(job)

        if len(rows) < PAGE_SIZE:
            break

    return jobs
