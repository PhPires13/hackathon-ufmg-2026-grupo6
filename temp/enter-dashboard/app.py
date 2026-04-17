"""Enter Dashboard — Hackathon UFMG.

Home: KPIs e visão geral da base de 60k sentenças do Banco UFMG em casos de
'não reconhecimento de contratação de empréstimo'.
"""
import streamlit as st
import plotly.express as px

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters, SUBSIDIOS
from src.charts import donut_resultado_micro, SEQ_MACRO

st.set_page_config(
    page_title="Enter Dashboard — Banco UFMG",
    page_icon="⚖️",
    layout="wide",
)

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("⚖️ Dashboard — Política de Acordos | Banco UFMG")
st.caption(
    "Análise exploratória de 60.000 sentenças em casos de *não reconhecimento "
    "de contratação de empréstimo* para embasar a política de acordos."
)

if len(filtered) == 0:
    st.warning("Nenhum processo atende aos filtros selecionados.")
    st.stop()

# ======================== KPIs ========================
c1, c2, c3, c4 = st.columns(4)
total = len(filtered)
taxa_exito = filtered["sucesso"].mean()
valor_causa_medio = filtered["Valor da causa"].mean()
valor_cond_medio = filtered["Valor da condenação/indenização"].mean()
valor_cond_medio_perdidos = filtered.loc[filtered["sucesso"] == 0, "Valor da condenação/indenização"].mean()

c1.metric("Processos", f"{total:,}".replace(",", "."))
c2.metric("Taxa de êxito", f"{taxa_exito:.1%}",
          help="Êxito = banco não é condenado (Improcedência ou Extinção)")
c3.metric("Valor médio da causa", f"R$ {valor_causa_medio:,.0f}".replace(",", "."))
c4.metric("Condenação média (casos perdidos)", f"R$ {valor_cond_medio_perdidos:,.0f}".replace(",", "."))

st.divider()

# ======================== Linhas principais ========================
col_a, col_b = st.columns([1.2, 1])

with col_a:
    st.plotly_chart(donut_resultado_micro(filtered), use_container_width=True)

with col_b:
    st.subheader("Êxito por Sub-assunto")
    g = (filtered.groupby("Sub-assunto")["sucesso"]
         .agg(["count", "mean"]).reset_index()
         .rename(columns={"count": "n", "mean": "taxa_exito"}))
    fig = px.bar(
        g, x="Sub-assunto", y="taxa_exito",
        text=g["taxa_exito"].map(lambda x: f"{x:.1%}"),
        color="Sub-assunto", title=None,
    )
    fig.update_yaxes(tickformat=".0%", title="Taxa de êxito")
    fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Processos classificados como **Golpe** e **Genérico** podem ter "
        "padrões de desfecho distintos — observe a diferença."
    )

# ======================== Exposição financeira ========================
st.divider()
st.subheader("💰 Exposição financeira")

perdidos = filtered[filtered["sucesso"] == 0]
exposicao_total = perdidos["Valor da condenação/indenização"].sum()
valor_causa_total = filtered["Valor da causa"].sum()
economia_hipotetica = filtered.loc[filtered["sucesso"] == 1, "Valor da causa"].sum() - \
                     filtered.loc[filtered["sucesso"] == 1, "Valor da condenação/indenização"].sum()

ec1, ec2, ec3 = st.columns(3)
ec1.metric("Valor total em jogo (causa)", f"R$ {valor_causa_total/1e6:,.1f} mi".replace(",", "."))
ec2.metric("Condenações pagas (perdidos)", f"R$ {exposicao_total/1e6:,.1f} mi".replace(",", "."))
ec3.metric("Economia histórica (êxito)", f"R$ {economia_hipotetica/1e6:,.1f} mi".replace(",", "."),
           help="Soma de Valor da causa - Valor pago, nos casos em que o banco obteve êxito")

st.caption(
    f"Com **{total:,}**".replace(",", ".") +
    f" processos analisados, o banco deixou de pagar cerca de "
    f"**R$ {economia_hipotetica/1e6:,.1f} milhões**".replace(",", ".") +
    " em casos de êxito (Improcedência/Extinção) em relação ao valor pedido pelos autores."
)

# ======================== Guia das páginas ========================
st.divider()
st.subheader("🗺️ Navegação")
st.markdown("""
Use as páginas na barra lateral para aprofundar:

- **1 — Fatores Categóricos:** UF, comarca, sub-assunto × resultado. Teste de associação (Cramér's V).
- **2 — Subsídios:** qual é o peso de cada documento (Contrato, Extrato, Dossiê...) na taxa de êxito.
- **3 — Valores Financeiros:** distribuição de causa × condenação e onde estão as maiores exposições.
- **4 — Modelo Preditivo:** Logistic + Random Forest + SHAP → qual é o fator que mais pesa **em conjunto**.
""")

# Atalho para amostra dos dados
with st.expander("🔍 Ver amostra dos dados (10 linhas)"):
    st.dataframe(
        filtered.sample(min(10, len(filtered)), random_state=0)[
            ["Número do processo", "UF", "tribunal_sigla", "Sub-assunto",
             "Resultado macro", "Resultado micro", "Valor da causa",
             "Valor da condenação/indenização", "num_subsidios"]
        ],
        use_container_width=True,
    )
