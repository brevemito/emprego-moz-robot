# =========================================================================
# Páginas do site geradas pelo robô
# =========================================================================
#
# Depois de exportar data/jobs.json, este módulo gera em docs/:
#
#   docs/vagas/<job_id>.html  -> uma página por vaga, com pré-visualização
#                                própria no WhatsApp/Facebook e, quando há
#                                dados suficientes, os dados estruturados
#                                JobPosting que o Google usa no Google for Jobs
#   docs/sitemap.xml          -> lista de todas as páginas, para o Google
#   docs/canal.html           -> texto pronto a colar no canal do WhatsApp,
#                                com as melhores vagas novas para o público
#
# As páginas de vagas que já não existem são apagadas em cada execução.
# =========================================================================

import html
import json
import os
import re
from datetime import datetime, timezone, timedelta

SITE = "https://brevemito.github.io/emprego-moz-robot/"
DOCS = "docs"
PAGES_DIR = os.path.join(DOCS, "vagas")
CHANNEL_URL = "https://whatsapp.com/channel/0029VbD9lut2Jl88G0igIL0O"
OG_IMAGE = SITE + "icon-512.png"
# GoatCounter: o mesmo código usado no index.html (ver instruções).
GOATCOUNTER = "https://brevemito.goatcounter.com/count"

GENERIC = {"", "desconhecida", "mocambique", "moçambique"}


def _e(text):
    return html.escape(text or "", quote=True)


def _safe_id(job_id):
    return re.sub(r"[^A-Za-z0-9_-]", "_", job_id or "")


def page_path(job):
    return "vagas/" + _safe_id(job.get("job_id")) + ".html"


def _date(iso):
    if not iso:
        return None
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _paragraphs(text):
    parts = [p.strip() for p in re.split(r"\n\s*\n|\n", text or "") if p.strip()]
    return "".join("<p>" + _e(p) + "</p>" for p in parts)


def _job_posting(job):
    """Dados estruturados JobPosting - só quando a vaga tem o essencial."""
    desc = (job.get("description") or "").strip()
    company = (job.get("company") or "").strip()
    posted = _date(job.get("first_seen_at"))
    if len(desc) < 100 or company.lower() in GENERIC or not posted:
        return ""
    locality = (job.get("locations") or [job.get("location") or "Moçambique"])[0]
    data = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": job.get("title"),
        "description": _paragraphs(desc),
        "datePosted": posted.isoformat(),
        # Sem prazo conhecido: o Google pede validThrough quando existe;
        # usamos 30 dias depois da 1.ª vez que a vaga foi vista.
        "validThrough": (posted + timedelta(days=30)).isoformat() + "T23:59",
        "hiringOrganization": {"@type": "Organization", "name": company},
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": locality if locality.lower() not in GENERIC else "Maputo",
                "addressCountry": "MZ",
            },
        },
        "directApply": False,
        "url": SITE + page_path(job),
    }
    if job.get("job_id"):
        data["identifier"] = {"@type": "PropertyValue", "name": "Brevemito", "value": job["job_id"]}
    raw = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/ld+json">' + raw + "</script>"


PAGE_CSS = """
:root{--ink:#34383B;--paper:#F6EEDD;--rust:#C4501E;--card:#fff;--mu:#5f6366}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 Inter,Arial,sans-serif}
header{background:var(--ink);color:#fff;padding:12px 16px}header a{color:#fff;text-decoration:none;font-weight:700}
main{max-width:760px;margin:0 auto;padding:16px}
.card{background:var(--card);border-radius:12px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin:14px 0}
h1{font-size:1.45em;line-height:1.25;margin:.2em 0 .4em}
.meta{color:var(--mu);font-size:.95em}.tags span{display:inline-block;background:var(--ink);color:#fff;border-radius:20px;padding:2px 10px;margin:6px 6px 0 0;font-size:.82em}
.btn{display:inline-block;text-decoration:none;border-radius:8px;padding:11px 16px;margin:6px 8px 6px 0;font-weight:600;color:#fff}
.apply{background:var(--rust)}.wa{background:#25D366}.fb{background:#1877F2}.back{background:var(--ink)}
.warn{background:#fff4e5;border-left:4px solid #e08a00;padding:10px 14px;border-radius:6px;font-size:.92em}
.desc p{margin:.5em 0}footer{max-width:760px;margin:0 auto;padding:16px;color:var(--mu);font-size:.85em}
"""


def _page(job):
    title = job.get("title") or "Vaga"
    company = job.get("company") or ""
    location = job.get("location") or "Moçambique"
    url = SITE + page_path(job)
    head_title = f"{title} — {company} ({location}) | Vagas Brevemito"
    desc_meta = (job.get("description") or "").strip().replace("\n", " ")
    desc_meta = (desc_meta[:155] + "…") if len(desc_meta) > 156 else desc_meta
    if not desc_meta:
        desc_meta = f"Vaga de {title} em {location}, {company}. Veja os detalhes e candidate-se no site oficial."
    tags = [t for t in (job.get("level_label"), job.get("category")) if t]
    posted = _date(job.get("first_seen_at"))
    share_txt = f"Vaga: {title}" + (f" — {company}" if company else "") + f" ({location})\n{url}"
    body_desc = _paragraphs(job.get("description")) or (
        "<p>A fonte não publica a descrição completa. Abra o anúncio original para ver os requisitos e o prazo.</p>"
    )
    return f"""<!DOCTYPE html>
<html lang="pt-MZ">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(head_title)}</title>
<meta name="description" content="{_e(desc_meta)}">
<link rel="canonical" href="{_e(url)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Brevemito">
<meta property="og:locale" content="pt_MZ">
<meta property="og:title" content="{_e(title + (' — ' + company if company else ''))}">
<meta property="og:description" content="{_e(location + ' · ' + desc_meta)}">
<meta property="og:url" content="{_e(url)}">
<meta property="og:image" content="{_e(OG_IMAGE)}">
<meta name="theme-color" content="#34383B">
<link rel="manifest" href="../manifest.webmanifest">
<link rel="icon" type="image/png" href="../icon-192.png">
<style>{PAGE_CSS}</style>
{_job_posting(job)}
</head>
<body>
<header><a href="../">← Brevemito · Vagas e Bolsas</a></header>
<main>
  <article class="card">
    <h1>{_e(title)}</h1>
    <p class="meta">{_e(company)}{' · ' if company else ''}{_e(location)}{(' · Publicada em ' + posted.strftime('%d/%m/%Y')) if posted else ''}</p>
    <p class="tags">{''.join('<span>' + _e(t) + '</span>' for t in tags)}</p>
    <div class="desc">{body_desc}</div>
    <p><a class="btn apply" href="{_e(job.get('url') or '#')}" target="_blank" rel="noopener" data-gc="candidatar">Candidatar no site oficial</a></p>
    <p class="warn">⚠️ Nenhuma vaga verdadeira pede dinheiro para a candidatura. Confirme sempre os detalhes e o prazo no anúncio original.</p>
  </article>
  <div class="card">
    <p><b>Partilhe com quem precisa:</b></p>
    <a class="btn wa" href="https://wa.me/?text={_e(_urlq(share_txt))}" target="_blank" rel="noopener" data-gc="partilhar-whatsapp">WhatsApp</a>
    <a class="btn fb" href="https://www.facebook.com/sharer/sharer.php?u={_e(_urlq(url))}" target="_blank" rel="noopener" data-gc="partilhar-facebook">Facebook</a>
    <a class="btn back" href="../#vagas">Ver todas as vagas</a>
    <p class="meta">Receba as novas vagas no <a href="{CHANNEL_URL}" target="_blank" rel="noopener">canal Brevemito no WhatsApp</a>.</p>
  </div>
</main>
<footer>As oportunidades são recolhidas automaticamente de fontes públicas. © Brevemito</footer>
<script>document.addEventListener("click",function(e){{var a=e.target.closest&&e.target.closest("[data-gc]");if(a&&window.goatcounter&&window.goatcounter.count)window.goatcounter.count({{path:"evento-"+a.dataset.gc,title:document.title,event:true}})}});</script>
<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


def _urlq(text):
    from urllib.parse import quote
    return quote(text, safe="")


def _sitemap(jobs):
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [f"<url><loc>{SITE}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>"]
    for job in jobs:
        last = (job.get("last_seen_at") or job.get("first_seen_at") or today)[:10]
        urls.append(f"<url><loc>{_e(SITE + page_path(job))}</loc><lastmod>{last}</lastmod></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")


NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def channel_text(jobs, limit=8):
    """Texto do dia para o canal do WhatsApp: vagas recentes, público principal primeiro."""
    pool = [j for j in jobs if j.get("audience") != "internacional"]
    for days in (3, 7, 30, 9999):
        fresh = [j for j in pool if (j.get("days_since_first_seen") or 0) <= days]
        if len(fresh) >= limit:
            break
    fresh.sort(key=lambda j: (j.get("audience") != "jovens", j.get("days_since_first_seen") or 0, -(j.get("rank") or 0)))
    # A mesma vaga em várias cidades aparece uma só vez.
    picked, seen = [], {}
    for j in fresh:
        key = re.sub(r"[^a-z]+", " ", re.sub(r"\(.*?\)|\d+\s*vagas?", " ", (j.get("title") or "").lower())).strip()
        if key in seen:
            seen[key]["_mais"] = seen[key].get("_mais", 0) + 1
            continue
        seen[key] = j
        picked.append(j)
        if len(picked) == limit:
            break
    today = datetime.now(timezone(timedelta(hours=2))).strftime("%d/%m/%Y")
    lines = [f"🔔 *Vagas de hoje — {today}*", "Para jovens moçambicanos: 12.ª classe, técnicos e recém-formados", ""]
    for n, j in enumerate(picked):
        where = j.get("location") or "Moçambique"
        if j.get("_mais"):
            where += f" e mais {j['_mais']} local(is)"
        who = f" — {j['company']}" if j.get("company") and j["company"].lower() not in GENERIC else ""
        lines.append(f"{NUMBERS[n]} *{j.get('title')}*{who} ({where})")
        lines.append(f"👉 {SITE + page_path(j)}")
        lines.append("")
        j.pop("_mais", None)
    lines.append(f"📋 Mais vagas e bolsas de estudo: {SITE}")
    lines.append("⚠️ Nenhuma vaga verdadeira pede dinheiro para a candidatura.")
    return "\n".join(lines)


def _channel_page(text):
    return f"""<!DOCTYPE html>
<html lang="pt-MZ"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Texto do canal — Brevemito</title><meta name="robots" content="noindex">
<style>{PAGE_CSS} textarea{{width:100%;height:60vh;font:15px/1.5 monospace;border-radius:8px;padding:10px}}</style></head>
<body><header><a href="./">← Brevemito</a></header><main>
<h1>Texto de hoje para o canal do WhatsApp</h1>
<p class="meta">Gerado automaticamente com as melhores vagas novas para o público principal. Copie, reveja e publique no canal.</p>
<p><button class="btn apply" id="cp" style="border:0;cursor:pointer">Copiar texto</button> <a class="btn wa" href="{CHANNEL_URL}" target="_blank" rel="noopener">Abrir o canal</a></p>
<textarea id="t" readonly>{_e(text)}</textarea>
</main>
<script>document.getElementById("cp").onclick=function(){{var t=document.getElementById("t"),b=this;try{{navigator.clipboard.writeText(t.value).then(function(){{b.textContent="Copiado ✓"}})}}catch(e){{t.select();document.execCommand("copy");b.textContent="Copiado ✓"}}}};</script>
</body></html>
"""


def generate_site(jobs):
    os.makedirs(PAGES_DIR, exist_ok=True)
    wanted = set()
    for job in jobs:
        name = os.path.basename(page_path(job))
        wanted.add(name)
        with open(os.path.join(PAGES_DIR, name), "w", encoding="utf-8") as f:
            f.write(_page(job))
    removed = 0
    for name in os.listdir(PAGES_DIR):
        if name.endswith(".html") and name not in wanted:
            os.remove(os.path.join(PAGES_DIR, name))
            removed += 1
    with open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(_sitemap(jobs))
    with open(os.path.join(DOCS, "canal.html"), "w", encoding="utf-8") as f:
        f.write(_channel_page(channel_text(jobs)))
    with_ld = sum(1 for j in jobs if _job_posting(j))
    print(f"🌐 {len(jobs)} páginas de vagas geradas ({with_ld} com dados para o Google for Jobs), "
          f"{removed} antigas apagadas; sitemap.xml e canal.html actualizados.")
