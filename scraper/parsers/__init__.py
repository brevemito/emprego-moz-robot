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
    "enh": parse_enh
}
