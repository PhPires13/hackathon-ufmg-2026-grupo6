"""Página 9 — Análise e Modelo de Acordos.

Analisa apenas os casos finalizados com acordo e treina um modelo para
prever o valor do acordo em relação ao valor da causa.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters, SUBSIDIOS
from src.modeling_acordo import train_acordo_model, predict_acordo, _add_features_acordo

st.set_page_config(page_title="Análise de Acordos", page_icon="🤝", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("🤝 Análise e Modelo de Acordos")
st.caption(
    "Analisa os casos que finalizaram com acordo e treina um modelo para "
    "prever o valor do acordo em relação ao valor da causa."
)

# Filtrar apenas acordos
acordos = filtered[filtered["Resultado micro"] == "Acordo"].copy()

if len(acordos) == 0:
    acordos_full = df[df["Resultado micro"] == "Acordo"]
    st.warning(
        f"Nenhum acordo encontrado com os filtros atuais. "
        f"Existem **{len(acordos_full)}** acordos na base completa. "
        "Remova os filtros ou ajuste-os para incluir acordos."
    )
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# PARTE 1: ANÁLISE DESCRITIVA DOS ACORDOS
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader(f"📊 Parte 1 — Análise descritiva ({len(acordos)} acordos)")

# Métricas resumo
acordos["ratio_acordo"] = acordos["Valor da condenação/indenização"] / acordos["Valor da causa"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de acordos", f"{len(acordos):,}")
col2.metric("Ratio médio (acordo/causa)", f"{acordos['ratio_acordo'].mean():.1%}")
col3.metric("Ratio mediano", f"{acordos['ratio_acordo'].median():.1%}")
col4.metric("Valor médio do acordo", f"R$ {acordos['Valor da condenação/indenização'].mean():,.0f}".replace(",", "."))

col5, col6, col7, col8 = st.columns(4)
col5.metric("Valor da causa médio", f"R$ {acordos['Valor da causa'].mean():,.0f}".replace(",", "."))
col6.metric("Menor ratio", f"{acordos['ratio_acordo'].min():.1%}")
col7.metric("Maior ratio", f"{acordos['ratio_acordo'].max():.1%}")
col8.metric("Desvio padrão ratio", f"{acordos['ratio_acordo'].std():.1%}")

st.markdown("---")

# Distribuição do ratio
c1, c2 = st.columns(2)
with c1:
    fig_hist = px.histogram(
        acordos, x="ratio_acordo", nbins=25,
        title="Distribuição do ratio Acordo / Valor da Causa",
        labels={"ratio_acordo": "Ratio (Acordo / Causa)"},
        color_discrete_sequence=["#3498db"],
    )
    fig_hist.add_vline(x=acordos["ratio_acordo"].mean(), line_dash="dash",
                       line_color="red", annotation_text=f"Média: {acordos['ratio_acordo'].mean():.1%}")
    fig_hist.add_vline(x=acordos["ratio_acordo"].median(), line_dash="dash",
                       line_color="green", annotation_text=f"Mediana: {acordos['ratio_acordo'].median():.1%}")
    fig_hist.update_layout(height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

with c2:
    fig_scatter = px.scatter(
        acordos, x="Valor da causa", y="Valor da condenação/indenização",
        color="ratio_acordo", color_continuous_scale="RdYlGn_r",
        title="Valor da Causa vs Valor do Acordo",
        labels={"Valor da condenação/indenização": "Valor do Acordo (R$)",
                "Valor da causa": "Valor da Causa (R$)", "ratio_acordo": "Ratio"},
        hover_data={"UF": True, "Sub-assunto": True},
    )
    # Linha de referência (30%)
    x_range = np.linspace(acordos["Valor da causa"].min(), acordos["Valor da causa"].max(), 100)
    fig_scatter.add_scatter(x=x_range, y=x_range * 0.3, mode="lines",
                            line=dict(dash="dash", color="gray"), name="30% da causa")
    fig_scatter.update_layout(height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)

# Por UF
st.markdown("---")
c3, c4 = st.columns(2)
with c3:
    uf_stats = (acordos.groupby("UF")
                .agg(n=("ratio_acordo", "size"),
                     ratio_medio=("ratio_acordo", "mean"))
                .reset_index()
                .sort_values("ratio_medio"))
    fig_uf = px.bar(uf_stats, x="UF", y="ratio_medio",
                    color="ratio_medio", color_continuous_scale="RdYlGn_r",
                    hover_data={"n": True},
                    title="Ratio médio acordo/causa por UF")
    fig_uf.update_yaxes(tickformat=".0%", title="Ratio médio")
    fig_uf.update_layout(height=400, xaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_uf, use_container_width=True)

with c4:
    sub_stats = (acordos.groupby("Sub-assunto")
                 .agg(n=("ratio_acordo", "size"),
                      ratio_medio=("ratio_acordo", "mean"))
                 .reset_index()
                 .sort_values("ratio_medio"))
    fig_sub = px.bar(sub_stats, x="Sub-assunto", y="ratio_medio",
                     color="ratio_medio", color_continuous_scale="RdYlGn_r",
                     hover_data={"n": True},
                     title="Ratio médio acordo/causa por Sub-assunto")
    fig_sub.update_yaxes(tickformat=".0%", title="Ratio médio")
    fig_sub.update_layout(height=400)
    st.plotly_chart(fig_sub, use_container_width=True)

# Tabela com todos os acordos
with st.expander("📋 Tabela completa de acordos"):
    show_cols = ["Número do processo", "UF", "Sub-assunto", "Valor da causa",
                 "Valor da condenação/indenização", "ratio_acordo", "num_subsidios"]
    show_df = acordos[show_cols].copy()
    show_df["ratio_acordo"] = show_df["ratio_acordo"].map(lambda x: f"{x:.1%}")
    show_df["Valor da causa"] = show_df["Valor da causa"].map(
        lambda x: f"R$ {x:,.0f}".replace(",", "."))
    show_df["Valor da condenação/indenização"] = show_df["Valor da condenação/indenização"].map(
        lambda x: f"R$ {x:,.0f}".replace(",", "."))
    st.dataframe(show_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# PARTE 2: MODELO PREDITIVO DE ACORDO
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🤖 Parte 2 — Modelo preditivo de valor de acordo")

if len(acordos) < 20:
    st.warning("Menos de 20 acordos disponíveis. O modelo pode ser impreciso.")

# Treinar modelo
acordo_bundle = train_acordo_model(df_hash=len(df))

# Métricas do modelo
st.markdown("#### 📏 Métricas do modelo")
m = acordo_bundle.metrics

m1, m2, m3, m4 = st.columns(4)
m1.metric("MAE (ratio)", f"{m['mae_ratio']:.4f}",
          help="Erro absoluto médio no ratio acordo/causa")
m2.metric("MAPE (%)", f"{m['mape']:.1f}%",
          help="Erro percentual médio absoluto")
m3.metric("Cobertura P25-P75", f"{m['cobertura_p25_p75']:.1%}",
          help="% de acordos reais dentro da faixa P25-P75 predita")
m4.metric("N treino / teste", f"{m['n_treino']} / {m['n_teste']}")

st.caption(
    f"Ratio médio no treino: **{m['ratio_medio_treino']:.1%}** | "
    f"Ratio mediano no treino: **{m['ratio_mediano_treino']:.1%}** | "
    f"Total de acordos no banco: **{m['n_total_acordos']}**"
)

# ── Validação no test set ──
st.markdown("---")
st.markdown("#### 🧪 Validação no test set (20%)")

# Pegar dados de teste
test_idx = acordo_bundle.test_indices
if test_idx is not None:
    acordos_full = df[df["Resultado micro"] == "Acordo"].copy()
    acordos_full["ratio_acordo"] = (
        acordos_full["Valor da condenação/indenização"] /
        acordos_full["Valor da causa"].replace(0, np.nan)
    ).fillna(0)
    acordos_full = _add_features_acordo(acordos_full)

    test_data = acordos_full.loc[acordos_full.index.intersection(test_idx)]

    if len(test_data) > 0:
        all_feats = ["UF", "Sub-assunto", "tribunal_sigla"] + acordo_bundle.numeric_feats
        pred_ratio = acordo_bundle.pipeline_median.predict(test_data[all_feats])
        pred_ratio = np.clip(pred_ratio, 0, 1)

        pred_p25 = acordo_bundle.pipeline_p25.predict(test_data[all_feats])
        pred_p75 = acordo_bundle.pipeline_p75.predict(test_data[all_feats])
        pred_p25 = np.clip(pred_p25, 0, 1)
        pred_p75 = np.clip(pred_p75, 0, 1)

        real_ratio = test_data["ratio_acordo"].values
        real_valor = test_data["Valor da condenação/indenização"].values
        pred_valor = pred_ratio * test_data["Valor da causa"].values

        # Scatter: predito vs real
        fig_val = px.scatter(
            x=real_ratio, y=pred_ratio,
            labels={"x": "Ratio real (acordo/causa)", "y": "Ratio predito"},
            title="Validação: Ratio predito vs Ratio real (test set)",
            color_discrete_sequence=["#2ecc71"],
        )
        fig_val.add_scatter(x=[0, 0.5], y=[0, 0.5], mode="lines",
                            line=dict(dash="dash", color="red"), name="Perfeito")
        fig_val.update_layout(height=450)
        st.plotly_chart(fig_val, use_container_width=True)

        # Erro por processo
        erro_ratio = pred_ratio - real_ratio
        erro_valor = pred_valor - real_valor

        e1, e2, e3 = st.columns(3)
        e1.metric("Erro médio ratio", f"{erro_ratio.mean():+.4f}",
                   help="Positivo = modelo superestima o ratio")
        e2.metric("Erro médio R$", f"R$ {erro_valor.mean():+,.0f}".replace(",", "."))
        e3.metric("% dentro da faixa P25-P75",
                  f"{((real_ratio >= pred_p25) & (real_ratio <= pred_p75)).mean():.1%}")

        # Histograma dos erros
        fig_err = px.histogram(
            x=erro_ratio, nbins=20,
            title="Distribuição do erro (ratio predito − ratio real)",
            labels={"x": "Erro no ratio", "y": "Frequência"},
            color_discrete_sequence=["#e74c3c"],
        )
        fig_err.add_vline(x=0, line_dash="dash", line_color="green",
                          annotation_text="Erro zero")
        fig_err.update_layout(height=350)
        st.plotly_chart(fig_err, use_container_width=True)

        # Tabela detalhada
        with st.expander("📋 Detalhes por processo (test set)"):
            detail = pd.DataFrame({
                "UF": test_data["UF"].values,
                "Sub-assunto": test_data["Sub-assunto"].values,
                "Valor da causa": test_data["Valor da causa"].values,
                "Ratio real": real_ratio,
                "Ratio predito": pred_ratio,
                "Erro ratio": erro_ratio,
                "Acordo real (R$)": real_valor,
                "Acordo predito (R$)": pred_valor,
                "Erro (R$)": erro_valor,
            })
            detail["Ratio real"] = detail["Ratio real"].map(lambda x: f"{x:.1%}")
            detail["Ratio predito"] = detail["Ratio predito"].map(lambda x: f"{x:.1%}")
            detail["Erro ratio"] = detail["Erro ratio"].map(lambda x: f"{x:+.1%}")
            for c in ["Valor da causa", "Acordo real (R$)", "Acordo predito (R$)", "Erro (R$)"]:
                detail[c] = detail[c].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))
            st.dataframe(detail, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# PARTE 3: SIMULADOR DE ACORDO
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🔮 Parte 3 — Simulador: prever valor de acordo para um processo")

st.caption("Insira os dados de um processo para obter a previsão do ratio e valor de acordo.")

with st.form("simulador_acordo"):
    s1, s2, s3 = st.columns(3)
    with s1:
        uf = st.selectbox("UF", sorted(df["UF"].unique()))
    with s2:
        sub = st.selectbox("Sub-assunto", sorted(df["Sub-assunto"].unique()))
    with s3:
        valor_causa = st.number_input("Valor da causa (R$)", min_value=100.0,
                                       value=15000.0, step=500.0)

    st.markdown("**Subsídios disponíveis:**")
    sub_cols = st.columns(3)
    subsidios_vals = {}
    for i, s in enumerate(SUBSIDIOS):
        with sub_cols[i % 3]:
            subsidios_vals[s] = st.checkbox(s, value=False)

    submitted = st.form_submit_button("🔮 Prever valor do acordo", type="primary")

if submitted:
    # Identificar tribunal
    tribunal_map = df.groupby("UF")["tribunal_sigla"].first().to_dict()
    tribunal = tribunal_map.get(uf, "TJ")

    dados = {
        "UF": uf,
        "Sub-assunto": sub,
        "tribunal_sigla": tribunal,
        **{s: int(v) for s, v in subsidios_vals.items()},
        "num_subsidios": sum(subsidios_vals.values()),
    }

    pred = predict_acordo(acordo_bundle, dados, valor_causa)

    st.markdown("---")
    st.markdown("### 📊 Resultado da previsão")

    r1, r2, r3 = st.columns(3)
    r1.metric("Ratio previsto (mediana)", f"{pred['ratio_median']:.1%}")
    r2.metric("Faixa P25 — P75",
              f"{pred['ratio_p25']:.1%} — {pred['ratio_p75']:.1%}")
    r3.metric("Peso KNN / Regressão",
              f"{pred['knn_weight']:.0%} / {pred['reg_weight']:.0%}")

    v1, v2, v3 = st.columns(3)
    v1.metric("💰 Valor de acordo sugerido",
              f"R$ {pred['valor_acordo_median']:,.0f}".replace(",", "."))
    v2.metric("Faixa P25",
              f"R$ {pred['valor_acordo_p25']:,.0f}".replace(",", "."))
    v3.metric("Faixa P75",
              f"R$ {pred['valor_acordo_p75']:,.0f}".replace(",", "."))

    # Gauge visual
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pred["ratio_median"] * 100,
        title={"text": "Ratio acordo/causa previsto (%)"},
        gauge={
            "axis": {"range": [0, 50]},
            "bar": {"color": "#2ecc71"},
            "steps": [
                {"range": [0, pred["ratio_p25"] * 100], "color": "#d5f5e3"},
                {"range": [pred["ratio_p25"] * 100, pred["ratio_p75"] * 100], "color": "#82e0aa"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 2},
                "thickness": 0.75,
                "value": pred["ratio_median"] * 100,
            },
        },
    ))
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

    with st.expander("🔍 Detalhes dos vizinhos KNN"):
        st.markdown(f"**UFs dos vizinhos:** {pred['neighbors_ufs']}")
        st.markdown(f"**Sub-assuntos dos vizinhos:** {pred['neighbors_subs']}")
        st.markdown(f"**Ratios dos vizinhos:** {[f'{r:.1%}' for r in pred['neighbors_ratios']]}")
        st.markdown(f"**Distância média:** {pred['knn_mean_dist']:.4f}")
