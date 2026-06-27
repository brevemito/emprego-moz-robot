# Robô de recolha de empregos - Moçambique
import requests
from bs4 import BeautifulSoup
from sources import SOURCES


# Palavras que indicam lixo / conteúdo não relacionado a vagas
IGNORE_KEYWORDS = [
    "whatsapp",
    "baixar agora",
    "subscribe",
    "telegram",
    "http",
    "+",
    "clique aqui",
    "download",
    "share",
    "login",
    "register"
]


def is_valid_job_text(text: str) -> bool:
    """
    Filtra textos irrelevantes.
    Mantém apenas candidatos prováveis a título de vaga.
    """

    if not text:
        return False

    text = text.strip()

    # Rejeita textos curtos demais
    if len(text) < 15:
        return False

    # Rejeita textos com lixo conhecido
    lower_text = text.lower()
    for word in IGNORE_KEYWORDS:
        if word in lower_text:
            return False

    # Evita números de contacto e spam óbvio
    if any(char.isdigit() for char in text) and len(text) < 40:
        return False

    return True


def fetch_jobs():
    all_jobs = []

    for source in SOURCES:
        print(f"\nA recolher de: {source['name']}")

        try:
            response = requests.get(
                source["url"],
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            )

            soup = BeautifulSoup(response.text, "html.parser")

            # estratégia simples inicial (será melhorada depois)
            links = soup.find_all("a")

            count = 0

            for link in links:
                text = link.get_text(strip=True)

                if is_valid_job_text(text):
                    all_jobs.append({
                        "title": text,
                        "company": "",
                        "location": "Moçambique",
                        "description": text,
                        "url": source["url"],
                        "source": source["name"]
                    })
                    count += 1

            print(f"Vagas filtradas: {count}")

        except Exception as e:
            print(f"Erro ao processar {source['name']}: {e}")

    return all_jobs


if __name__ == "__main__":
    jobs = fetch_jobs()

    print("\n==============================")
    print("TOTAL DE VAGAS ENCONTRADAS:", len(jobs))
    print("==============================\n")

    for job in jobs[:10]:
        print(job)
