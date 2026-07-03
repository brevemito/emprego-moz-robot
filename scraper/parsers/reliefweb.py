from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_reliefweb(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # ReliefWeb usa links com estrutura relativamente limpa
    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

        if not title or len(title) < 10:
            continue

        title_lower = title.lower()

        lixo = [
            "home",
            "about",
            "contact",
            "terms",
            "privacy",
            "login",
            "subscribe",
            "rss"
        ]

        if any(x in title_lower for x in lixo):
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        jobs.append({
            "title": title,
            "company": "ReliefWeb",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "reliefweb"
        })

    return jobs
