from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_un_mozambique(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()  # Deduplicação dentro da página

    for a in soup.find_all("a"):

        title = a.get_text(separator=" ", strip=True)

        if not title or len(title) < 15:
            continue

        title_lower = title.lower()

        lixo = [
            "cookie",
            "política",
            "privacidade",
            "privacy",
            "termos",
            "terms",
            "login",
            "início",
            "home",
            "contacto",
            "contact",
            "sobre",
            "search",
            "pesquisar",
            "mapa do site",
            "site index",
            "fraud",
            "fraude",
            "copyright",
            "direitos de reprodução",
            "facebook",
            "twitter",
            "instagram",
            "youtube",
            "flickr",
            "carreiras nas nações unidas",
            "vistar carreiras",
            "processo de candidatura",
            "criar a sua candidatura",
            "ver todos os concursos",
            "na entrevista"
        ]

        if any(x in title_lower for x in lixo):
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        jobs.append({
            "title": title,
            "company": "Nações Unidas Moçambique",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "un_mozambique"
        })

    return jobs
