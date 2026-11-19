import re
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA (Nov 2026): a lista de ofertas está em
# https://www.contact.co.mz/pt/recrutamento/ofertas-de-emprego (a página
# inicial deixou de listar vagas - por isso a fonte dava 0 resultados).
# Cada oferta é um <div class="oferta"> com:
#   h3.titulo a  -> título e link /recrutamento/oferta-de-emprego/<hash>/<slug>
#   span.data    -> data de publicação ("19-11-2026 às 12:57")
#   span.local   -> local ("Quelimane, Zambezia Province, Mozambique")
# A CONTACT é uma agência de recrutamento licenciada pelo INEP, com
# muitas vagas de nível médio e de entrada (atendedores, digitadores,
# motoristas, estagiários) - exactamente o público do site.
JOB_DETAIL_URL_HINT = "oferta-de-emprego/"

PROVINCES_PT = {
    "maputo province": "Maputo Província",
    "maputo city": "Maputo",
    "gaza province": "Gaza",
    "inhambane province": "Inhambane",
    "sofala province": "Sofala",
    "manica province": "Manica",
    "tete province": "Tete",
    "zambezia province": "Zambézia",
    "nampula province": "Nampula",
    "cabo delgado province": "Cabo Delgado",
    "niassa province": "Niassa",
}


def _clean_location(raw):
    """'Quelimane, Zambezia Province, Mozambique' -> 'Quelimane, Zambézia'."""
    parts = [p.strip() for p in re.split(r",", raw or "") if p.strip()]
    parts = [p for p in parts if p.lower() not in ("mozambique", "moçambique")]
    out = []
    for p in parts:
        p = PROVINCES_PT.get(p.lower(), p.replace(" District", ""))
        if p not in out:
            out.append(p)
    return ", ".join(out) or "Moçambique"


def _refetch(source_url):
    try:
        r = requests.get(source_url, timeout=25, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        })
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException:
        return ""


def parse_contact_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    # O site da CONTACT às vezes devolve uma página incompleta, sem a
    # lista (visto nos testes: ~18 KB em vez de ~42 KB). Nesse caso
    # tentamos de novo, até 2 vezes, antes de desistir.
    for _ in range(2):
        if soup.select("div.oferta"):
            break
        time.sleep(3)
        soup = BeautifulSoup(_refetch(source_url), "html.parser")

    jobs = []
    seen_urls = set()

    blocks = soup.select("div.oferta") or [soup]

    for block in blocks:
        for a in block.select("h3 a") or block.find_all("a"):

            title = a.get_text(separator=" ", strip=True)
            link = a.get("href")
            if not title or not link:
                continue
            # "Candidatura Espontânea" é um formulário permanente para
            # enviar CV, não uma vaga.
            if "espontânea" in title.lower() or "espontanea" in title.lower():
                continue

            link = urljoin(source_url, link)
            if JOB_DETAIL_URL_HINT not in link:
                continue

            normalized_url = link.split("?")[0]
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            local = block.select_one("span.local") if block is not soup else None
            location = _clean_location(local.get_text(" ", strip=True)) if local else "Moçambique"

            job = {
                "title": title,
                "company": "CONTACT",
                "location": location,
                "description": f"{title}. Recrutamento CONTACT em {location}.",
                "url": link,
                "source": "contact_mz"
            }

            result = jv.classify(job["title"], job["description"], job["url"])
            if not result["is_valid"]:
                continue

            job["validity_score"] = result["validity_score"]
            jobs.append(job)

    return jobs
