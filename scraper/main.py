# Robô de recolha de empregos - Moçambique
import requests
from bs4 import BeautifulSoup
from sources import SOURCES

def fetch_jobs():
    all_jobs = []

    for source in SOURCES:
        print(f"A recolher de: {source['name']}")

        response = requests.get(source["url"])
        soup = BeautifulSoup(response.text, "html.parser")

        # tentativa genérica de capturar títulos de vagas
        titles = soup.find_all("a")

        for t in titles:
            text = t.get_text(strip=True)

            if len(text) > 10:  # filtro simples
                all_jobs.append({
                    "title": text,
                    "company": "",
                    "location": "Moçambique",
                    "description": text,
                    "url": source["url"],
                    "source": source["name"]
                })

    return all_jobs


if __name__ == "__main__":
    jobs = fetch_jobs()
    print(f"Total de vagas encontradas: {len(jobs)}")

    for job in jobs[:10]:
        print(job)
