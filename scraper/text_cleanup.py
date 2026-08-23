# =========================================================================
# Limpeza de texto para apresentação (título + localização)
# =========================================================================
#
# Este módulo NÃO decide se um item é uma vaga válida (isso é o
# job_validator.py) - só melhora a APRESENTAÇÃO do que já foi aceite,
# para ficar pronto a publicar no brevemito.com:
#
#   1. smart_title_case(): "ASSISTENTE DE CONTROLO DE CREDITO" ->
#      "Assistente de Controlo de Credito", preservando siglas como
#      "M/F", "HSE", "QHSE", "TI".
#
#   2. extract_location(): lê o título/descrição à procura de uma
#      província ou cidade de Moçambique mencionada, para substituir o
#      valor genérico "Moçambique" por algo mais específico e útil para
#      filtrar vagas por localização no site (ex.: "Pemba", "Beira").
#
# =========================================================================

import re


# =========================================================================
# CAPITALIZAÇÃO INTELIGENTE
# =========================================================================

# Siglas/abreviaturas que devem manter-se exactamente como estão,
# independentemente de estarem em maiúsculas no texto original.
PRESERVE_AS_IS = {
    "M/F", "F/M", "HSE", "HSSE", "QHSE", "HST", "SST", "EPI", "TI", "IT",
    "HR", "RH", "CEO", "CFO", "COO", "ONG", "NGO", "UN", "ONU", "UNICEF",
    "ESAR", "CST", "PSA", "USD", "MZN", "PF4C", "OHCHR", "WFP", "UNDP",
    "UNHCR", "UNFPA", "WHO", "OMS", "GV4G", "EWENE",
}
_PRESERVE_LOOKUP = {w.upper(): w for w in PRESERVE_AS_IS}

# Palavras pequenas de ligação que ficam em minúsculas no meio do título
# (mas não se forem a primeira palavra).
_LOWERCASE_CONNECTORS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "em", "para", "com",
    "num", "numa", "no", "na", "nos", "nas", "à", "ao", "aos", "às",
    "and", "of", "the", "for", "in", "on", "at", "to", "or",
}


def _capitalize_word(word, is_first_word):
    """Aplica a regra de capitalização a uma única palavra/token."""

    if not word:
        return word

    # Siglas conhecidas: preservar tal como estão definidas na lista,
    # independentemente da capitalização com que apareceram no original.
    bare = word.strip("(),.:;")
    if bare.upper() in _PRESERVE_LOOKUP:
        preserved = _PRESERVE_LOOKUP[bare.upper()]
        return word.replace(bare, preserved)

    # Padrões tipo "M/F" com barra (ex.: "M/F", "m/f") - preservar em
    # maiúsculas por convenção do sector de recrutamento em Moçambique.
    if re.fullmatch(r"[A-Za-z]/[A-Za-z]", bare):
        return word.replace(bare, bare.upper())

    # Números, códigos de referência (#138289), percentagens: não mexer.
    if re.search(r"\d", bare):
        return word

    # Conectores em minúsculas, excepto se for a primeira palavra do título.
    if not is_first_word and bare.lower() in _LOWERCASE_CONNECTORS:
        return word.replace(bare, bare.lower())

    # NOTA: já tivemos aqui uma heurística que preservava "siglas curtas
    # desconhecidas" (todas maiúsculas, 2-6 letras). Removida de propósito:
    # esta função só corre quando o título INTEIRO já está predominantemente
    # em maiúsculas (>70%), por isso praticamente qualquer palavra comum
    # também aparece toda em maiúsculas nesse contexto (ex.: "SENIOR",
    # "CLAIMS") - a heurística não conseguia distinguir isso de uma sigla
    # real, e produzia capitalização inconsistente (ex.: "SENIOR Contract
    # & CLAIMS Engineer"). A única forma fiável de preservar uma sigla é
    # via a lista explícita PRESERVE_AS_IS acima - qualquer sigla nova
    # que apareça deve ser adicionada lá.

    # Caso geral: primeira letra maiúscula, resto minúsculas.
    if bare.isalpha() or "-" in bare:
        # Suporta palavras compostas com hífen (ex.: "sócio-ambiental").
        parts = bare.split("-")
        capitalized = "-".join(p[:1].upper() + p[1:].lower() if p else p for p in parts)
        return word.replace(bare, capitalized)

    return word


def smart_title_case(text):
    """
    Converte um título para capitalização legível, preservando siglas
    conhecidas (M/F, HSE, QHSE, TI, etc.) e números/códigos de referência.

    Só reformata texto que pareça "GRITADO" (muitas maiúsculas seguidas)
    ou totalmente em minúsculas - títulos já bem formatados (mistura
    normal de maiúsculas/minúsculas) são deixados exactamente como estão,
    para não estragar títulos que os empregadores já escreveram bem.
    """
    if not text:
        return text

    letters = [c for c in text if c.isalpha()]
    if not letters:
        return text

    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)

    # Só reescreve se o título estiver predominantemente em maiúsculas
    # (>70% das letras) ou totalmente em minúsculas (0% maiúsculas).
    # Títulos com capitalização mista normal ficam intocados.
    if 0.0 < upper_ratio < 0.7:
        return text

    words = text.split(" ")
    result = []
    is_first = True

    for word in words:
        if word == "":
            result.append(word)
            continue
        result.append(_capitalize_word(word, is_first))
        if word.strip("(),.:;"):
            is_first = False

    return " ".join(result)


# =========================================================================
# EXTRACÇÃO DE LOCALIZAÇÃO
# =========================================================================

# Cidades/distritos mais específicos primeiro (para dar preferência a
# "Pemba" em vez de apenas "Cabo Delgado" quando ambos aparecem).
MOZAMBIQUE_CITIES = [
    "Maputo", "Matola", "Beira", "Chimoio", "Tete", "Quelimane",
    "Nampula", "Pemba", "Lichinga", "Xai-Xai", "Inhambane", "Nacala",
    "Chiúre", "Chiure", "Palma", "Afungi", "Mocímboa da Praia",
    "Montepuez", "Cuamba", "Angoche", "Gurué", "Dondo", "Manica",
    "Chókwè", "Chokwe", "Vilankulo", "Massinga", "Mueda", "Ilha de Moçambique",
    "Marrupa", "Metangula", "Milange", "Mocuba", "Ribáuè",
]

MOZAMBIQUE_PROVINCES = [
    "Cabo Delgado", "Niassa", "Nampula", "Zambézia", "Zambezia", "Tete",
    "Manica", "Sofala", "Inhambane", "Gaza", "Maputo Província",
    "Maputo Provincia",
]

# Ordenar por comprimento decrescente para que nomes compostos (ex.:
# "Cabo Delgado", "Xai-Xai") sejam detectados antes de qualquer
# substring mais curta coincidente.
_ALL_LOCATIONS = sorted(
    set(MOZAMBIQUE_CITIES + MOZAMBIQUE_PROVINCES),
    key=len,
    reverse=True
)
_LOCATION_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(loc) for loc in _ALL_LOCATIONS) + r")\b",
    re.IGNORECASE
)

# Mapa para normalizar a capitalização do nome encontrado, independente
# de como apareceu no texto original (maiúsculas, minúsculas, etc.)
_CANONICAL_NAME = {loc.lower(): loc for loc in _ALL_LOCATIONS}


GENERIC_LOCATION_VALUES = {"", "moçambique", "mozambique", "moçambique.", "n/a", "não especificado"}


def extract_location(*texts):
    """
    Procura, pelo texto fornecido (título, descrição, etc.), uma menção
    a uma cidade ou província de Moçambique. Devolve o nome encontrado
    com capitalização normalizada, ou None se não encontrar nada.

    Se encontrar mais do que uma localização diferente, devolve as duas
    primeiras encontradas, separadas por vírgula (ex.: "Pemba, Cabo
    Delgado"), para manter alguma precisão sem sobrecarregar o campo.
    """
    combined = " ".join(t for t in texts if t)

    matches = []
    seen_lower = set()

    for m in _LOCATION_REGEX.finditer(combined):
        canonical = _CANONICAL_NAME[m.group(1).lower()]
        if canonical.lower() not in seen_lower:
            seen_lower.add(canonical.lower())
            matches.append(canonical)
        if len(matches) >= 2:
            break

    if not matches:
        return None

    return ", ".join(matches)


def improve_location(current_location, title, description=None):
    """
    Só substitui o campo de localização se o valor actual for genérico
    (vazio ou apenas "Moçambique"). Se já houver algo mais específico
    definido pelo parser da fonte, respeita-o e não mexe.
    """
    current_normalized = (current_location or "").strip().lower()

    if current_normalized not in GENERIC_LOCATION_VALUES:
        return current_location

    found = extract_location(title, description or "")

    if found:
        return found

    return current_location or "Moçambique"
