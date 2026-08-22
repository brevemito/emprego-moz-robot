from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: a página institucional mozambiquelng.co.mz não
# lista vagas - é conteúdo descritivo sobre o projecto. No entanto, tem
# um link directo ("Apply to available jobs") para o portal de vagas da
# TotalEnergies (empresa operadora do projecto), filtrado especificamente
# pelo projecto Mozambique LNG. É essa página filtrada que configurámos
# como URL desta fonte em sources.py.
#
# Tal como em totalenergies.py, o filtro do URL não é totalmente fiável
# (o projecto tem vagas em várias localizações: Cabo Delgado/Afungi,
# Maputo, mas também Singapura, Milão, Houston), por isso confirmamos a
# localização lendo o texto de cada bloco de vaga, aceitando qualquer
# menção a Moçambique ou aos locais do projecto dentro do país.
JOB_DETAIL_URL_HINT = "/JobDetail/"

MOZAMBIQUE_LOCATION_HINTS = [
    "mozambique", "moçambique", "cabo delgado", "afungi", "palma", "maputo"
]


def _find_job_container(anchor):
    node = anchor
    for _ in range(6):
        if node.parent is None:
            break
        node = node.parent
        text = node.get_text(" ", strip=True).lower()
        if "apply" in text or "aplicar" in text:
            return node
    return anchor.parent or anchor


def parse_mozambique_lng(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):

        link = a["href"]

        if JOB_DETAIL_URL_HINT not in link:
            continue

        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        link = urljoin(source_url, link)

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue

        container = _find_job_container(a)
        container_text = container.get_text(" ", strip=True).lower()

        if not any(hint in container_text for hint in MOZAMBIQUE_LOCATION_HINTS):
            continue

        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "Mozambique LNG (TotalEnergies)",
            "location": "Moçambique",
            "description": container.get_text(" ", strip=True)[:400],
            "url": link,
            "source": "mozambique_lng"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
