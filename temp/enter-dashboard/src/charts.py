"""Wrappers Plotly para visualizações consistentes."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLOR_EXITO = "#2ecc71"
COLOR_NAO_EXITO = "#e74c3c"
SEQ_MACRO = {"Êxito": COLOR_EXITO, "Não êxito": COLOR_NAO_EXITO}
SEQ_MICRO = {
    "Improcedência": "#27ae60",
    "Extinção": "#16a085",
    "Acordo": "#f39c12",
    "Parcial procedência": "#e67e22",
    "Procedência": "#c0392b",
}


def donut_resultado_micro(df: pd.DataFrame) -> go.Figure:
    counts = df["Resultado micro"].value_counts().reset_index()
    counts.columns = ["Resultado micro", "n"]
    fig = px.pie(
        counts, names="Resultado micro", values="n", hole=0.55,
        color="Resultado micro", color_discrete_map=SEQ_MICRO,
        title="Distribuição dos resultados (Resultado micro)",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def barras_exito_por(df: pd.DataFrame, col: str, title: str | None = None) -> go.Figure:
    from .analysis import taxa_exito_por
    dd = taxa_exito_por(df, col)
    fig = px.bar(
        dd, x=col, y="taxa_exito",
        error_y=dd["ic_hi"] - dd["taxa_exito"],
        error_y_minus=dd["taxa_exito"] - dd["ic_lo"],
        hover_data={"n": True, "ic_lo": ":.3f", "ic_hi": ":.3f"},
        title=title or f"Taxa de êxito por {col} (IC 95%)",
    )
    fig.update_yaxes(tickformat=".0%", title="Taxa de êxito")
    fig.update_layout(showlegend=False)
    return fig


def heatmap_uf_resultado(df: pd.DataFrame) -> go.Figure:
    ct = pd.crosstab(df["UF"], df["Resultado micro"], normalize="index") * 100
    ct = ct.round(1)
    fig = px.imshow(
        ct, aspect="auto", text_auto=".1f", color_continuous_scale="RdYlGn_r",
        labels=dict(x="Resultado micro", y="UF", color="% na UF"),
        title="% de cada resultado por UF",
    )
    fig.update_layout(height=650)
    return fig


def sankey_sub_macro_micro(df: pd.DataFrame) -> go.Figure:
    a = df.groupby(["Sub-assunto", "Resultado macro"]).size().reset_index(name="n")
    b = df.groupby(["Resultado macro", "Resultado micro"]).size().reset_index(name="n")
    labels = (list(df["Sub-assunto"].unique()) +
              list(df["Resultado macro"].unique()) +
              list(df["Resultado micro"].unique()))
    idx = {l: i for i, l in enumerate(labels)}
    src = [idx[x] for x in a["Sub-assunto"]] + [idx[x] for x in b["Resultado macro"]]
    tgt = [idx[x] for x in a["Resultado macro"]] + [idx[x] for x in b["Resultado micro"]]
    val = list(a["n"]) + list(b["n"])
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=18, thickness=18),
        link=dict(source=src, target=tgt, value=val),
    ))
    fig.update_layout(title="Fluxo: Sub-assunto → Resultado macro → Resultado micro", height=520)
    return fig


def barras_lift_subsidios(lift_df: pd.DataFrame) -> go.Figure:
    m = lift_df.melt(
        id_vars=["subsidio"],
        value_vars=["taxa_exito_com", "taxa_exito_sem"],
        var_name="situacao", value_name="taxa",
    )
    m["situacao"] = m["situacao"].map({
        "taxa_exito_com": "Subsídio presente",
        "taxa_exito_sem": "Subsídio ausente",
    })
    fig = px.bar(
        m, x="subsidio", y="taxa", color="situacao", barmode="group",
        color_discrete_map={"Subsídio presente": COLOR_EXITO, "Subsídio ausente": COLOR_NAO_EXITO},
        title="Taxa de êxito com vs sem cada subsídio",
    )
    fig.update_yaxes(tickformat=".0%", title="Taxa de êxito")
    fig.update_layout(xaxis_title=None, legend_title=None)
    return fig


def heatmap_corr_subsidios(df: pd.DataFrame, subsidios: list[str]) -> go.Figure:
    corr = df[subsidios].corr()
    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Correlação entre subsídios (Pearson)",
    )
    fig.update_layout(height=500)
    return fig


def linha_num_subsidios_vs_exito(df: pd.DataFrame) -> go.Figure:
    g = df.groupby("num_subsidios")["sucesso"].agg(["count", "mean"]).reset_index()
    g.columns = ["num_subsidios", "n", "taxa_exito"]
    fig = go.Figure()
    fig.add_bar(x=g["num_subsidios"], y=g["n"], name="Qtd processos", yaxis="y2",
                marker_color="lightgray", opacity=0.6)
    fig.add_scatter(x=g["num_subsidios"], y=g["taxa_exito"], mode="lines+markers",
                    name="Taxa de êxito", line=dict(color=COLOR_EXITO, width=3),
                    marker=dict(size=12))
    fig.update_layout(
        title="Taxa de êxito vs. quantidade de subsídios fornecidos",
        xaxis=dict(title="Quantidade de subsídios (0–6)", dtick=1),
        yaxis=dict(title="Taxa de êxito", tickformat=".0%"),
        yaxis2=dict(title="N processos", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
    )
    return fig


def scatter_causa_condenacao(df: pd.DataFrame, sample: int = 5000) -> go.Figure:
    s = df.sample(min(sample, len(df)), random_state=0)
    fig = px.scatter(
        s, x="Valor da causa", y="Valor da condenação/indenização",
        color="Resultado micro", color_discrete_map=SEQ_MICRO,
        opacity=0.5, title=f"Valor da causa × Valor da condenação (amostra de {len(s):,})",
        labels={"Valor da causa": "Valor da causa (R$)",
                "Valor da condenação/indenização": "Condenação (R$)"},
    )
    fig.update_traces(marker=dict(size=5))
    return fig


def box_condenacao_por(df: pd.DataFrame, col: str, top_n: int | None = None) -> go.Figure:
    sub = df[df["Valor da condenação/indenização"] > 0]
    if top_n is not None:
        top = sub.groupby(col)["Valor da condenação/indenização"].median().nlargest(top_n).index
        sub = sub[sub[col].isin(top)]
    fig = px.box(
        sub, x=col, y="Valor da condenação/indenização",
        points=False, title=f"Valor de condenação por {col} (apenas casos condenados)",
        color=col,
    )
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.update_yaxes(title="Condenação (R$)")
    return fig
