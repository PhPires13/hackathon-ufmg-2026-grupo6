"""Funções estatísticas para cruzamentos categóricos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


def taxa_exito_por(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Retorna taxa de êxito e IC95% (Wilson) para cada nível de `col`."""
    g = df.groupby(col)["sucesso"]
    n = g.count()
    k = g.sum()
    p = k / n
    # Intervalo de Wilson 95%
    z = 1.96
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    err = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    out = pd.DataFrame({
        "n": n,
        "taxa_exito": p,
        "ic_lo": (centre - err).clip(0, 1),
        "ic_hi": (centre + err).clip(0, 1),
    }).reset_index()
    return out.sort_values("taxa_exito", ascending=False)


def cramers_v(df: pd.DataFrame, col: str, target: str = "Resultado macro") -> float:
    """Cramér's V entre duas variáveis categóricas (medida de associação 0–1)."""
    ct = pd.crosstab(df[col], df[target])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return 0.0
    chi2, _, _, _ = chi2_contingency(ct)
    n = ct.sum().sum()
    phi2 = chi2 / n
    r, k = ct.shape
    return float(np.sqrt(phi2 / min(r - 1, k - 1)))


def ranking_associacao(df: pd.DataFrame, cols: list[str], target: str = "Resultado macro") -> pd.DataFrame:
    """Ranking de força de associação (Cramér's V) + chi² p-valor."""
    rows = []
    for c in cols:
        ct = pd.crosstab(df[c], df[target])
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            rows.append({"variavel": c, "cramers_v": 0.0, "chi2": 0.0, "p_valor": 1.0, "n_niveis": ct.shape[0]})
            continue
        chi2, p, _, _ = chi2_contingency(ct)
        n = ct.sum().sum()
        v = np.sqrt((chi2 / n) / min(ct.shape[0] - 1, ct.shape[1] - 1))
        rows.append({
            "variavel": c, "cramers_v": float(v), "chi2": float(chi2),
            "p_valor": float(p), "n_niveis": int(ct.shape[0]),
        })
    return pd.DataFrame(rows).sort_values("cramers_v", ascending=False)


def lift_subsidio(df: pd.DataFrame, subsidios: list[str]) -> pd.DataFrame:
    """Lift de cada subsídio: P(êxito|=1) / P(êxito|=0)."""
    rows = []
    base = df["sucesso"].mean()
    for s in subsidios:
        p1 = df.loc[df[s] == 1, "sucesso"].mean()
        p0 = df.loc[df[s] == 0, "sucesso"].mean()
        n1 = int((df[s] == 1).sum())
        n0 = int((df[s] == 0).sum())
        lift = p1 / p0 if p0 > 0 else float("nan")
        rows.append({
            "subsidio": s,
            "taxa_exito_com": p1,
            "taxa_exito_sem": p0,
            "diferenca_pp": (p1 - p0) * 100,
            "lift": lift,
            "n_com": n1,
            "n_sem": n0,
        })
    out = pd.DataFrame(rows).sort_values("diferenca_pp", ascending=False)
    out.attrs["base"] = base
    return out


def combinacoes_subsidios(df: pd.DataFrame, subsidios: list[str], top: int = 20) -> pd.DataFrame:
    """Top combinações (padrões binários de subsídios) por volume."""
    df2 = df.copy()
    df2["combo"] = df2[subsidios].astype(int).astype(str).agg("".join, axis=1)
    g = df2.groupby("combo").agg(
        n=("sucesso", "size"),
        taxa_exito=("sucesso", "mean"),
        valor_medio_condenacao=("Valor da condenação/indenização", "mean"),
        valor_medio_causa=("Valor da causa", "mean"),
    )
    # Legíveis: lista de subsídios presentes
    def combo_to_names(bits: str) -> str:
        names = [subsidios[i][:12] for i, b in enumerate(bits) if b == "1"]
        return ", ".join(names) if names else "(nenhum)"
    g["subsidios_presentes"] = g.index.map(combo_to_names)
    g["qtd"] = g.index.map(lambda b: sum(int(x) for x in b))
    return g.sort_values("n", ascending=False).head(top).reset_index()
