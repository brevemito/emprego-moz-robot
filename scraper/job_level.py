# =========================================================================
# Nível pedido e público de cada vaga
# =========================================================================
#
# O público principal do site são jovens moçambicanos: quem tem a 12.ª
# classe, técnicos médios (ensino técnico-profissional) e recém-formados.
# Este módulo lê o título e a descrição de cada vaga e devolve:
#
#   level     -> "basico", "tecnico", "estagio", "licenciatura", "experiente"
#                ou "" quando não há pistas suficientes
#   audience  -> "jovens"        (serve directamente o público principal)
#                "internacional" (ONU, consultorias, normalmente em inglês)
#                "geral"         (todas as outras)
#   lang      -> "en" quando o título está em inglês, senão "pt"
#
# Tal como job_category.py, funciona por EVIDÊNCIA POSITIVA: só atribui
# um nível quando encontra palavras que o indiquem.
# =========================================================================

import re
import unicodedata


LEVEL_LABELS = {
    "basico": "12.ª classe ou menos",
    "tecnico": "Técnico médio",
    "estagio": "Estágio / recém-formado",
    "licenciatura": "Licenciatura",
    "experiente": "Experiente / sénior",
}


def _plain(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


# Requisitos de escolaridade escritos na descrição (têm prioridade).
EDU_BASICO = [
    r"\b1[02] ?(a|ª|o)? ?classe\b", r"\bdecima segunda classe\b", r"\bensino secundario\b",
    r"\bnivel basico\b", r"\bensino basico\b", r"\bsaber ler e escrever\b",
]
EDU_TECNICO = [
    r"\btecnico medio\b", r"\bnivel medio\b", r"\bcurso tecnico\b", r"\bensino tecnico\b",
    r"\bmedio profissional\b", r"\binstituto industrial\b", r"\binstituto comercial\b",
    r"\bcertificado profissional\b", r"\bcv ?[345]\b", r"\bcurso profissional\b",
    r"\bformacao profissional\b", r"\btechnical diploma\b", r"\bvocational\b",
]
EDU_LICENCIATURA = [
    r"\blicenciatura\b", r"\blicenciado\b", r"\bbacharel\b", r"\bbachelor", r"\buniversity degree\b",
    r"\bensino superior\b", r"\bgrau academico\b",
]
EDU_EXPERIENTE = [
    r"\bmestrado\b", r"\bmaster'?s\b", r"\bphd\b", r"\bdoutoramento\b",
    r"\b(minimo|pelo menos|at least|minimum)( de)? (de )?([5-9]|1[0-9]) (anos|years)\b",
    r"\b([5-9]|1[0-9])\+? (anos|years) (de )?(experiencia|experience)\b",
]

# Pistas no título do cargo.
TITLE_ESTAGIO = [
    r"\bestagi", r"\bestagio\b", r"\bintern(ship)?\b", r"\btrainee\b", r"\brecem[ -](licenciad|formad|graduad)",
    r"\bgraduate (programme|program|trainee)\b", r"\bprimeiro emprego\b", r"\bjunior\b",
    r"\bearly careers?\b", r"\bgraduate\b",
]
TITLE_LICENCIATURA = [
    r"\bengenheir", r"\bengineer\b", r"\beconomista\b", r"\bcontabilista\b", r"\baccountant\b",
    r"\badvogad", r"\bjurista\b", r"\barquitect", r"\banalista\b", r"\banalyst\b", r"\bauditor\b",
    r"\bpsicolog", r"\bmedico\b", r"\bfarmaceutic", r"\bgeolog", r"\bgeophysic",
]
TITLE_EXPERIENTE = [
    r"\bsenior\b", r"\bchefe\b", r"\bdirector\b", r"\bdiretor\b", r"\bhead of\b", r"\bmanager\b",
    r"\bgestor\b", r"\bgerente\b", r"\bcoordenador", r"\bcoordinator\b", r"\blead\b", r"\bprincipal\b",
    r"\bsuperintendent", r"\bspecialist\b", r"\bespecialista\b", r"\badvisor\b", r"\bassessor\b",
    r"\bconsultor\b", r"\bconsultant\b", r"\bofficer\b",
]
TITLE_TECNICO = [
    r"\btecnic", r"\btechnician\b", r"\belectricista\b", r"\beletricista\b", r"\belectrician\b",
    r"\bmecanico\b", r"\bmechanic\b", r"\bserralheiro\b", r"\bsoldador\b", r"\bwelder\b",
    r"\bcanalizador\b", r"\bplumber\b", r"\bcarpinteiro\b", r"\bpedreiro\b", r"\binstalador\b",
    r"\bformador", r"\binstrutor", r"\bprofessor", r"\bdocente\b", r"\benfermeir", r"\bfiel de armazem\b",
    r"\boperador de (maquina|equipamento|grua|empilhador)", r"\brefrigeracao\b", r"\bfrio\b",
]
TITLE_BASICO = [
    r"\bmotorista\b", r"\bdriver\b", r"\bdigitador", r"\bguarda\b", r"\bagente de seguranca\b", r"\bseguranca patrimonial\b", r"\bajudante\b",
    r"\bauxiliar\b", r"\bservente\b", r"\bcozinheir", r"\bempregad", r"\bjardineir", r"\blimpeza\b",
    r"\bcleaner\b", r"\bcaixa\b", r"\brecepcionista\b", r"\bpromotor", r"\bvendedor", r"\bestafeta\b",
    r"\boperador\b", r"\bcarregador\b", r"\bmensageiro\b",
]

# Áreas que o público procura muito: professor, formador, electricista.
TARGET_TITLES = [
    r"\belectricista\b", r"\beletricista\b", r"\belectrician\b", r"\belectrotecn", r"\beletrotecn",
    r"\bformador", r"\bformadora\b", r"\bprofessor", r"\bdocente\b", r"\binstrutor",
]

INTERNATIONAL_SOURCES = {"unjobs", "reliefweb", "un_mozambique"}

ENGLISH_WORDS = {
    "officer", "manager", "engineer", "assistant", "specialist", "coordinator", "analyst", "senior",
    "advisor", "consultant", "director", "head", "lead", "programme", "program", "development",
    "support", "management", "operations", "technician", "driver", "supervisor", "associate",
    "intern", "internship", "and", "of", "for", "the", "project",
}
PORTUGUESE_HINTS = {"de", "da", "do", "das", "dos", "e", "para", "tecnico", "gestor", "assistente", "vaga", "vagas"}


def detect_lang(title):
    words = re.findall(r"[a-z]+", _plain(title))
    if not words:
        return "pt"
    en = sum(1 for w in words if w in ENGLISH_WORDS)
    pt = sum(1 for w in words if w in PORTUGUESE_HINTS)
    return "en" if en > pt and en >= 1 else "pt"


def detect_level(title, description=""):
    t = _plain(title)
    d = _plain(description)
    # 1) Estágio no título manda sempre.
    if _any(TITLE_ESTAGIO, t):
        return "estagio"
    # 2) Requisitos de escolaridade escritos na descrição.
    if d:
        if _any(EDU_EXPERIENTE, d):
            return "experiente"
        if _any(EDU_BASICO, d) and not _any(EDU_LICENCIATURA, d):
            return "basico"
        if _any(EDU_TECNICO, d) and not _any(EDU_LICENCIATURA, d):
            return "tecnico"
    # 3) Pistas no título do cargo.
    if _any(TITLE_EXPERIENTE, t):
        return "experiente"
    if _any(TITLE_LICENCIATURA, t):
        return "licenciatura"
    if _any(TITLE_TECNICO, t):
        return "tecnico"
    if _any(TITLE_BASICO, t):
        return "basico"
    if d and _any(EDU_LICENCIATURA, d):
        return "licenciatura"
    return ""


def classify(job, category=""):
    """Devolve (level, audience, lang) para uma vaga (dicionário)."""
    title = job.get("title") or ""
    description = job.get("description") or ""
    source = (job.get("source") or "").lower()
    level = detect_level(title, description)
    lang = detect_lang(title)

    if source in INTERNATIONAL_SOURCES or category == "Consultoria e Organizações Internacionais":
        audience = "internacional"
    elif (
        level in ("basico", "tecnico", "estagio")
        or category in ("Educação e Formação", "Electricidade e Energia", "Estágios")
        or _any(TARGET_TITLES, _plain(title))
    ):
        audience = "jovens"
    else:
        audience = "geral"
    return level, audience, lang


def rank(job, base_score):
    """Ordem de relevância: o público principal primeiro, a ONU no fim."""
    bonus = {"jovens": 40, "geral": 0, "internacional": -30}.get(job.get("audience"), 0)
    return (base_score or 0) + bonus
