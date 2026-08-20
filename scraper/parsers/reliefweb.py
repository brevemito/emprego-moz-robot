import json

# A página pública reliefweb.int/jobs é renderizada em JavaScript (React) -
# um GET simples devolve uma shell HTML vazia, por isso esta fonte
# produzia sempre 0 resultados. O ReliefWeb disponibiliza, no entanto,
# uma API pública em JSON (sem necessidade de chave de API para uso
# moderado) que devolve exactamente os mesmos dados de forma estruturada.
# Ver: https://apidoc.reliefweb.int/


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
