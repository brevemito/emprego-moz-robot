# Sistema de pontuação de vagas
def score_job(job):
    """
    Atribui uma pontuação de relevância à vaga.
    Quanto maior o score, mais relevante para o teu perfil.
    """

    text = (job["title"] + " " + job.get("description", "")).lower()

    score = 0

    # ===== ÁREAS PRINCIPAIS =====
    if "engenheiro" in text or "engineering" in text:
        score += 25

    if "elétr" in text or "electric" in text:
        score += 25

    if "solar" in text or "energia" in text or "renewable" in text:
        score += 20

    if "manutenção" in text or "maintenance" in text:
        score += 18

    if "técnico" in text or "docente" in text:
        score += 15

    if "formador" in text or "professor" in text:
        score += 10

    # ===== SETORES ESTRATÉGICOS =====
    if "energia" in text:
        score += 10

    if "indústria" in text or "industrial" in text:
        score += 10

    if "construção" in text or "construction" in text:
        score += 8

    return score
