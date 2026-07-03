from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_unjobs(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # UNJobs normalmente usa links diretos para vagas
    for a in soup.find_all("a"):

        title = a.get_text(strip=True)

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

        jobs.append({
            "title": title,
            "company": "UN Jobs",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "unjobs"
        })

    return jobs
