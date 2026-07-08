from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_emprego_co_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()  # Tarefa 4: Deduplicação dentro da página

    for a in soup.find_all("a"):

        # Tarefa 2: Separador de espaço na extração
        title = a.get_text(separator=" ", strip=True)

        if not title or len(title) < 20:
            continue

        # tenta capturar link real da vaga
        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        title_lower = title.lower()

        lixo = [
            "cookie",
            "política",
            "privacidade",
            "login",
            "register",
            "sobre nós",
            "contacto",
            "faq",
            "subscribe"
        ]

        if any(x in title_lower for x in lixo):
            continue

        # Tarefa 4: Normalizar URL e verificar duplicação
        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "emprego_co_mz"
        }

        jobs.append(job)

    return jobs
