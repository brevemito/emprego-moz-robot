from parsers.emprego_co_mz import parse_emprego_co_mz
from parsers.totalenergies import parse_totalenergies
from parsers.unjobs import parse_unjobs
from parsers.reliefweb import parse_reliefweb
from parsers.vodacom_mz import parse_vodacom_mz
from parsers.bci import parse_bci
from parsers.millennium_bim import parse_millennium_bim
from parsers.movitel import parse_movitel
from parsers.contact_mz import parse_contact_mz
from parsers.enh import parse_enh
from parsers.agl_transport import parse_agl_transport
from parsers.un_mozambique import parse_un_mozambique
from parsers.absa import parse_absa
from parsers.mozambique_lng import parse_mozambique_lng
from parsers.bni import parse_bni
from parsers.moza_banco import parse_moza_banco
from parsers.heineken_mz import parse_heineken_mz
from parsers.cim import parse_cim
from parsers.mozparks import parse_mozparks
from parsers.crowe_mz import parse_crowe_mz


PARSERS = {
    "emprego_co_mz": parse_emprego_co_mz,
    "totalenergies": parse_totalenergies,
    "unjobs": parse_unjobs,
    "reliefweb": parse_reliefweb,
    "vodacom_mz": parse_vodacom_mz,
    "bci": parse_bci,
    "millennium_bim": parse_millennium_bim,
    "movitel": parse_movitel,
    "contact_mz": parse_contact_mz,
    "enh": parse_enh,
    "agl_transport": parse_agl_transport,
    "un_mozambique": parse_un_mozambique,
    "absa": parse_absa,
    "mozambique_lng": parse_mozambique_lng,
    "bni": parse_bni,
    "moza_banco": parse_moza_banco,
    "heineken_mz": parse_heineken_mz,
    "cim": parse_cim,
    "mozparks": parse_mozparks,
    "crowe_mz": parse_crowe_mz
    # NOTA: "tmcel" fica deliberadamente sem parser - ver comentário em
    # sources.py (robots.txt bloqueia scraping nos domínios reais).
}
