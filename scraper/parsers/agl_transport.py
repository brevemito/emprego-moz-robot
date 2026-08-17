import xml.etree.ElementTree as ET


def parse_agl_transport(xml_text, source_url):
    """
    A AGL (Africa Global Logistics) disponibiliza um feed RSS já filtrado
    por país. O URL configurado em sources.py aponta directamente para o
    feed de Moçambique (Rss_JobCountry=159), por isso aqui basta ler os
    itens do RSS, sem necessidade de filtrar por localização.
    """
    jobs = []
    seen_urls = set()  # Deduplicação dentro do feed

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return jobs

    for item in root.iter("item"):

        title_el = item.find("title")
        link_el = item.find("link")

        title = (title_el.text or "").strip() if title_el is not None else ""
        link = (link_el.text or "").strip() if link_el is not None else ""

        if not title or len(title) < 10:
            continue

        if not link:
            link = source_url

        # Nota: ao contrário de outras fontes, aqui o identificador da vaga
        # (idOffre) vai na query string, por isso usamos o URL completo na
        # deduplicação em vez de o cortar em "?".
        if link in seen_urls:
            continue
        seen_urls.add(link)

        # O título do RSS vem no formato "2026-10240 - ASSISTENTE DE HST M/F"
        # Removemos a referência numérica inicial para ficar mais legível.
        clean_title = title
        if " - " in title:
            prefix, rest = title.split(" - ", 1)
            if prefix.replace("-", "").isdigit():
                clean_title = rest.strip()

        jobs.append({
            "title": clean_title,
            "company": "AGL (Africa Global Logistics)",
            "location": "Moçambique",
            "description": clean_title,
            "url": link,
            "source": "agl_transport"
        })

    return jobs
