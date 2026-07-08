from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_bci(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()  # Tarefa 4: Deduplicação dentro da página

    for a in soup.find_all("a"):

        # Tarefa 2: Separador de espaço na extração
        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        title_lower = title.lower()

        lixo = [
            "cookie",
            "privacy",
            "termos",
            "login",
            "register",
            "início",
            "home",
            "contacto",
            "sobre nós",
            "search"
        ]

        if len(title) < 10:
            continue

        if any(x in title_lower for x in lixo):
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        # Tarefa 4: Normalizar URL e verificar duplicação
        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        jobs.append({
            "title": title,
            "company": "BCI",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "bci"
        })

    return jobs
