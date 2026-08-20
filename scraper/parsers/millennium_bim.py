from bs4 import BeautifulSoup
from urllib.parse import urljoin

import job_validator as jv

# NOTA IMPORTANTE (investigação): a página institucional
# millenniumbim.co.mz/.../carreira NÃO expõe uma lista estruturada de
# vagas com páginas de detalhe individuais - o banco usa um sistema
# externo de candidatura espontânea (candidaturas.millenniumbim.co.mz) e
# anuncia vagas pontuais via LinkedIn. Não existe, por isso, um padrão de
# URL de "detalhe de vaga" fiável nesta página para usar como evidência
# estrutural (ao contrário de emprego.co.mz ou contact.co.mz).
#
# Nestes casos, a extracção continua a percorrer todos os links da
# página, mas a decisão de incluir ou não cada candidato passa a ser
# feita pelo JobValidator central (scraper/job_validator.py), que exige
# evidência positiva de cargo/vaga em vez de uma lista de palavras a
# excluir. Na prática, isto significa que esta fonte só produzirá
# resultados quando o banco publicar mesmo uma vaga com título de cargo
# reconhecível nesta página - caso contrário, devolve 0 resultados, o
# que é o comportamento correcto (não inventar vagas onde não existem).


def parse_millennium_bim(html, source_url):
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    seen_urls = set()

    for a in soup.find_all("a"):

        title = a.get_text(separator=" ", strip=True)

        if not title:
            continue

        link = a.get("href")

        if link:
            link = urljoin(source_url, link)
        else:
            link = source_url

        normalized_url = link.split("?")[0]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)

        job = {
            "title": title,
            "company": "Millennium BIM",
            "location": "Moçambique",
            "description": title,
            "url": link,
            "source": "millennium_bim"
        }

        result = jv.classify(job["title"], job["description"], job["url"])
        if not result["is_valid"]:
            continue

        job["validity_score"] = result["validity_score"]
        jobs.append(job)

    return jobs
