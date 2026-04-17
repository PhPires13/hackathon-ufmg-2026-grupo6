"""Carrega e unifica a base de sentenças + subsídios.

Estratégia:
1. Tenta ler `data/base.parquet` (cache rápido).
2. Se não existir, lê o XLSX, faz merge, aplica feature engineering e salva em parquet.
3. Caminho do XLSX configurável via env var ENTER_XLSX_PATH ou default em `data/` e na pasta pai.
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import streamlit as st

from .cnj_parser import parse_cnj_series

SUBSIDIOS = [
    "Contrato",
    "Extrato",
    "Comprovante de crédito",
    "Dossiê",
    "Demonstrativo de evolução da dívida",
    "Laudo referenciado",
]

DEFAULT_XLSX_NAMES = ["Hackaton_Enter_Base_Candidatos.xlsx", "base.xlsx"]


def _find_xlsx() -> Path:
    env = os.environ.get("ENTER_XLSX_PATH")
    if env and Path(env).exists():
        return Path(env)
    here = Path(__file__).resolve().parent.parent  # enter-dashboard/
    candidates = [
        here / "data" / "Hackaton_Enter_Base_Candidatos.xlsx",
        here / "data" / "base.xlsx",
        here.parent / "Hackaton_Enter_Base_Candidatos.xlsx",  # pasta Enter/
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "XLSX não encontrado. Defina ENTER_XLSX_PATH ou coloque o arquivo em "
        "enter-dashboard/data/ ou na pasta pai (Enter/)."
    )


def _build_dataframe(xlsx_path: Path) -> pd.DataFrame:
    """Lê ambas abas, faz merge e engenharia de features."""
    res = pd.read_excel(xlsx_path, sheet_name="Resultados dos processos")
    sub = pd.read_excel(xlsx_path, sheet_name="Subsídios disponibilizados", header=1)

    # Normaliza nomes das colunas-chave entre as duas abas
    sub = sub.rename(columns={"Número do processos": "Número do processo"})

    df = res.merge(sub, on="Número do processo", how="inner", validate="one_to_one")

    # Feature: quantidade de subsídios
    df["num_subsidios"] = df[SUBSIDIOS].sum(axis=1).astype(int)

    # Feature: flag binário de êxito
    df["sucesso"] = (df["Resultado macro"] == "Êxito").astype(int)

    # Feature: ratio valor pago/pedido (evitar div/0 — raros; fillna 0)
    df["valor_pago_ratio"] = (
        df["Valor da condenação/indenização"] / df["Valor da causa"].replace(0, pd.NA)
    ).fillna(0.0)

    # Parse CNJ
    cnj = parse_cnj_series(df["Número do processo"])
    df = pd.concat([df, cnj], axis=1)

    # Identificador amigável de comarca
    df["comarca_id"] = df["UF"].astype(str) + "-" + df["comarca_cod"].astype(str)

    return df


@st.cache_data(show_spinner="Carregando base de 60k processos...")
def load_data() -> pd.DataFrame:
    here = Path(__file__).resolve().parent.parent
    parquet = here / "data" / "base.parquet"
    if parquet.exists():
        return pd.read_parquet(parquet)

    xlsx = _find_xlsx()
    df = _build_dataframe(xlsx)
    parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet, index=False)
    return df


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros globais salvos em st.session_state."""
    filtered = df
    ufs = st.session_state.get("filter_ufs")
    if ufs:
        filtered = filtered[filtered["UF"].isin(ufs)]
    sub_assuntos = st.session_state.get("filter_sub_assuntos")
    if sub_assuntos:
        filtered = filtered[filtered["Sub-assunto"].isin(sub_assuntos)]
    valor_min = st.session_state.get("filter_valor_min")
    valor_max = st.session_state.get("filter_valor_max")
    if valor_min is not None:
        filtered = filtered[filtered["Valor da causa"] >= valor_min]
    if valor_max is not None:
        filtered = filtered[filtered["Valor da causa"] <= valor_max]
    return filtered


def render_sidebar_filters(df: pd.DataFrame) -> None:
    """Renderiza filtros na sidebar (reusável entre páginas)."""
    st.sidebar.header("Filtros globais")
    all_ufs = sorted(df["UF"].unique())
    st.sidebar.multiselect(
        "UF", options=all_ufs, default=[], key="filter_ufs",
        help="Deixe vazio para considerar todas"
    )
    st.sidebar.multiselect(
        "Sub-assunto",
        options=sorted(df["Sub-assunto"].unique()),
        default=[], key="filter_sub_assuntos",
    )
    vmin = int(df["Valor da causa"].min())
    vmax = int(df["Valor da causa"].max())
    faixa = st.sidebar.slider(
        "Faixa de valor da causa (R$)",
        min_value=vmin, max_value=vmax, value=(vmin, vmax), step=500,
    )
    st.session_state["filter_valor_min"] = faixa[0]
    st.session_state["filter_valor_max"] = faixa[1]

    if st.sidebar.button("Limpar filtros"):
        for k in ["filter_ufs", "filter_sub_assuntos"]:
            st.session_state[k] = []
        st.rerun()
