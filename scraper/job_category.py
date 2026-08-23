# =========================================================================
# Categorização de vagas por área profissional
# =========================================================================
#
# Atribui uma categoria a cada vaga, com base no título, para o
# brevemito.com poder organizar/filtrar as vagas por área (ex.: mostrar
# só vagas de "Logística e Transportes", ou "Tecnologia da Informação").
#
# Tal como em job_validator.py, isto é baseado em EVIDÊNCIA POSITIVA
# (palavras associadas a cada área), não numa lista negra. Uma vaga pode,
# teoricamente, encaixar em mais do que uma categoria (ex.: "Estágio de
# TI" é simultaneamente "Estágio" e "Tecnologia da Informação") - nesses
# casos aplicamos uma ordem de prioridade definida em CATEGORY_PRIORITY.
#
# =========================================================================

import re


CATEGORY_KEYWORDS = {

    "Estágios": [
        "estágio", "estagio", "estagiário", "estagiario", "estagiária",
        "intern", "internship", "trainee",
    ],

    "Tecnologia da Informação": [
        "programador", "programadora", "desenvolvedor", "desenvolvedora",
        "developer", "programmer", "software", "sistemas de informação",
        "ti", "it officer", "it support", "informática", "informatica",
        "cibersegurança", "database", "rede informática",
    ],

    "Saúde": [
        "enfermeiro", "enfermeira", "médico", "medico", "médica",
        "farmacêutico", "farmaceutico", "nutricionista", "psicólogo",
        "psicologo", "socorrista", "nurse", "doctor", "pharmacist",
        "clinico", "clínico", "clínica", "saúde", "paramedic",
    ],

    "Segurança e HSE": [
        "hse", "hst", "sst", "hsse", "qhse", "safety", "guarda",
        "segurança", "sinaleiro", "epi",
    ],

    "Financeiro e Contabilidade": [
        "contabilista", "financeiro", "financeira", "finanças", "financas",
        "accountant", "auditor", "auditora", "orçamentista", "orcamentista",
        "budget", "finance", "controlo de credito", "controlador financeiro",
        "banqueiro",
    ],

    "Recursos Humanos": [
        "recrutador", "recrutadora", "recruiter", "recursos humanos",
        "talent", "human resources", "rh",
    ],

    "Comercial e Vendas": [
        "vendedor", "vendedora", "comercial", "sales", "caixa",
        "cashier", "salesperson", "representante comercial",
    ],

    "Logística e Transportes": [
        "motorista", "driver", "logístico", "logistico", "armazenista",
        "estivador", "camionista", "warehouse", "warehousing",
        "despacho de mercadorias", "condutor", "piloto",
        "agente de navegação", "frotas", "aprovisionamento",
        "supply chain", "buyer", "comprador", "compradora",
    ],

    "Engenharia": [
        "engenheiro", "engenheira", "engineer", "geólogo", "geologo",
        "arquitecto", "arquiteto", "topógrafo", "topografo",
    ],

    "Construção e Manutenção Técnica": [
        "pedreiro", "carpinteiro", "soldador", "mason", "carpenter",
        "welder", "electricista", "eletricista", "electrician",
        "mecânico", "mecanico", "mechanic", "técnico eléctrico",
        "técnico mecânico", "operador de ponte rolante", "estaleiro",
    ],

    "Hotelaria e Restauração": [
        "cozinheiro", "cozinheira", "cook", "chef", "empregado de mesa",
        "hotelaria", "receptionist", "recepcionista",
    ],

    "Gestão e Direcção": [
        "gestor", "gestora", "gerente", "director", "diretor",
        "directora", "diretora", "manager", "executive", "supervisor",
        "supervisora", "chefe", "administrador", "administradora",
        "ceo", "cfo", "coo", "vice president", "head of",
    ],

    "Consultoria e Organizações Internacionais": [
        "consultor", "consultora", "consultant", "consultancy",
        "oficial", "officer", "coordenador", "coordenadora",
        "coordinator", "assistente", "assistant", "analista", "analyst",
        "especialista", "specialist",
    ],
}

# Ordem de prioridade quando um título corresponde a mais do que uma
# categoria: a primeira categoria da lista que tiver correspondência
# "ganha". Estágios primeiro (é uma característica mais específica e
# útil para filtrar do que a área em si); Gestão/Consultoria por último
# por serem categorias muito abrangentes que facilmente "engolem"
# títulos que encaixam melhor numa área mais específica.
CATEGORY_PRIORITY = [
    "Estágios",
    "Saúde",
    "Segurança e HSE",
    "Tecnologia da Informação",
    "Financeiro e Contabilidade",
    "Recursos Humanos",
    "Comercial e Vendas",
    "Logística e Transportes",
    "Engenharia",
    "Construção e Manutenção Técnica",
    "Hotelaria e Restauração",
    "Gestão e Direcção",
    "Consultoria e Organizações Internacionais",
]

FALLBACK_CATEGORY = "Outros"


def _compile_pattern(keywords):
    """
    Compila uma regex com fronteiras de palavra (\\b) para cada
    palavra-chave, com um sufixo plural opcional (s/es). Isto evita dois
    tipos de falso positivo:
      - Substring dentro de outra palavra (ex.: "coo" a apanhar
        "Coordinator", "rh" a apanhar "linha").
      - Falhar em apanhar plurais legítimos (ex.: "motorista" não bater
        em "Motoristas").
    Frases com mais de uma palavra (ex.: "vice president") são tratadas
    literalmente, sem sufixo plural.
    """
    parts = []
    for k in keywords:
        k = k.strip()
        if " " in k:
            parts.append(re.escape(k))
        else:
            parts.append(r"\b" + re.escape(k) + r"(?:es|s)?\b")
    return re.compile("|".join(parts), re.IGNORECASE)


_COMPILED = {
    cat: _compile_pattern(keywords)
    for cat, keywords in CATEGORY_KEYWORDS.items()
}


def categorize(title, description=None):
    """
    Devolve o nome da categoria mais adequada para a vaga, com base no
    título (e, subsidiariamente, na descrição). Devolve "Outros" se
    nenhuma categoria tiver correspondência.
    """
    text = f"{title or ''} {description or ''}"

    for category in CATEGORY_PRIORITY:
        pattern = _COMPILED[category]
        if pattern.search(text):
            return category

    return FALLBACK_CATEGORY
