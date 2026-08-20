from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# ESTRUTURA CONFIRMADA: a fonte anterior apontava para a homepage da
# TotalEnergies (jobs.totalenergies.com/.../Home), que é uma SPA e não
# devolve vagas em HTML simples - daí o histórico de 0 resultados.
#
# A página de resultados de pesquisa (.../SearchJobs/Mozambique/?...), no
# entanto, É renderizada no servidor e contém páginas de detalhe em
# /JobDetail/<slug>/<id>. Nota importante: o filtro de país no próprio URL
# NÃO filtra de facto os resultados devolvidos (a listagem mistura vagas
# de vários países) - por isso este parser confirma o país correcto lendo
# o texto de cada bloco de vaga, não confiando apenas no URL.
JOB_DETAIL_URL_HINT = "/JobDetail/"


def _find_job_container(anchor):
    """
    Sobe na árvore DOM a partir do link do título até encontrar o bloco
    que representa a vaga inteira (título + data + país + tipo de
    contrato + empresa + link "Apply"). Usamos a presença de um link
    "Apply" no mesmo bloco como sinal estrutural de que chegámos ao
    contentor correcto, em vez de assumir nomes de classes CSS que podem
    mudar.
    """
    node = anchor
    for _ in range(6):
        if node.parent is None:
            break
        node = node.parent
        text = node.get_text(" ", strip=True).lower()
        if "apply" in text or "aplicar" in text:
            return node
    return anchor.parent or anchor


def parse_totalenergies(html, source_url):
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
        container_text = container.get_text(" ", strip=True)

        # Evidência estrutural de localização: só aceitamos se o bloco da
        # vaga mencionar mesmo Moçambique, já que o filtro do URL sozinho
        # não é fiável nesta plataforma.
        if "mozambique" not in container_text.lower() and "moçambique" not in container_text.lower():
            continue

        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "TotalEnergies",
            "location": "Moçambique",
            "description": container_text[:400],
            "url": link,
            "source": "totalenergies"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
