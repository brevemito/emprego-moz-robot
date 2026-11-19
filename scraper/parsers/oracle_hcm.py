import json

import requests

import job_validator as jv

# =========================================================================
# Portais de recrutamento Oracle Cloud HCM ("Candidate Experience")
# =========================================================================
#
# Usado por grandes empresas com operações em Moçambique:
#   - ExxonMobil (Rovuma LNG):  fa-exmi-saasfaprod1.fa.ocs.oraclecloud.com, site CX_1
#   - Eni (Coral Sul FLNG):     jobs.eni.com, site CX_1004
#
# A página de vagas é uma aplicação JavaScript, mas os dados vêm de uma
# API pública em JSON (a mesma que o navegador usa):
#   /hcmRestApi/resources/latest/recruitingCEJobRequisitions
#     ?onlyData=true&expand=requisitionList.secondaryLocations
#     &finder=findReqs;siteNumber=<SITE>,limit=25,offset=<N>,sortBy=POSTING_DATES_DESC
# Cada vaga traz o país em "PrimaryLocationCountry" (código ISO, ex.: MZ)
# e as localizações secundárias em "secondaryLocations". Ficam só as
# vagas com Moçambique numa dessas localizações.
#
# O URL da fonte (em sources.py) é a primeira página da API; este parser
# percorre as páginas seguintes até ao fim (com limite de segurança).
# =========================================================================

PAGE_SIZE = 25
MAX_PAGES = 40  # até 1000 vagas por empresa

HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/138.0 Safari/537.36"
    ),
}


def _api_url(base, site, offset):
    return (
        f"{base}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        f"?onlyData=true&expand=requisitionList.secondaryLocations"
        f"&finder=findReqs;siteNumber={site},limit={PAGE_SIZE},offset={offset},sortBy=POSTING_DATES_DESC"
    )


def _requisitions(payload):
    try:
        return payload["items"][0].get("requisitionList") or []
    except (KeyError, IndexError, TypeError, AttributeError):
        return []


def _in_mozambique(req):
    if (req.get("PrimaryLocationCountry") or "").upper() == "MZ":
        return True
    places = [req.get("PrimaryLocation") or ""]
    places += [s.get("Name") or "" for s in req.get("secondaryLocations") or []]
    return any("mozambique" in p.lower() or "moçambique" in p.lower() for p in places)


def _location(req):
    for place in [req.get("PrimaryLocation") or ""] + [s.get("Name") or "" for s in req.get("secondaryLocations") or []]:
        if "mozambique" in place.lower() or "moçambique" in place.lower():
            city = place.split(",")[0].strip()
            return city if city.lower() not in ("mozambique", "moçambique") else "Moçambique"
    return "Moçambique"


def make_oracle_parser(base, site, company, source_name):
    """Cria um parser para um portal Oracle HCM concreto."""

    def parse(text, source_url):
        jobs = []
        seen = set()

        try:
            first = json.loads(text)
        except (ValueError, TypeError):
            first = None

        for page in range(MAX_PAGES):
            if page == 0 and first is not None:
                payload = first
            else:
                try:
                    r = requests.get(_api_url(base, site, page * PAGE_SIZE), headers=HEADERS, timeout=30)
                    r.raise_for_status()
                    payload = r.json()
                except (requests.exceptions.RequestException, ValueError):
                    break

            reqs = _requisitions(payload)
            if not reqs:
                break

            for req in reqs:
                if not _in_mozambique(req):
                    continue
                req_id = str(req.get("Id") or "")
                title = (req.get("Title") or "").strip()
                if not req_id or not title or req_id in seen:
                    continue
                seen.add(req_id)

                url = f"{base}/hcmUI/CandidateExperience/en/sites/{site}/job/{req_id}"
                summary = (req.get("ShortDescriptionStr") or "").strip()
                job = {
                    "title": title,
                    "company": company,
                    "location": _location(req),
                    "description": summary[:400] or title,
                    "url": url,
                    "source": source_name,
                }

                result = jv.classify(job["title"], job["description"], job["url"])
                if not result["is_valid"]:
                    continue
                job["validity_score"] = result["validity_score"]
                jobs.append(job)

            if len(reqs) < PAGE_SIZE:
                break

        return jobs

    return parse


parse_exxonmobil = make_oracle_parser(
    "https://fa-exmi-saasfaprod1.fa.ocs.oraclecloud.com", "CX_1", "ExxonMobil", "exxonmobil"
)

parse_eni = make_oracle_parser(
    "https://jobs.eni.com", "CX_1004", "Eni", "eni"
)
