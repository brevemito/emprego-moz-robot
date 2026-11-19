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
#
# A página inicial mostra só as vagas activas, cada uma num cartão
# <li class="grid-list-el"> com: título (h3), resumo (h4), empresa
# (a.company) e local (span.location). Lemos esses campos do cartão
# para cada vaga ter empresa e local reais (antes ficava tudo como
# "Moçambique" e "Desconhecida").
JOB_DETAIL_URL_HINT = "/vaga/"

# Vagas publicadas no emprego.co.mz mas para trabalhar fora do país
# (ex.: recrutamento para Portugal). O público do site procura trabalho
# em Moçambique, por isso ficam de fora.
FOREIGN_LOCATIONS = ("portugal", "angola", "brasil", "south africa", "áfrica do sul", "dubai", "qatar")


def _text(node, selector):
    found = node.select_one(selector) if node else None
    return found.get_text(" ", strip=True) if found else ""


def _card_of(a):
    """Cartão da vaga (li da grelha da página inicial ou da listagem)."""
    return a.find_parent("li")


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

        card = _card_of(a)
        summary = _text(card, "h4")
        company = _text(card, "a.company") or _text(card, "a.companylink")
        location = _text(card, "span.location a") or _text(card, "span.location")

        # Cartões das listagens de pesquisa/categoria trazem "Expirado"
        # no fim; a página inicial só tem vagas activas, mas fica a
        # protecção para o caso de o URL da fonte mudar.
        card_text = card.get_text(" ", strip=True) if card else ""
        if card_text.endswith("Expirado"):
            continue

        where = f"{location} {summary}".lower()
        if any(f in where for f in FOREIGN_LOCATIONS) and "moçambique" not in where:
            continue

        job = {
            "title": title,
            "company": company,
            "location": location or "Moçambique",
            "description": summary or title,
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
