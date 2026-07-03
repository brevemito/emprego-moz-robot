from bs4 import BeautifulSoup


def parse_emprego_co_mz(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # Seleciona todos os links
    for a in soup.find_all("a"):
        title = a.get_text(strip=True)

        if not title:
            continue

        title_lower = title.lower()

        # 🔴 FILTRO DE LIXO (menus e conteúdo irrelevante)
        lixo = [
            "cookie",
            "política",
            "privacidade",
            "login",
            "register",
            "subscribe",
            "sobre nós",
            "contacto",
            "faq"
        ]

        if len(title) < 20:
            continue

        if any(x in title_lower for x in lixo):
            continue

        job = {
            "title": title,
            "company": "",
            "location": "Moçambique",
            "description": title,
            "url": source_url,
            "source": "emprego_co_mz"
        }

        jobs.append(job)

    return jobs
