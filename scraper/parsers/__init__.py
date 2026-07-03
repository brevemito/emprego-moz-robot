from parsers.emprego_co_mz import parse_emprego_co_mz
from parsers.totalenergies import parse_totalenergies
from parsers.unjobs import parse_unjobs


PARSERS = {
    "emprego_co_mz": parse_emprego_co_mz,
    "totalenergies": parse_totalenergies,
    "unjobs": parse_unjobs
}
