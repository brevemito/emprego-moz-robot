def score_job(job):
    score = 0

    title = (job.get("title") or "").lower()
    source = (job.get("source") or "").lower()
    url = (job.get("url") or "").lower()

    # =========================
    # BASE QUALITY
    # =========================
    if len(title) > 30:
        score += 20
    elif len(title) > 15:
        score += 10

    # =========================
    # KEYWORD QUALITY BOOST
    # =========================
    keywords_high_value = [
        "engenheiro",
        "developer",
        "it",
        "gestor",
        "formador",
        "eletricista",
        "manager",
        "analista",
        "financeiro",
        "procurement",
        "electric",
        "tecnico"
    ]

    if any(k in title for k in keywords_high_value):
        score += 25

    # =========================
    # SITE QUALITY (IMPORTANTE)
    # =========================
    trusted_sources = [
        "totalenergies",
        "vodacom",
        "bci",
        "millennium",
        "unjobs",
        "reliefweb"
    ]

    if any(s in source for s in trusted_sources):
        score += 30

    # =========================
    # PENALIZAÇÕES
    # =========================
    bad_keywords = [
        "cookie",
        "política",
        "privacidade",
        "subscribe",
        "login",
        "register",
        "faq"
    ]

    if any(b in title for b in bad_keywords):
        score -= 100

    if len(title) < 10:
        score -= 50

    # =========================
    # URL QUALITY
    # =========================
    if "http" in url:
        score += 5

    return score
