import json

# A página pública reliefweb.int/jobs é renderizada em JavaScript (React) -
# um GET simples devolve uma shell HTML vazia. Por isso trocámos para a
# API pública em JSON do ReliefWeb (https://apidoc.reliefweb.int/).
#
# LIMITAÇÃO CONHECIDA (confirmada em produção): a partir de 1 de Novembro
# de 2025, a API do ReliefWeb passou a EXIGIR um parâmetro "appname"
# PRÉ-APROVADO pela equipa do ReliefWeb - deixou de aceitar qualquer
# valor arbitrário. Sem essa aprovação prévia, a API devolve
# "403 Forbidden" (não é um bug de código, é uma exigência deles).
#
# Para resolver definitivamente:
#   1. Contactar o ReliefWeb em https://reliefweb.int/contact a pedir
#      aprovação de um appname (ex.: o domínio "brevemito.com").
#   2. Depois de aprovado, actualizar o parâmetro appname= em
#      scraper/sources.py com o nome aprovado.
#
# Até lá, esta fonte falha de forma controlada (devolve 0 candidatos,
# sem rebentar o resto do scraper) - main.py já trata isto como
# "network_error"/"erro" e continua normalmente para as outras fontes.


def parse_reliefweb(response_text, source_url):
    jobs = []
    seen_urls = set()

    try:
        data = json.loads(response_text)
    except (ValueError, TypeError):
        return jobs

    for item in data.get("data", []):

        fields = item.get("fields", {})

        title = (fields.get("title") or "").strip()

        if not title:
            continue

        link = fields.get("url_alias") or fields.get("url") or source_url

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        company = "ReliefWeb"
        sources = fields.get("source") or []
        if sources and isinstance(sources, list):
            first_source_name = sources[0].get("name")
            if first_source_name:
                company = first_source_name

        countries = fields.get("country") or []
        location = "Moçambique"
        if countries and isinstance(countries, list):
            country_names = [c.get("name") for c in countries if c.get("name")]
            if country_names:
                location = ", ".join(country_names)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "description": title,
            "url": link,
            "source": "reliefweb"
        })

    return jobs
