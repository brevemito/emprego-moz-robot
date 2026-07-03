from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_movitel(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

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
            "search",
            "mapa do site",
            "facebook",
            "twitter"
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

        jobs.append({
            "title": title,
            "company": "Movitel",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "movitel"
        })

    return jobs
