import json
import re
import unicodedata
from datetime import datetime, timezone
from database import get_connection
from job_category import categorize
from job_level import classify, rank, LEVEL_LABELS


def _to_iso8601(sqlite_timestamp):
    """
    Converte o formato do SQLite ("YYYY-MM-DD HH:MM:SS", em UTC) para
    ISO 8601 ("YYYY-MM-DDTHH:MM:SSZ"), que é o formato que o
    JavaScript (new Date(...)) e a generalidade das APIs/frontends
    conseguem interpretar directamente sem ambiguidade de fuso horário.
    """
    if not sqlite_timestamp:
        return None
    return sqlite_timestamp.replace(" ", "T") + "Z"


def _days_since(sqlite_timestamp):
    """
    Calcula há quantos dias completos uma vaga foi vista pela primeira
    vez (created_at), para o site poder mostrar por exemplo "Publicada
    há 5 dias" sem ter de fazer essa conta no frontend.
    """
    if not sqlite_timestamp:
        return None
    try:
        seen = datetime.strptime(sqlite_timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    delta = datetime.now(timezone.utc) - seen
    return max(delta.days, 0)


# =========================
# DEDUPLICAÇÃO ENTRE FONTES
# =========================
# A mesma vaga aparece muitas vezes em mais do que uma fonte (ex.: uma
# vaga da CONTACT está no site da CONTACT e também no emprego.co.mz). A
# base de dados só junta cópias com o mesmo título+empresa+URL, por isso
# aqui juntamos as cópias da mesma vaga vindas de fontes diferentes e
# fica a da fonte mais próxima do empregador (link mais "oficial"),
# mantendo a data em que a vaga foi vista pela primeira vez.
# Número menor = fonte preferida. Fontes não listadas valem 50.
SOURCE_PRIORITY = {
    "contact_mz": 10,
    "emprego_co_mz": 80,
    "reliefweb": 85,
    "unjobs": 90,
}


def _plain(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


GENERIC_WORDS = {"", "desconhecida", "mocambique", "mozambique"}


# =========================
# SEGURANÇA
# =========================
# 1) Só links normais (http/https). Um link "javascript:..." vindo de uma
#    fonte comprometida seria executado no site quando alguém tocasse em
#    "Candidatar" - por isso essas vagas nunca são publicadas.
SAFE_URL = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

# 2) Vagas-burla: anúncios que pedem dinheiro ao candidato. Frases
#    específicas, para não apanhar cargos legítimos como "Técnico de
#    Pagamentos" ou "Gestor de Produto M-Pesa".
SCAM_PATTERNS = [
    r"taxa de (inscricao|candidatura|processamento|registo|admissao|seleccao|selecao)",
    r"(pagar|pague|efectue|efetue|efectuar|efetuar|faca|fazer) (uma |a |o )?(taxa|pagamento|deposito)",
    r"(via|por|pelo|para o|numero( de)?) (m-?pesa|e-?mola|mkesh)",
    r"deposito (de|no valor)",
    r"(envie|enviar|transfira|transferir) (o |um |uma )?(valor|montante|dinheiro|quantia)",
    r"\bpay (a|the|an) (fee|registration|processing|application)",
    r"\bapplication fee\b",
]
_SCAM_RE = re.compile("|".join(SCAM_PATTERNS))


def is_safe_url(url):
    return bool(url) and bool(SAFE_URL.match(url.strip()))


def looks_like_scam(title, description):
    return bool(_SCAM_RE.search(_plain((title or "") + " " + (description or ""))))


def _norm_title(title):
    t = _plain(title)
    t = re.sub(r"\((m/f|f/m|m/f/d|h/m)\)", " ", t)
    t = re.sub(r"[-–—]?\s*\(?\d+\)?\s*vagas?\b", " ", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _first_word(text):
    words = re.sub(r"[^a-z0-9 ]+", " ", _plain(text)).split()
    return words[0] if words else ""


def _compatible(a, b):
    """Mesma empresa e mesmo local - ou um dos dois é genérico/desconhecido."""
    for field in ("company", "location"):
        x, y = _first_word(a.get(field)), _first_word(b.get(field))
        if x not in GENERIC_WORDS and y not in GENERIC_WORDS and x != y:
            return False
    return True


def _better(a, b):
    """Escolhe a cópia a manter: fonte mais oficial; depois a mais completa."""
    pa = SOURCE_PRIORITY.get(a.get("source"), 50)
    pb = SOURCE_PRIORITY.get(b.get("source"), 50)
    if pa != pb:
        return a if pa < pb else b
    known_a = _first_word(a.get("company")) not in GENERIC_WORDS
    known_b = _first_word(b.get("company")) not in GENERIC_WORDS
    if known_a != known_b:
        return a if known_a else b
    return a if (a.get("last_seen_at") or "") >= (b.get("last_seen_at") or "") else b


def dedupe_across_sources(jobs):
    """
    Junta cópias da mesma vaga: o mesmo link, ou o mesmo título com
    empresa e local compatíveis. Vagas iguais em locais diferentes (ex.:
    "Digitador de dados" em 7 cidades) continuam separadas.
    Devolve (vagas_sem_repetidas, numero_de_repetidas_juntadas).
    """
    kept = []
    by_url = {}
    by_title = {}
    for job in jobs:
        url = (job.get("url") or "").rstrip("/")
        match = by_url.get(url) if url else None
        if match is None:
            for cand in by_title.get(_norm_title(job.get("title")), []):
                if _compatible(cand, job):
                    match = cand
                    break
        if match is None:
            kept.append(job)
            if url:
                by_url[url] = job
            by_title.setdefault(_norm_title(job.get("title")), []).append(job)
            continue
        winner = _better(match, job)
        oldest = min(filter(None, [match.get("created_at"), job.get("created_at")]), default=None)
        if winner is job:
            match.clear()
            match.update(job)
        match["created_at"] = oldest
    return kept, len(jobs) - len(kept)


def export_jobs_to_json():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            job_id,
            title,
            company,
            location,
            description,
            url,
            source,
            score,
            created_at,
            last_seen_at
        FROM jobs
        ORDER BY score DESC, created_at DESC
    """)

    rows, merged = dedupe_across_sources([dict(r) for r in cursor.fetchall()])
    if merged:
        print(f"🔁 {merged} vaga(s) repetida(s) noutra fonte foram juntadas (fica o link mais oficial).")

    jobs = []
    unsafe = scams = 0

    for row in rows:
        job = dict(row)

        title = job.get("title") or ""
        description = job.get("description") or ""

        if not is_safe_url(job.get("url")):
            unsafe += 1
            continue
        if looks_like_scam(title, description):
            scams += 1
            print(f"🚫 Vaga retirada (pede dinheiro ao candidato): {title[:70]} | {job.get('url')}")
            continue
        location = job.get("location") or "Moçambique"

        # Se a descrição for apenas uma repetição do título (comum nas
        # fontes que não fornecem descrição própria), não faz sentido
        # expor o mesmo texto duas vezes no site - fica a null, para o
        # frontend saber que não há descrição adicional a mostrar.
        clean_description = description if description.strip() != title.strip() else None

        # Localização como lista, além da string original, para o site
        # poder filtrar por província/cidade sem ter de reprocessar o
        # texto (ex.: "Cabo Delgado, Pemba" -> ["Cabo Delgado", "Pemba"]).
        locations_list = [loc.strip() for loc in location.split(",") if loc.strip()]

        category = categorize(title, description)
        # Nível pedido e público (ver job_level.py): permite ao site
        # filtrar "Para o meu nível" e pôr o público principal primeiro.
        level, audience, lang = classify(job, category)

        jobs.append({
            "job_id": job.get("job_id"),
            "title": title,
            "company": job.get("company") or "Desconhecida",
            "location": location,
            "locations": locations_list,
            "category": category,
            "level": level,
            "level_label": LEVEL_LABELS.get(level, ""),
            "audience": audience,
            "lang": lang,
            "description": clean_description,
            "url": job.get("url"),
            "source": job.get("source"),
            "score": job.get("score", 0),
            "scraped_at": _to_iso8601(job.get("created_at")),
            # Mantido por compatibilidade com integrações já existentes
            # que possam estar a ler o campo "created_at" directamente.
            "created_at": job.get("created_at"),
            # Novos campos, só significativos desde que a base de dados
            # passou a ser "semeada" com o histórico entre execuções
            # (ver database.seed_from_previous_export): antes disso,
            # first_seen_at e last_seen_at eram sempre iguais a
            # scraped_at, porque cada execução começava do zero.
            "first_seen_at": _to_iso8601(job.get("created_at")),
            "last_seen_at": _to_iso8601(job.get("last_seen_at")),
            "days_since_first_seen": _days_since(job.get("created_at")),
        })
        jobs[-1]["rank"] = rank(jobs[-1], jobs[-1]["score"])
        # Página própria de cada vaga (gerada por site_pages.py).
        jobs[-1]["page"] = "vagas/" + re.sub(r"[^A-Za-z0-9_-]", "_", jobs[-1]["job_id"] or "") + ".html"

    jobs.sort(key=lambda j: -(j.get("rank") or 0))

    with open(
        "data/jobs.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=4
        )

    conn.close()

    print(f"JSON exportado com {len(jobs)} vagas.")
    if unsafe or scams:
        print(f"🛡️ Segurança: {unsafe} vaga(s) com link inválido e {scams} possível(is) burla(s) não foram publicadas.")

    # Páginas por vaga, sitemap.xml e texto do canal. Uma falha aqui
    # nunca impede a publicação do jobs.json.
    try:
        from site_pages import generate_site
        generate_site(jobs)
    except Exception as err:  # noqa: BLE001
        print(f"⚠️ Não foi possível gerar as páginas do site: {err}")
