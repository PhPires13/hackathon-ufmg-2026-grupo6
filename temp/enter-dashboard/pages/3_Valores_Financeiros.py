"""Página 3 — Valores financeiros: causa × condenação."""
import streamlit as st
import plotly.express as px
import numpy as np

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters
from src.charts import scatter_causa_condenacao, box_condenacao_por, SEQ_MICRO

st.set_page_config(page_title="Valores Financeiros", page_icon="💰", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("💰 Valores Financeiros")
st.caption(
    "Onde está a maior exposição financeira? Qual o 'desconto' obtido "
    "(valor condenado vs valor pedido)?"
)

if len(filtered) == 0:
    st.warning("Nenhum processo atende aos filtros selecionados.")
    st.stop()

# ======================== Big numbers ========================
perdidos = filtered[filtered["sucesso"] == 0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor total pedido (causa)",
          f"R$ {filtered['Valor da causa'].sum()/1e6:,.1f} mi".replace(",", "."))
c2.metric("Total pago (condenações)",
          f"R$ {filtered['Valor da condenação/indenização'].sum()/1e6:,.1f} mi".replace(",", "."))
if len(perdidos) > 0:
    ratio = perdidos["Valor da condenação/indenização"].sum() / perdidos["Valor da causa"].sum()
    c3.metric("% pago / pedido (nos perdidos)", f"{ratio:.1%}")
    c4.metric("Condenação mediana (perdidos)",
              f"R$ {perdidos['Valor da condenação/indenização'].median():,.0f}".replace(",", "."))

st.divider()

# ======================== Scatter ========================
st.subheader("📉 Dispersão: Valor da causa × Valor da condenação")
st.plotly_chart(scatter_causa_condenacao(filtered), use_container_width=True)
st.caption(
    "Casos verdes (Improcedência/Extinção) ficam colados no eixo X (condenação=0). "
    "Casos vermelhos (Procedência) tendem a ter condenação proporcional ao valor da causa."
)

st.divider()

# ======================== Box por resultado micro ========================
st.subheader("📦 Distribuição de condenação por Resultado micro")
sub = filtered[filtered["Valor da condenação/indenização"] > 0]
fig = px.box(
    sub, x="Resultado micro", y="Valor da condenação/indenização",
    color="Resultado micro", color_discrete_map=SEQ_MICRO, points=False,
    title="Apenas casos em que houve condenação (valor > 0)",
)
fig.update_layout(showlegend=False, xaxis_title=None)
fig.update_yaxes(title="Condenação (R$)")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================== Por UF ========================
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🗺️ Top 10 UFs com maiores condenações")
    st.plotly_chart(box_condenacao_por(filtered, "UF", top_n=10), use_container_width=True)
with col_b:
    st.subheader("🎯 Por Sub-assunto")
    st.plotly_chart(box_condenacao_por(filtered, "Sub-assunto"), use_container_width=True)

st.divider()

# ======================== Condenação por num_subsidios ========================
st.subheader("🔢 Valor de condenação por quantidade de subsídios")
g = (filtered.groupby("num_subsidios")
     .agg(n=("sucesso", "size"),
          taxa_exito=("sucesso", "mean"),
          cond_media=("Valor da condenação/indenização", "mean"),
          cond_media_perdidos=("Valor da condenação/indenização",
                               lambda s: s[s > 0].mean() if (s > 0).any() else 0))
     .reset_index())
fig = px.bar(
    g, x="num_subsidios", y="cond_media",
    hover_data={"n": True, "taxa_exito": ":.1%", "cond_media_perdidos": ":,.0f"},
    title="Condenação média (incluindo R$0 de êxitos) por quantidade de subsídios",
    labels={"cond_media": "Condenação média (R$)", "num_subsidios": "Nº de subsídios"},
)
fig.update_xaxes(dtick=1)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================== Exposição esperada ========================
st.subheader("🎯 Exposição esperada por UF (para priorização da política)")
st.caption(
    "**Exposição esperada por caso** = P(não êxito na UF) × E[condenação | não êxito na UF]. "
    "Indica quanto o banco 'espera pagar' em média por caso naquela UF — "
    "base para decidir onde propor acordos mais agressivos."
)
expo = (filtered.groupby("UF")
        .apply(lambda g: (1 - g["sucesso"].mean()) *
                          g.loc[g["sucesso"] == 0, "Valor da condenação/indenização"].mean()
                          if (g["sucesso"] == 0).any() else 0,
               include_groups=False)
        .reset_index(name="exposicao_esperada"))
expo["n"] = filtered.groupby("UF").size().values
expo["taxa_nao_exito"] = (1 - filtered.groupby("UF")["sucesso"].mean().values)
expo["condenacao_media_perdidos"] = (
    filtered[filtered["sucesso"] == 0].groupby("UF")["Valor da condenação/indenização"].mean()
    .reindex(expo["UF"].values).values
)
expo = expo.sort_values("exposicao_esperada", ascending=False)
fig = px.bar(
    expo, x="UF", y="exposicao_esperada",
    hover_data={"n": True, "taxa_nao_exito": ":.1%",
                "condenacao_media_perdidos": ":,.0f"},
    title="Exposição esperada por caso (R$) por UF",
)
fig.update_layout(xaxis={"categoryorder": "total descending"})
fig.update_yaxes(title="Exposição esperada (R$)")
st.plotly_chart(fig, use_container_width=True)
