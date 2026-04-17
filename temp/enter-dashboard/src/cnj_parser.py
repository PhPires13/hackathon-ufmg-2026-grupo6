"""Parse do número CNJ no formato NNNNNNN-DD.AAAA.J.TR.OOOO."""
import re
import pandas as pd

CNJ_RE = re.compile(r"^(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$")

TRIBUNAL_ESTADUAL = {
    "01": "TJAC", "02": "TJAL", "03": "TJAP", "04": "TJAM", "05": "TJBA",
    "06": "TJCE", "07": "TJDF", "08": "TJES", "09": "TJGO", "10": "TJMA",
    "11": "TJMT", "12": "TJMS", "13": "TJMG", "14": "TJPA", "15": "TJPB",
    "16": "TJPR", "17": "TJPE", "18": "TJPI", "19": "TJRJ", "20": "TJRN",
    "21": "TJRS", "22": "TJRO", "23": "TJRR", "24": "TJSC", "25": "TJSP",
    "26": "TJSE", "27": "TJTO",
}


def parse_cnj_series(numeros: pd.Series) -> pd.DataFrame:
    """Recebe Series com números de processo e retorna DataFrame com
    colunas ano, ramo_justica_cod, tribunal_cod, tribunal_sigla, comarca_cod."""
    extracted = numeros.astype(str).str.extract(CNJ_RE)
    extracted.columns = ["seq", "dv", "ano", "ramo", "tribunal", "comarca"]
    out = pd.DataFrame(index=numeros.index)
    out["ano"] = pd.to_numeric(extracted["ano"], errors="coerce").astype("Int64")
    out["ramo_justica_cod"] = extracted["ramo"]
    out["tribunal_cod"] = extracted["tribunal"]
    out["tribunal_sigla"] = extracted["tribunal"].map(TRIBUNAL_ESTADUAL).fillna("OUTRO")
    out["comarca_cod"] = extracted["comarca"]
    return out
