# =========================================================================
# Bolsas de estudo - recolha automática
# =========================================================================
#
# Recolhe bolsas de estudo internacionais a que candidatos moçambicanos
# podem concorrer e grava-as em data/bolsas.json, que o site
# (docs/bolsas.js) mostra no separador "Bolsas de Estudo".
#
# Fonte: Scholars4Dev (www.scholars4dev.com), apenas a lista
# "scholarships for africans" - bolsas cuja elegibilidade inclui
# candidatos de África (Moçambique incluído). Bolsas gerais, sem
# indicação de que estão abertas a africanos, ficam de fora.
# Cada anúncio tem uma estrutura fixa (título, entidade, nível/país e
# prazo), o robots.txt permite a leitura e as páginas são HTML simples.
#
# É um script INDEPENDENTE do main.py (vagas): se a recolha de bolsas
# falhar, as vagas continuam a ser actualizadas normalmente.
#
# Regras principais:
#   - Bolsas cujo prazo já passou saem automaticamente.
#   - Bolsas sem data reconhecível ficam, com o texto original do prazo,
#     até deixarem de aparecer na fonte durante MAX_DAYS_UNSEEN dias.
#   - Se a fonte falhar por completo, o ficheiro anterior é mantido
#     (só se removem as que expiraram) - uma falha de rede nunca apaga
#     a lista publicada.
#
# Correr localmente:   python scraper/bolsas.py
# =========================================================================

import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = Path("data/bolsas.json")

# Lista de bolsas abertas a candidatos africanos. O script lê a página 1,
# 2, 3... até encontrar uma página vazia (ou chegar a MAX_PAGES).
LISTING_URL = "https://www.scholars4dev.com/tag/scholarships-for-africans/"
MAX_PAGES = 20

SOURCE_NAME = "scholars4dev"
MAX_DAYS_UNSEEN = 45
PAUSE_BETWEEN_PAGES = 1.5  # segundos, para não sobrecarregar o site

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/138.0 Safari/537.36 "
        "emprego-moz-robot (+https://github.com/brevemito/emprego-moz-robot)"
    )
}


# =========================================================================
# PRAZOS
# =========================================================================
# Os prazos vêm em texto livre e com muitos formatos, por exemplo:
#   "15 Dec 2026"            "15 Dec 2026 (Masters)"
#   "5 Jan/31 Mar 2027"      "Dec 2026/Jan 2027"
#   "18 Dec 2026/10 Sep 2027"  "16 Nov 2026 – 2 Feb 2027 (varies by school)"
#   "Not specified (automatic with admission)"  "Coincides with MBA admission rounds"
# Extraímos todas as datas do texto e guardamos a PRÓXIMA que ainda não
# passou. Sem nenhuma data reconhecível, o prazo fica "None" e o site
# mostra o texto original ("ver no site").

MONTHS = {
    "jan": 1, "feb": 2, "fev": 2, "mar": 3, "apr": 4, "abr": 4, "may": 5,
    "mai": 5, "jun": 6, "jul": 7, "aug": 8, "ago": 8, "sep": 9, "set": 9,
    "oct": 10, "out": 10, "nov": 11, "dec": 12, "dez": 12,
}

_DATE_TOKEN = re.compile(
    r"(?:(\d{1,2})(?:st|nd|rd|th)?\s+)?"           # dia (opcional)
    r"(jan|feb|fev|mar|apr|abr|may|mai|jun|jul|aug|ago|sep|set|oct|out|nov|dec|dez)"
    r"[a-z]*\.?"
    r"(?:,?\s+(\d{4}))?",                            # ano (opcional)
    re.IGNORECASE,
)


def _last_day_of_month(year, month):
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def parse_deadline_dates(text, today=None):
    """
    Devolve a lista de datas (date) encontradas no texto do prazo, pela
    ordem em que aparecem. Datas sem ano herdam o ano da data seguinte
    que o tenha ("5 Jan/31 Mar 2027" -> 5 Jan 2027 e 31 Mar 2027).
    Datas só com mês ("Dec 2026") contam como o último dia desse mês.
    """
    today = today or date.today()
    if not text:
        return []

    tokens = []
    for m in _DATE_TOKEN.finditer(text):
        day = int(m.group(1)) if m.group(1) else None
        month = MONTHS[m.group(2).lower()[:3]]
        year = int(m.group(3)) if m.group(3) else None
        tokens.append([day, month, year, year is not None])

    if not tokens:
        return []

    # Propagar o ano da direita para a esquerda, e depois da esquerda
    # para a direita (para casos como "Dec 2026/Jan").
    next_year = None
    for tok in reversed(tokens):
        if tok[2] is not None:
            next_year = tok[2]
        elif next_year is not None:
            tok[2] = next_year
    prev_year = None
    for tok in tokens:
        if tok[2] is not None:
            prev_year = tok[2]
        elif prev_year is not None:
            tok[2] = prev_year
            tok.append("from_left")

    dates = []
    explicit = []
    from_left = []
    for tok in tokens:
        day, month, year, had_year = tok[:4]
        if year is None:
            # Nenhum ano no texto: assume a próxima ocorrência desse mês.
            year = today.year
            probe = date(year, month, min(day or _last_day_of_month(year, month), _last_day_of_month(year, month)))
            if probe < today:
                year += 1
        last = _last_day_of_month(year, month)
        d = min(day, last) if day else last
        try:
            dates.append(date(year, month, d))
            explicit.append(had_year)
            from_left.append(len(tok) > 4)
        except ValueError:
            continue

    # Corrige casos como "Dec/Jan 2027" lidos como Dez 2027 -> Jan 2027:
    # se uma data SEM ano escrito ficou depois da seguinte, recua-a um ano.
    for i in range(len(dates) - 1):
        if not explicit[i] and dates[i] > dates[i + 1]:
            try:
                dates[i] = dates[i].replace(year=dates[i].year - 1)
            except ValueError:
                pass

    # E o inverso: "10 Nov 2026/30 Jan" -> o ano 2026 veio da esquerda,
    # mas 30 Jan tem de ser do ano seguinte.
    for i in range(1, len(dates)):
        if from_left[i] and dates[i] < dates[i - 1]:
            try:
                dates[i] = dates[i].replace(year=dates[i].year + 1)
            except ValueError:
                pass

    return dates


def next_deadline(text, today=None):
    """
    Devolve (proxima_data_ou_None, estado):
      - (date, "open")     : há pelo menos uma data futura (ou hoje)
      - (None, "expired")  : há datas e todas já passaram
      - (None, "unknown")  : nenhuma data reconhecível no texto
    """
    today = today or date.today()
    dates = parse_deadline_dates(text, today)
    if not dates:
        return None, "unknown"
    upcoming = sorted(d for d in dates if d >= today)
    if upcoming:
        return upcoming[0], "open"
    return None, "expired"


# =========================================================================
# NÍVEL E PAÍS (em português)
# =========================================================================

LEVEL_RULES = [
    (r"\bassociate\b", "Curso técnico superior"),
    (r"\b(bachelors?|undergraduate|bsc|ba)\b", "Licenciatura"),
    (r"\bmba\b", "MBA"),
    (r"\b(master|masters|msc|ma|llm|postgraduate|graduate)\b", "Mestrado"),
    (r"\b(phd|dphil|doctoral|doctorate)\b", "Doutoramento"),
    (r"\b(postdoc|postdoctoral|fellowship|research)\b", "Investigação"),
    (r"\b(short course|training|diploma|certificate)\b", "Curso curto / formação"),
]

COUNTRIES_PT = {
    "uk": "Reino Unido", "united kingdom": "Reino Unido", "england": "Reino Unido",
    "scotland": "Reino Unido", "usa": "EUA", "united states": "EUA", "us": "EUA",
    "canada": "Canadá", "australia": "Austrália", "new zealand": "Nova Zelândia",
    "germany": "Alemanha", "france": "França", "italy": "Itália", "spain": "Espanha",
    "portugal": "Portugal", "netherlands": "Países Baixos", "belgium": "Bélgica",
    "switzerland": "Suíça", "sweden": "Suécia", "norway": "Noruega",
    "denmark": "Dinamarca", "finland": "Finlândia", "ireland": "Irlanda",
    "austria": "Áustria", "hungary": "Hungria", "poland": "Polónia",
    "czech republic": "República Checa", "japan": "Japão", "china": "China",
    "korea": "Coreia do Sul", "south korea": "Coreia do Sul", "taiwan": "Taiwan",
    "singapore": "Singapura", "india": "Índia", "malaysia": "Malásia",
    "thailand": "Tailândia", "turkey": "Turquia", "türkiye": "Turquia",
    "south africa": "África do Sul", "kenya": "Quénia", "ghana": "Gana",
    "rwanda": "Ruanda", "egypt": "Egipto", "morocco": "Marrocos",
    "brazil": "Brasil", "lebanon": "Líbano", "costa rica": "Costa Rica", "europe": "Europa", "africa": "África",
    "any country (online)": "Online", "any country": "Vários países",
    "online": "Online", "various countries": "Vários países",
}


def extract_levels(facts):
    text = (facts or "").lower()
    levels = []
    for pattern, label in LEVEL_RULES:
        if re.search(pattern, text) and label not in levels:
            levels.append(label)
    return levels


def extract_country(facts):
    """'Masters Degree. Study in UK. Course starts ...' -> 'Reino Unido'."""
    m = re.search(r"study (?:in|at)\s+([^.]+)", facts or "", re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).strip(" *")
    key = raw.lower()
    if key in COUNTRIES_PT:
        return COUNTRIES_PT[key]
    # "Kyoto, Japan" / "London, UK": cidade + país -> fica só o país
    if "," in raw:
        last = raw.rsplit(",", 1)[1].strip().lower()
        if last in COUNTRIES_PT and raw.split(",")[0].strip().lower() not in COUNTRIES_PT:
            return COUNTRIES_PT[last]
    # Vários países: "UK/USA", "Germany or France"
    parts = [p.strip() for p in re.split(r"/|,| or | and ", raw) if p.strip()]
    if len(parts) > 1:
        return ", ".join(COUNTRIES_PT.get(p.lower(), p) for p in parts)
    return raw


# =========================================================================
# LEITURA DA PÁGINA
# =========================================================================

def _text(node, selector):
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else ""


def parse_listing(html, for_africans):
    """
    Lê uma página de listagem e devolve as bolsas encontradas. Lê só os
    blocos de bolsa (article.row-scholarship); anúncios patrocinados
    (row-ad), menus e listas temáticas ficam de fora por estrutura, não
    por lista de palavras.

    Se o site mudar as classes CSS, há uma segunda via: qualquer <article>
    com um título-ligação e um texto de prazo ("Deadline").
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("article.row-scholarship")

    if not rows:
        rows = [
            a for a in soup.find_all("article")
            if "row-ad" not in (a.get("class") or [])
            and a.find(["h2", "h3"])
            and re.search(r"deadline", a.get_text(" ", strip=True), re.IGNORECASE)
        ]

    items = []
    for row in rows:
        title_tag = row.select_one(".row-title a") or row.select_one("h2 a, h3 a")
        if not title_tag or not title_tag.get("href"):
            continue

        title = title_tag.get_text(" ", strip=True)
        url = title_tag["href"].split("#")[0]

        deadline_text = _text(row, ".row-deadline")
        if not deadline_text:
            m = re.search(r"deadline\s*:?\s*(.+?)(?:last updated|$)", row.get_text(" ", strip=True), re.IGNORECASE)
            deadline_text = m.group(1).strip() if m else ""

        facts = _text(row, ".row-facts")
        if not title or len(title) < 8:
            continue

        items.append({
            "title": title,
            "provider": _text(row, ".row-provider") or None,
            "summary": facts or None,
            "deadline_text": deadline_text or None,
            "url": url,
            "for_africans": for_africans,
        })
    return items


def page_url(n):
    return LISTING_URL if n == 1 else f"{LISTING_URL}page/{n}/"


def fetch_all(session=None, max_pages=MAX_PAGES):
    """Devolve (lista_de_bolsas, numero_de_paginas_lidas_com_sucesso)."""
    session = session or requests.Session()
    found = {}
    ok_pages = 0

    for n in range(1, max_pages + 1):
        url = page_url(n)
        if n > 1:
            time.sleep(PAUSE_BETWEEN_PAGES)
        try:
            resp = session.get(url, headers=HEADERS, timeout=25)
            if resp.status_code == 404:
                break  # fim da lista
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ❌ página {n}: {type(e).__name__}")
            if n == 1:
                break  # a fonte não responde; não vale a pena insistir
            continue

        ok_pages += 1
        items = parse_listing(resp.text, True)
        print(f"  ✅ página {n}: {len(items)} bolsas")
        if not items:
            break

        for item in items:
            found.setdefault(item["url"], item)

    return list(found.values()), ok_pages


# =========================================================================
# HISTÓRICO, EXPIRAÇÃO E EXPORTAÇÃO
# =========================================================================

def make_id(url):
    return "bolsa_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def load_previous(path=OUTPUT_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("bolsas", []) if isinstance(data, dict) else data
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def enrich(item, today):
    deadline, status = next_deadline(item.get("deadline_text"), today)
    item["deadline"] = deadline.isoformat() if deadline else None
    item["deadline_status"] = status
    item["days_left"] = (deadline - today).days if deadline else None
    item["levels"] = extract_levels(item.get("summary"))
    item["country"] = extract_country(item.get("summary"))
    return item


def merge(previous, fresh, now, today, max_days_unseen=MAX_DAYS_UNSEEN):
    """
    Junta as bolsas desta execução com as do ficheiro anterior:
      - mantém first_seen_at da primeira vez que a bolsa apareceu
      - actualiza last_seen_at das que voltaram a aparecer
      - mantém as que não apareceram agora, desde que o prazo não tenha
        passado e não estejam "desaparecidas" há mais de max_days_unseen
      - retira todas as que têm o prazo expirado
    Devolve (lista_final, numero_de_expiradas_ou_desaparecidas).
    """
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    by_url = {b["url"]: b for b in previous if b.get("url")}
    result = {}

    for item in fresh:
        old = by_url.get(item["url"], {})
        item["id"] = old.get("id") or make_id(item["url"])
        item["source"] = SOURCE_NAME
        item["first_seen_at"] = old.get("first_seen_at") or now_iso
        item["last_seen_at"] = now_iso
        result[item["url"]] = enrich(item, today)

    removed = 0
    for url, old in by_url.items():
        if url in result:
            continue
        last_seen = old.get("last_seen_at") or old.get("first_seen_at")
        try:
            seen_day = datetime.strptime(last_seen, "%Y-%m-%dT%H:%M:%SZ").date()
        except (TypeError, ValueError):
            seen_day = today
        if (today - seen_day).days > max_days_unseen:
            removed += 1
            continue
        result[url] = enrich(dict(old), today)

    final = []
    for item in result.values():
        if item["deadline_status"] == "expired":
            removed += 1
            continue
        final.append(item)

    # Prazo mais próximo primeiro; sem data no fim.
    final.sort(key=lambda b: (b["deadline"] is None, b["deadline"] or "", b["title"]))
    return final, removed


FIELD_ORDER = [
    "id", "title", "provider", "country", "levels", "summary",
    "deadline", "days_left", "deadline_text", "deadline_status",
    "for_africans", "url", "source", "first_seen_at", "last_seen_at",
]


def export(bolsas, now, path=OUTPUT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(bolsas),
        "bolsas": [{k: b.get(k) for k in FIELD_ORDER} for b in bolsas],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    now = datetime.now(timezone.utc)
    today = now.date()

    print("=" * 60)
    print("BOLSAS DE ESTUDO - recolha")
    print("=" * 60)

    previous = load_previous()
    print(f"📚 Bolsas no ficheiro anterior: {len(previous)}")

    fresh, ok_pages = fetch_all()

    if ok_pages == 0:
        print("\n⚠️ Nenhuma página da fonte respondeu. Mantém-se a lista anterior "
              "(só se retiram as bolsas com prazo já expirado).")

    final, removed = merge(previous, fresh, now, today)
    export(final, now)

    novas = sum(1 for b in final if b["first_seen_at"] == b["last_seen_at"] == now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    com_prazo = sum(1 for b in final if b["deadline"])
    print("\n" + "-" * 60)
    print(f"  Bolsas lidas nesta execução : {len(fresh)}")
    print(f"  Novas                       : {novas}")
    print(f"  Retiradas (prazo/ausência)  : {removed}")
    print(f"  Publicadas em {OUTPUT_PATH}  : {len(final)} ({com_prazo} com data de prazo)")
    print("-" * 60)

    # Código de saída 0 mesmo sem páginas: o ficheiro anterior foi
    # preservado e não queremos marcar o workflow inteiro como falhado.
    return 0


if __name__ == "__main__":
    sys.exit(main())
