"""Página 1 — Fatores categóricos: UF, comarca, sub-assunto vs resultado."""
import streamlit as st
import plotly.express as px

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters
from src.charts import heatmap_uf_resultado, sankey_sub_macro_micro, barras_exito_por
from src.analysis import ranking_associacao, taxa_exito_por

st.set_page_config(page_title="Fatores Categóricos", page_icon="🗺️", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("🗺️ Fatores Categóricos")
st.caption(
    "Qual é a força da associação entre cada variável categórica "
    "(UF, comarca, sub-assunto, tribunal) e o desfecho do processo?"
)

if len(filtered) == 0:
    st.warning("Nenhum processo atende aos filtros selecionados.")
    st.stop()

# ======================== Ranking de associação ========================
st.subheader("📊 Força de associação com o resultado (Cramér's V)")
st.caption(
    "Cramér's V mede a força de associação entre duas variáveis categóricas (0 = nenhuma, 1 = máxima). "
    "Quanto maior o valor, mais a variável separa casos de êxito e não-êxito."
)

rank = ranking_associacao(
    filtered,
    cols=["UF", "Sub-assunto", "tribunal_sigla", "comarca_id", "num_subsidios"],
)
rank_display = rank.copy()
rank_display["cramers_v"] = rank_display["cramers_v"].map(lambda x: f"{x:.3f}")
rank_display["p_valor"] = rank_display["p_valor"].map(lambda x: f"{x:.2e}" if x < 0.001 else f"{x:.3f}")
rank_display["chi2"] = rank_display["chi2"].map(lambda x: f"{x:,.1f}".replace(",", "."))
st.dataframe(rank_display, use_container_width=True, hide_index=True)

st.divider()

# ======================== Sankey ========================
st.subheader("🔀 Fluxo Sub-assunto → Macro → Micro")
st.plotly_chart(sankey_sub_macro_micro(filtered), use_container_width=True)

st.divider()

# ======================== Heatmap UF ========================
st.subheader("🗺️ % de cada resultado por UF")
st.plotly_chart(heatmap_uf_resultado(filtered), use_container_width=True)
st.caption(
    "Cada linha soma 100%. UFs com % alto em Procedência/Parcial procedência "
    "são as mais favoráveis aos autores — onde a estratégia de acordo deveria ser mais agressiva."
)

st.divider()

# ======================== UF — taxa de êxito ordenada ========================
st.subheader("🏆 Ranking de UF por taxa de êxito")
st.plotly_chart(barras_exito_por(filtered, "UF"), use_container_width=True)

st.divider()

# ======================== Top comarcas ========================
st.subheader("🏛️ Top 20 comarcas por volume")
g = (filtered.groupby(["comarca_id", "UF"]).agg(
    n=("sucesso", "size"),
    taxa_exito=("sucesso", "mean"),
    valor_medio_condenacao=("Valor da condenação/indenização", "mean"),
).reset_index().sort_values("n", ascending=False).head(20))

col1, col2 = st.columns([1.3, 1])
with col1:
    fig = px.bar(
        g, x="comarca_id", y="n", color="taxa_exito",
        color_continuous_scale="RdYlGn", range_color=(0.3, 1.0),
        hover_data={"UF": True, "taxa_exito": ":.1%",
                    "valor_medio_condenacao": ":,.0f"},
        title="Volume de processos e taxa de êxito (cor)",
    )
    fig.update_layout(xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    display = g.copy()
    display["taxa_exito"] = display["taxa_exito"].map(lambda x: f"{x:.1%}")
    display["valor_medio_condenacao"] = display["valor_medio_condenacao"].map(
        lambda x: f"R$ {x:,.0f}".replace(",", "."))
    st.dataframe(display, use_container_width=True, hide_index=True, height=450)

st.caption(
    "Comarcas são extraídas dos últimos 4 dígitos do número CNJ (código de origem "
    "dentro do tribunal estadual)."
)

st.divider()

# ======================== Sub-assunto ========================
st.subheader("🎯 Sub-assunto × Resultado")
col3, col4 = st.columns(2)
with col3:
    ct = filtered.groupby(["Sub-assunto", "Resultado micro"]).size().reset_index(name="n")
    total_sub = ct.groupby("Sub-assunto")["n"].transform("sum")
    ct["pct"] = ct["n"] / total_sub
    fig = px.bar(
        ct, x="Sub-assunto", y="pct", color="Resultado micro", barmode="stack",
        title="Distribuição de resultado por Sub-assunto",
    )
    fig.update_yaxes(tickformat=".0%", title="% dos casos")
    st.plotly_chart(fig, use_container_width=True)
with col4:
    st.plotly_chart(barras_exito_por(filtered, "Sub-assunto"), use_container_width=True)
