# Robô de recolha de empregos - Moçambique
import requests
from bs4 import BeautifulSoup
from sources import SOURCES
from scoring import score_job


IGNORE_KEYWORDS = [
    "whatsapp",
    "baixar agora",
    "subscribe",
    "telegram",
    "+",
    "http",
    "clique aqui",
    "login",
    "register"
]


def is_valid(text):
    if not text:
        return False

    text = text.strip().lower()

    if len(text) < 15:
        return False

    if any(k in text for k in IGNORE_KEYWORDS):
        return False

    return True


def fetch_jobs():
    jobs = []
    seen = set()

    for source in SOURCES:
        print(f"\nA recolher de: {source['name']}")

        try:
            r = requests.get(
                source["url"],
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a"):
                title = a.get_text(strip=True)

                if not is_valid(title):
                    continue

                # remover duplicados
                key = title.lower()
                if key in seen:
                    continue

                seen.add(key)

                job = {
                    "title": title,
                    "company": "",
                    "location": "Moçambique",
                    "description": title,
                    "url": source["url"],
                    "source": source["name"]
                }

                job["score"] = score_job(job)

                jobs.append(job)

        except Exception as e:
            print(f"Erro em {source['name']}: {e}")

    return jobs


if __name__ == "__main__":
    jobs = fetch_jobs()

    # ordenar por relevância
    jobs = sorted(jobs, key=lambda x: x["score"], reverse=True)

    print("\n========================")
    print("TOTAL LIMPO:", len(jobs))
    print("========================\n")

    for job in jobs[:20]:
        print(job)
