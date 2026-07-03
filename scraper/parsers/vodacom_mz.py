from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_vodacom_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # Workday / portais corporativos usam links + títulos estruturados
    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

        if not title:
            continue

        title_lower = title.lower()

        # filtros de lixo corporativo
        lixo = [
            "cookie",
            "privacy",
            "terms",
            "login",
            "register",
            "sign in",
            "share",
            "follow",
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

        jobs.append({
            "title": title,
            "company": "Vodacom Moçambique",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "vodacom_mz"
        })

    return jobs
