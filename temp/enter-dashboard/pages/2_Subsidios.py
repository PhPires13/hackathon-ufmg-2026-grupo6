"""Página 2 — Subsídios: qual subsídio pesa mais?"""
import streamlit as st
import plotly.express as px

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters, SUBSIDIOS
from src.charts import (
    barras_lift_subsidios, heatmap_corr_subsidios,
    linha_num_subsidios_vs_exito, barras_exito_por,
)
from src.analysis import lift_subsidio, combinacoes_subsidios

st.set_page_config(page_title="Subsídios", page_icon="📑", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("📑 Análise de Subsídios")
st.caption(
    "Quais documentos (Contrato, Extrato, Dossiê, Comprovante, Demonstrativo, Laudo) "
    "mais influenciam na chance do banco obter êxito?"
)

if len(filtered) == 0:
    st.warning("Nenhum processo atende aos filtros selecionados.")
    st.stop()

# ======================== Disponibilidade ========================
st.subheader("📊 Disponibilidade dos subsídios")
presenca = filtered[SUBSIDIOS].mean().sort_values(ascending=False).reset_index()
presenca.columns = ["Subsídio", "% presente"]
fig = px.bar(
    presenca, x="Subsídio", y="% presente",
    text=presenca["% presente"].map(lambda x: f"{x:.0%}"),
    title="% dos processos com cada subsídio disponibilizado",
)
fig.update_yaxes(tickformat=".0%", range=[0, 1])
fig.update_layout(xaxis_title=None)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================== Lift de cada subsídio ========================
st.subheader("⚖️ Qual é o impacto de cada subsídio na taxa de êxito?")
lift = lift_subsidio(filtered, SUBSIDIOS)
base = lift.attrs["base"]
st.caption(
    f"Taxa de êxito da base filtrada: **{base:.1%}**. A tabela abaixo mostra "
    "a taxa quando o subsídio está presente vs ausente, a diferença em pontos percentuais "
    "e o *lift* (razão entre elas). Ordenada por impacto (pp)."
)

st.plotly_chart(barras_lift_subsidios(lift), use_container_width=True)

lift_disp = lift.copy()
lift_disp["taxa_exito_com"] = lift_disp["taxa_exito_com"].map(lambda x: f"{x:.1%}")
lift_disp["taxa_exito_sem"] = lift_disp["taxa_exito_sem"].map(lambda x: f"{x:.1%}")
lift_disp["diferenca_pp"] = lift_disp["diferenca_pp"].map(lambda x: f"{x:+.1f} pp")
lift_disp["lift"] = lift_disp["lift"].map(lambda x: f"{x:.2f}×")
st.dataframe(lift_disp, use_container_width=True, hide_index=True)

st.info(
    "💡 **Interpretação prática:** o subsídio no topo da tabela é o que mais *por si só* "
    "move a agulha. Mas pode haver correlação com outros — o modelo preditivo (Página 4) "
    "dá o peso considerando todos em conjunto."
)

st.divider()

# ======================== Nº de subsídios ========================
st.subheader("🔢 Quantidade de subsídios × Taxa de êxito")
st.plotly_chart(linha_num_subsidios_vs_exito(filtered), use_container_width=True)
st.caption(
    "À medida que o banco consegue juntar mais subsídios no processo, a taxa de êxito "
    "tende a subir. Linha verde = taxa de êxito; barras cinzas = nº de processos."
)

st.divider()

# ======================== Correlação entre subsídios ========================
st.subheader("🧩 Correlação entre subsídios")
st.caption(
    "Subsídios altamente correlacionados são redundantes — quando aparecem, "
    "aparecem juntos. Isso afeta a interpretação dos coeficientes do modelo."
)
st.plotly_chart(heatmap_corr_subsidios(filtered, SUBSIDIOS), use_container_width=True)

st.divider()

# ======================== Combinações mais comuns ========================
st.subheader("🎛️ Combinações de subsídios mais frequentes")
combos = combinacoes_subsidios(filtered, SUBSIDIOS, top=20)
disp = combos[["subsidios_presentes", "qtd", "n", "taxa_exito", "valor_medio_condenacao", "valor_medio_causa"]].copy()
disp["taxa_exito"] = disp["taxa_exito"].map(lambda x: f"{x:.1%}")
disp["valor_medio_condenacao"] = disp["valor_medio_condenacao"].map(
    lambda x: f"R$ {x:,.0f}".replace(",", "."))
disp["valor_medio_causa"] = disp["valor_medio_causa"].map(
    lambda x: f"R$ {x:,.0f}".replace(",", "."))
disp.columns = ["Subsídios presentes", "Qtd", "N processos", "Taxa êxito",
                "Condenação média", "Causa média"]
st.dataframe(disp, use_container_width=True, hide_index=True, height=500)
st.caption(
    "💡 Combinações com alta taxa de êxito E volume alto são os *playbooks vencedores* "
    "que a política deve reforçar. Combinações com baixa taxa sinalizam casos onde **acordo** "
    "pode ser mais vantajoso."
)
