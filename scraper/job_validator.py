# =========================================================================
# JobValidator — validação ESTRUTURAL de candidatos a vaga
# =========================================================================
#
# Este módulo substitui a abordagem antiga de "lista negra de palavras".
# Em vez de tentar adivinhar todas as frases institucionais possíveis,
# o validador exige EVIDÊNCIA POSITIVA de que um item é realmente uma
# vaga de emprego (JOB_VALIDITY_SCORE), e só depois disso é que a
# pontuação de relevância para Moçambique/Brevemito entra em jogo
# (JOB_RELEVANCE_SCORE, calculada em scoring.py).
#
# Separação clara de responsabilidades:
#
#   JOB_VALIDITY_SCORE  (aqui)      -> "Isto é mesmo uma vaga?"
#   JOB_RELEVANCE_SCORE (scoring.py) -> "Esta vaga é relevante/boa?"
#
# Um item só chega ao score de relevância depois de passar na validação
# estrutural. Um domínio de confiança (ex.: millenniumbim.co.mz) NUNCA
# é suficiente, por si só, para tornar uma página institucional válida.
#
# Motivos de rejeição possíveis (guardados para reporting/depuração):
#   - insufficient_job_evidence : não há evidência suficiente (nem
#                                  palavra de cargo, nem URL de vaga)
#   - navigation                : artefacto de template / aviso técnico
#                                  (JS não activo, {{ }}, v-, ng-, etc.)
#   - procurement                : concurso público / RFP / RFQ / tender
#   - institutional_page         : página institucional, relatório,
#                                  produto bancário, política, etc.
#   - search_filter               : chip de filtro / menu lateral
#                                  (ex.: "Duty Stations", "Closing Soon")
#   - location_filter             : filtro de localização com contador
#                                  (ex.: "Maputo, Mozambique 36")
#   - category                    : categoria/área profissional genérica
#                                  (ex.: "Comunicação e Marketing")
#   - organization                : nome/sigla de organização, sem cargo
#                                  associado (ex.: "UNICEF: ...")
#
# =========================================================================

import re


# =========================================================================
# EVIDÊNCIA POSITIVA — palavras que indicam um cargo/oportunidade real
# =========================================================================
# IMPORTANTE: esta lista NUNCA é usada para rejeitar um título. É usada
# apenas para ATRIBUIR PONTOS a favor da validade de um item. Um título
# como "Procurement Officer" ou "Tender Manager" GANHA pontos aqui, e
# nunca é penalizado só por conter "procurement" ou "tender" - o que é
# rejeitado é a FRASE composta de um anúncio de concurso (ver secção de
# procurement mais abaixo), nunca o nome de um cargo.
JOB_ROLE_KEYWORDS = [
    # --- Português ---
    "gestor", "gestora", "gerente", "técnico", "tecnico", "técnica",
    "engenheiro", "engenheira", "assistente", "coordenador", "coordenadora",
    "director", "diretor", "directora", "diretora", "analista", "consultor",
    "consultora", "motorista", "estagiário", "estagiario", "estagiária",
    "estagiaria", "estágio", "estagio", "chefe", "supervisor", "supervisora", "agente", "oficial",
    "contabilista", "auditor", "auditora", "secretário", "secretario",
    "secretária", "secretaria", "recepcionista", "enfermeiro", "enfermeira",
    "professor", "professora", "formador", "formadora", "electricista",
    "eletricista", "mecânico", "mecanico", "soldador", "pedreiro",
    "carpinteiro", "cozinheiro", "cozinheira",
    "guarda", "vendedor", "vendedora", "caixa", "operador", "operadora",
    "especialista", "representante", "administrador", "administradora",
    "jurista", "advogado", "advogada", "médico", "medico", "médica",
    "farmacêutico", "farmaceutico", "nutricionista", "psicólogo",
    "psicologo", "arquitecto", "arquiteto", "topógrafo", "topografo",
    "inspector", "inspetor", "fiscal", "comprador", "compradora",
    "logístico", "logistico", "armazenista", "condutor", "piloto",
    "empregado", "empregada", "estivador", "sinaleiro", "recrutador",
    "recrutadora", "programador", "programadora", "desenvolvedor",
    "desenvolvedora", "instrutor", "instrutora", "auxiliar", "ajudante",
    "camionista", "cobrador", "cobradora", "receptor", "atendente",
    "digitador", "digitadora", "controlador", "controladora", "banqueiro",
    "orçamentista", "orcamentista", "químico", "quimico", "biólogo",
    "biologo", "geólogo", "geologo", "socorrista", "bombeiro",

    # --- English ---
    "manager", "officer", "engineer", "coordinator", "driver",
    "technician", "consultant", "intern", "internship", "specialist",
    "analyst", "assistant", "supervisor", "representative", "executive",
    "clerk", "accountant", "secretary", "guard", "cleaner", "receptionist",
    "administrator", "director", "auditor", "electrician", "mechanic",
    "welder", "mason", "carpenter", "cook", "chef", "cashier", "operator",
    "nurse", "teacher", "trainer", "lawyer", "doctor", "pharmacist",
    "architect", "surveyor", "inspector", "buyer", "warehouse", "security",
    "developer", "programmer", "recruiter", "instructor", "salesperson",
    "controller", "chemist", "biologist", "geologist", "paramedic",
    "firefighter", "attendant", "storekeeper", "foreman", "planner",
    "advisor", "adviser", "head of", "vice president",
    "consultancy",
]

# Ordenar por comprimento decrescente evita que substrings mais curtas
# (ex.: "chefe") "escondam" correspondências mais longas ao construir a
# regex; na prática usamos \b por palavra, por isso a ordem não é
# estritamente necessária, mas mantém-se por clareza.
#
# IMPORTANTE: o sufixo opcional (?:es|s)? permite apanhar plurais, tanto
# em português ("gestor" -> "gestores", "sinaleiro" -> "sinaleiros") como
# em inglês ("manager" -> "managers", "driver" -> "drivers"). Sem isto,
# QUALQUER vaga anunciada no plural (muito comum: "Motoristas",
# "Estagiários", "Warehouses Coordinator") era incorrectamente rejeitada.
_JOB_ROLE_REGEX = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in sorted(JOB_ROLE_KEYWORDS, key=len, reverse=True)) + r")(?:es|s)?\b",
    re.IGNORECASE
)


def has_job_role_evidence(text):
    """Devolve True se o texto contém pelo menos um cargo/função reconhecível."""
    if not text:
        return False
    return bool(_JOB_ROLE_REGEX.search(text))


# =========================================================================
# EVIDÊNCIA POSITIVA — padrões de URL que indicam página de detalhe de vaga
# =========================================================================
JOB_URL_PATTERNS = [
    r"/vaga/", r"/vagas/", r"/emprego/", r"/empregos/",
    r"/oferta-de-emprego/", r"/ofertas-de-emprego/", r"/oferta/",
    r"/job/", r"/jobs/", r"/job-detail", r"/jobdetail",
    r"/vacanc", r"/vacature", r"/career-detail", r"/careers/.*\d",
    r"/detailoffre", r"[?&]idoffre=", r"[?&]jobid=", r"[?&]job_id=",
    r"/offre-de-emploi/", r"/recrutamento/oferta", r"/position/",
    r"/opportunit", r"/vacancies/\d", r"/duty_stations/.*\d",
    r"/wd\d+\.myworkdayjobs\.com/.*/job/",
]
_JOB_URL_REGEX = re.compile("|".join(JOB_URL_PATTERNS), re.IGNORECASE)


def has_job_url_evidence(url):
    if not url:
        return False
    return bool(_JOB_URL_REGEX.search(url))


# =========================================================================
# PROCUREMENT / RFP / RFQ / TENDER (concursos públicos)
# =========================================================================
PROCUREMENT_PATTERNS = [
    "concurso público para fornecimento",
    "concurso público para aquisição",
    "anúncio de concurso",
    "aviso de concurso",
    "convite à apresentação de propostas",
    "convite a apresentação de propostas",
    "convite para apresentação de propostas",
    "request for proposal",
    "request for proposals",
    "request for quotation",
    "request for quotations",
    "invitation to bid",
    "invitation for bid",
    "invitation for bids",
    "tender notice",
    "tender document",
    "tender for the supply",
    "notice of tender",
    "expression of interest",
    "manifestação de interesse",
    "aquisição de bens e serviços",
    "aquisição de bens",
    "fornecimento de equipamentos",
    "fornecimento de bens",
    "fornecimento de material",
    "fornecimento de materiais",
    "solicitação de cotação",
    "pedido de cotação",
    "solicitação de propostas",
    "consultoria institucional",
    "caderno de encargos",
    "termos de referência para aquisição",
    "termos de referência para contratação de fornecedor",
]

PROCUREMENT_REGEX_PATTERNS = [
    r"concursos?\s*(público)?\s*n[ºo°.]*\s*\d",
    r"\brfp\b",
    r"\brfq\b",
    r"\(rfp\)",
    r"\(rfq\)",
]


def is_procurement_notice(text):
    if not text:
        return False
    if any(pattern in text for pattern in PROCUREMENT_PATTERNS):
        return True
    if any(re.search(pattern, text) for pattern in PROCUREMENT_REGEX_PATTERNS):
        return True
    return False


# =========================================================================
# PÁGINAS INSTITUCIONAIS (produtos bancários, relatórios, políticas, etc.)
# =========================================================================
# Frases específicas conhecidas (curadas a partir de exemplos reais que
# foram reportados como falsos positivos). Servem de rede de segurança
# adicional às regras estruturais abaixo, não como mecanismo principal.
INSTITUTIONAL_PHRASES = [
    "relatório anual",
    "relatório e contas",
    "relatório de sustentabilidade",
    "monitoria de acesso",
    "para a minha instituição",
    "serviços financeiros gratuitos",
    "compromisso de gestão",
    "compromisso de gestão sócio-ambiental",
    "carteira de imóveis",
    "responsabilidade social",
    "acesso às contas",
    "preçário completo",
    "preçário",
    "código de conduta",
    "governo corporativo",
    "estrutura accionista",
    "estrutura acionista",
    "política de privacidade",
    "termos e condições de utilização",
    "mapa do site",
    "quem somos",
    "sobre nós",
    "visão - missão",
    "visão – missão",
    "missão e valores",
    "visão, missão e valores",
    "ative o javascript",
    "active o javascript",
    "enable javascript",
    "javascript is disabled",
    "reactivar cartão",
    "onde estamos",
    "linhas de financiamento",
]

# Frases curtas/ambíguas: só rejeitam se forem o título INTEIRO
# (depois de normalizar espaços, hífens e vírgulas), nunca como
# substring de um título maior.
INSTITUTIONAL_EXACT_PHRASES = [
    "institucional",
    "visão missão valores",
    "visão missão e valores",
    "governo corporativo",
    "estrutura corporativa",
    "quem somos",
    "sobre nós",
]


def matches_institutional_phrase(text):
    if not text:
        return False
    if any(phrase in text for phrase in INSTITUTIONAL_PHRASES):
        return True
    # Frases curtas e ambíguas só rejeitam por correspondência EXACTA ao
    # título inteiro, para não apanhar cargos legítimos que as contenham
    # como parte de uma expressão maior (ex.: "Gestor de Parcerias
    # Institucionais" deve continuar válido).
    normalized = re.sub(r"[\s\-–—,]+", " ", text).strip()
    return normalized in INSTITUTIONAL_EXACT_PHRASES


# =========================================================================
# CHIPS DE FILTRO / MENUS LATERAIS (não são conteúdo, são controlos de UI)
# =========================================================================
FILTER_CHIP_PHRASES = [
    "duty stations",
    "organizations",
    "closing soon",
    "recrutamento e selecção",
    "recrutamento e seleção",
]


def matches_filter_chip(text):
    if not text:
        return False
    # Comparação de frase inteira (não substring) para não rejeitar
    # títulos legítimos que apenas mencionem estas palavras de passagem.
    normalized = text.strip().lower()
    return normalized in FILTER_CHIP_PHRASES


# Padrão estrutural de "categoria": duas expressões nominais unidas por
# "e"/"and", tudo em Title Case, sem dígitos - típico de chips de
# categoria profissional (ex.: "Comunicação e Marketing",
# "Engenharia e Técnica", "Administração e Secretariado").
_CATEGORY_PATTERN = re.compile(
    r"^[A-ZÀ-Ú][\wà-úÀ-Ú]*(\s+[a-zà-ú]+)*\s+(e|and)\s+[A-ZÀ-Ú][\wà-úÀ-Ú]*(\s+[a-zà-úÀ-Ú]+)*$"
)


def matches_category_pattern(text):
    if not text or len(text) > 45:
        return False
    if any(ch.isdigit() for ch in text):
        return False
    return bool(_CATEGORY_PATTERN.match(text.strip()))


# Padrão estrutural de "filtro de localização com contador":
# ex.: "Maputo, Mozambique 36", "Beira 12"
_LOCATION_FILTER_PATTERN = re.compile(
    r"^[A-ZÀ-Ú][\wà-úÀ-Ú]*(,\s*[A-ZÀ-Ú][\wà-úÀ-Ú]*)*\s+\d{1,4}$"
)


def matches_location_filter(text):
    if not text:
        return False
    return bool(_LOCATION_FILTER_PATTERN.match(text.strip()))


# Padrão estrutural de "organização/sigla" sem cargo associado:
# ex.: "UNICEF: United Nations Children's Fund", "OMS: ..."
_ORG_PATTERN = re.compile(r"^[A-Z]{2,10}\s*[:\-]\s+\S")


def matches_organization_pattern(text):
    if not text:
        return False
    if has_job_role_evidence(text):
        return False
    return bool(_ORG_PATTERN.match(text.strip()))


# =========================================================================
# ARTEFACTOS DE TEMPLATE / AVISOS TÉCNICOS
# =========================================================================
def is_template_artifact(text):
    if not text:
        return False
    if "{{" in text or "}}" in text:
        return True
    if text.startswith("v-") or " v-" in text:
        return True
    if "ng-" in text:
        return True
    if "javascript" in text:
        return True
    return False


# =========================================================================
# CLASSIFICAÇÃO ESTRUTURAL PRINCIPAL
# =========================================================================

MIN_TITLE_LENGTH = 8

# Pontuação mínima de validade para um item ser aceite quando nenhuma
# categoria de rejeição "dura" foi accionada.
VALIDITY_THRESHOLD = 40


def compute_validity_score(title, description, url):
    """
    JOB_VALIDITY_SCORE: mede a evidência de que este item é, de facto,
    uma vaga de emprego (não mede qualidade nem relevância, apenas se
    é estruturalmente uma oportunidade de emprego).
    """
    score = 0

    if has_job_role_evidence(title):
        score += 40

    if description and description.strip() != title.strip() and has_job_role_evidence(description):
        score += 15

    if has_job_url_evidence(url):
        score += 30

    if description and description.strip() and description.strip() != title.strip():
        # Descrição própria (não apenas repetição do título) é um sinal
        # adicional, ainda que fraco, de conteúdo estruturado real.
        score += 10

    if MIN_TITLE_LENGTH <= len(title or "") <= 120:
        score += 5

    return min(score, 100)


def classify(title, description=None, url=None):
    """
    Classifica um candidato a vaga.

    Devolve um dicionário:
        {
            "is_valid": bool,
            "reason": str | None,   # motivo de rejeição, ou None se válido
            "validity_score": int   # JOB_VALIDITY_SCORE (0-100)
        }
    """
    title = (title or "").strip()
    description = (description or "").strip()
    url = (url or "").strip()

    title_lower = title.lower()
    description_lower = description.lower()
    combined_lower = f"{title_lower} {description_lower}".strip()

    # ---- 1. Sanidade básica ----
    if len(title) < MIN_TITLE_LENGTH:
        return {"is_valid": False, "reason": "insufficient_job_evidence", "validity_score": 0}

    # ---- 2. Artefactos de template / avisos técnicos ----
    if is_template_artifact(title_lower) or is_template_artifact(description_lower):
        return {"is_valid": False, "reason": "navigation", "validity_score": 0}

    # ---- 3. Concursos públicos / RFP / RFQ / tender ----
    if is_procurement_notice(title_lower) or is_procurement_notice(description_lower):
        return {"is_valid": False, "reason": "procurement", "validity_score": 0}

    # ---- 4. Páginas institucionais conhecidas ----
    if matches_institutional_phrase(title_lower) or matches_institutional_phrase(description_lower):
        return {"is_valid": False, "reason": "institutional_page", "validity_score": 0}

    # ---- 5. Chips de filtro / menus laterais ----
    if matches_filter_chip(title_lower):
        return {"is_valid": False, "reason": "search_filter", "validity_score": 0}

    # ---- 6. Filtro de localização com contador ----
    if matches_location_filter(title):
        return {"is_valid": False, "reason": "location_filter", "validity_score": 0}

    # ---- 7. Categoria/área profissional genérica ----
    if matches_category_pattern(title):
        return {"is_valid": False, "reason": "category", "validity_score": 0}

    # ---- 8. Organização/sigla sem cargo associado ----
    if matches_organization_pattern(title):
        return {"is_valid": False, "reason": "organization", "validity_score": 0}

    # ---- 9. Evidência positiva (JOB_VALIDITY_SCORE) ----
    validity_score = compute_validity_score(title, description, url)

    if validity_score < VALIDITY_THRESHOLD:
        return {"is_valid": False, "reason": "insufficient_job_evidence", "validity_score": validity_score}

    return {"is_valid": True, "reason": None, "validity_score": validity_score}
