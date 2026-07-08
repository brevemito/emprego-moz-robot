from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_unjobs(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()  # Tarefa 4: Deduplicação dentro da página

    # UNJobs normalmente usa links diretos para vagas
    for a in soup.find_all("a"):

        # Tarefa 2: Separador de espaço na extração
        title = a.get_text(separator=" ", strip=True)

        if not title or len(title) < 10:
            continue

        title_lower = title.lower()

        lixo = [
            "home",
            "about",
            "contact",
            "privacy",
            "terms",
            "login",
            "register"
        ]

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
            "company": "UN Jobs",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "unjobs"
        })

    return jobs
