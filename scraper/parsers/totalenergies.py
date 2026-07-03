from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_totalenergies(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # TotalEnergies usa blocos de "a" e "div" estruturados
    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

        if not title:
            continue

        title_lower = title.lower()

        # filtros de lixo
        lixo = [
            "cookie",
            "privacy",
            "terms",
            "login",
            "register",
            "share",
            "follow",
            "read more"
        ]

        if len(title) < 15:
            continue

        if any(x in title_lower for x in lixo):
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        job = {
            "title": title,
            "company": "TotalEnergies",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "totalenergies"
        }

        jobs.append(job)

    return jobs
