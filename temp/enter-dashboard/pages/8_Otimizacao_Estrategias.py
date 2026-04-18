"""Página 8 — Otimização de Estratégias de Acordo.

Testa diferentes estratégias e combinações para proposta de acordo,
comparando: (1) erro vs condenação real, (2) impacto financeiro.
"""
import itertools
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters, SUBSIDIOS
from src.modeling import train_model
from src.modeling_regression import (
    train_regression_model, _add_financial_features, CATEGORICAL_FEATS,
)

st.set_page_config(page_title="Otimização de Estratégias", page_icon="🔬", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("🔬 Otimização de Estratégias de Acordo")
st.caption(
    "Compara diferentes regras de decisão para proposta de acordo, "
    "avaliando erro vs condenação real e impacto financeiro líquido."
)

if len(filtered) < 100:
    st.warning("Base filtrada muito pequena para análise confiável.")
    st.stop()

# ── Treinar modelos ──
bundle = train_model(df_hash=len(df), model_kind="rf")
reg_bundle = train_regression_model(df_hash=len(df))

# ══════════════════════════════════════════════════════════════════════
# PREPARAÇÃO DOS DADOS (apenas test set — 20%)
# ══════════════════════════════════════════════════════════════════════

# Filtrar apenas dados de TESTE
test_indices = bundle.test_indices
if test_indices is not None:
    valid_test = filtered.index.intersection(test_indices)
    filtered_test = filtered.loc[valid_test]
    st.info(f"🧪 Avaliando apenas os **{len(filtered_test):,}** processos do **test set (20%)**.")
else:
    filtered_test = filtered

if len(filtered_test) < 50:
    st.warning("Poucos processos no test set com os filtros atuais.")
    st.stop()

# Predições de classificação
X_cls = filtered_test[["UF", "Sub-assunto", "tribunal_sigla"] + SUBSIDIOS +
                 ["num_subsidios", "Valor da causa"]].copy()
X_cls["Valor da causa"] = np.log1p(X_cls["Valor da causa"])
y_real = filtered_test["sucesso"].values
proba_exito = bundle.pipeline.predict_proba(X_cls)[:, 1]
proba_derrota = 1 - proba_exito

# Predições de regressão para TODOS os processos do test set
all_feats = CATEGORICAL_FEATS + reg_bundle.numeric_feats
filtered_fe = _add_financial_features(filtered_test.copy())
X_reg_all = filtered_fe[all_feats]

pred_cond = reg_bundle.pipeline_median.predict(X_reg_all)
pred_cond = np.clip(pred_cond, 0, filtered_test["Valor da causa"].values)

cond_real_col = filtered_test["Valor da condenação/indenização"].values
vc_col = filtered_test["Valor da causa"].values
sucesso_col = filtered_test["sucesso"].values

# Medianas históricas por sub-assunto (calculadas na base completa para referência)
mediana_sub = (filtered[filtered["sucesso"] == 0]
               .groupby("Sub-assunto")["Valor da condenação/indenização"]
               .median().to_dict())

# Ratio histórico cond/causa por sub-assunto (base completa)
ratio_sub = {}
for sub in filtered["Sub-assunto"].unique():
    sub_data = filtered[(filtered["Sub-assunto"] == sub) & (filtered["sucesso"] == 0)]
    if len(sub_data) > 0:
        r = (sub_data["Valor da condenação/indenização"] /
             sub_data["Valor da causa"].replace(0, np.nan)).dropna()
        ratio_sub[sub] = r.median() if len(r) > 0 else 0.5
    else:
        ratio_sub[sub] = 0.5

sub_assunto_col = filtered_test["Sub-assunto"].values


# ══════════════════════════════════════════════════════════════════════
# DEFINIÇÃO DAS ESTRATÉGIAS
# ══════════════════════════════════════════════════════════════════════

def simular_estrategia(
    nome: str,
    threshold: float = 0.5,
    multiplicador_acordo: float = 0.95,
    ponderar_prob: bool = False,
    cap_mediana_sub: bool = False,
    usar_ratio: bool = False,
) -> dict:
    """Simula uma estratégia de decisão e retorna métricas."""

    # Decisão: propor acordo se prob_derrota >= (1 - threshold)
    propoe_acordo = proba_derrota >= (1 - threshold)

    # Calcular valor do acordo proposto
    if usar_ratio:
        # Usar ratio histórico em vez de predição absoluta
        estimativa = np.array([
            vc_col[i] * ratio_sub.get(sub_assunto_col[i], 0.5)
            for i in range(len(sucesso_col))
        ])
    else:
        estimativa = pred_cond.copy()

    if cap_mediana_sub:
        # Limitar estimativa à mediana histórica do sub-assunto
        cap_vals = np.array([
            mediana_sub.get(sub_assunto_col[i], estimativa[i])
            for i in range(len(sucesso_col))
        ])
        estimativa = np.minimum(estimativa, cap_vals)

    valor_acordo = estimativa * multiplicador_acordo
    if ponderar_prob:
        valor_acordo = valor_acordo * proba_derrota

    valor_acordo = np.clip(valor_acordo, 0, vc_col)

    # ── Calcular gasto por processo ──
    gasto_por_processo = np.zeros(len(sucesso_col))

    for i in range(len(sucesso_col)):
        if propoe_acordo[i]:
            # Modelo sugere acordo
            if sucesso_col[i] == 0:
                # Caso real era Não Êxito → acordo (acerto na decisão)
                gasto_por_processo[i] = valor_acordo[i]
            else:
                # Caso real era Êxito → acordo desnecessário (FN)
                gasto_por_processo[i] = valor_acordo[i]
        else:
            # Modelo sugere contestar
            if sucesso_col[i] == 0:
                # Caso real era Não Êxito → paga condenação integral (FP)
                gasto_por_processo[i] = cond_real_col[i]
            else:
                # Caso real era Êxito → ganha (TP)
                gasto_por_processo[i] = 0

    gasto_total = gasto_por_processo.sum()

    # ── Erro na estimativa de condenação (apenas casos realmente perdidos) ──
    mask_lost = sucesso_col == 0
    mask_lost_cond = mask_lost & (cond_real_col > 0)

    if mask_lost_cond.sum() > 0:
        erro_acordo_vs_real = np.abs(valor_acordo[mask_lost_cond] - cond_real_col[mask_lost_cond])
        erro_pct_acordo = np.where(
            cond_real_col[mask_lost_cond] > 0,
            erro_acordo_vs_real / cond_real_col[mask_lost_cond] * 100, 0
        )
        mae_acordo = erro_acordo_vs_real.mean()
        mape_acordo = erro_pct_acordo.mean()
        mediana_erro_acordo = np.median(erro_pct_acordo)

        # Direção do erro: superestimou ou subestimou?
        superestimou = (valor_acordo[mask_lost_cond] > cond_real_col[mask_lost_cond]).mean()
    else:
        mae_acordo = 0
        mape_acordo = 0
        mediana_erro_acordo = 0
        superestimou = 0

    # ── Contagens ──
    n_acordos_propostos = propoe_acordo.sum()
    n_acordos_acertos = (propoe_acordo & (sucesso_col == 0)).sum()  # TN
    n_fn = (propoe_acordo & (sucesso_col == 1)).sum()               # FN
    n_fp = (~propoe_acordo & (sucesso_col == 0)).sum()              # FP
    n_tp = (~propoe_acordo & (sucesso_col == 1)).sum()              # TP

    custo_fn = gasto_por_processo[propoe_acordo & (sucesso_col == 1)].sum()
    custo_fp = gasto_por_processo[~propoe_acordo & (sucesso_col == 0)].sum()
    custo_acordos_corretos = gasto_por_processo[propoe_acordo & (sucesso_col == 0)].sum()

    gasto_real = cond_real_col[sucesso_col == 0].sum()
    economia = gasto_real - gasto_total
    economia_pct = (economia / gasto_real * 100) if gasto_real > 0 else 0

    return {
        "Estratégia": nome,
        "Threshold": threshold,
        "Gasto real (R$)": gasto_real,
        "Gasto modelo (R$)": gasto_total,
        "Economia (R$)": economia,
        "Economia (%)": economia_pct,
        "MAE acordo vs real": mae_acordo,
        "MAPE acordo vs real (%)": mape_acordo,
        "Mediana erro (%)": mediana_erro_acordo,
        "% superestimou": superestimou * 100,
        "Acordos propostos": n_acordos_propostos,
        "Acordos corretos (TN)": n_acordos_acertos,
        "Falsos Negativos (FN)": n_fn,
        "Falsos Positivos (FP)": n_fp,
        "Custo FN (R$)": custo_fn,
        "Custo FP (R$)": custo_fp,
        "Custo acordos corretos (R$)": custo_acordos_corretos,
    }


# ══════════════════════════════════════════════════════════════════════
# EXECUÇÃO DAS ESTRATÉGIAS
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("⚙️ Testando estratégias individuais e combinações")

with st.spinner("Simulando todas as estratégias..."):
    resultados = []

    # ── Estratégias individuais ──
    resultados.append(simular_estrategia(
        "① Baseline (acordo = est × 0.95)", multiplicador_acordo=0.95))

    resultados.append(simular_estrategia(
        "② Prob-weighted (acordo = est × prob × 0.95)",
        ponderar_prob=True, multiplicador_acordo=0.95))

    resultados.append(simular_estrategia(
        "③ Threshold 0.6", threshold=0.4))

    resultados.append(simular_estrategia(
        "④ Threshold 0.7", threshold=0.3))

    resultados.append(simular_estrategia(
        "⑤ Cap mediana sub-assunto", cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑥ Ratio histórico (cond/causa)", usar_ratio=True))

    resultados.append(simular_estrategia(
        "⑦ Multiplicador 0.70", multiplicador_acordo=0.70))

    # ── Combinações ──
    resultados.append(simular_estrategia(
        "⑧ Prob + Thresh 0.6",
        ponderar_prob=True, threshold=0.4))

    resultados.append(simular_estrategia(
        "⑨ Prob + Thresh 0.7",
        ponderar_prob=True, threshold=0.3))

    resultados.append(simular_estrategia(
        "⑩ Prob + Cap sub",
        ponderar_prob=True, cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑪ Prob + Ratio",
        ponderar_prob=True, usar_ratio=True))

    resultados.append(simular_estrategia(
        "⑫ Thresh 0.6 + Cap sub",
        threshold=0.4, cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑬ Thresh 0.7 + Cap sub",
        threshold=0.3, cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑭ Ratio + Thresh 0.6",
        usar_ratio=True, threshold=0.4))

    resultados.append(simular_estrategia(
        "⑮ Prob + Thresh 0.6 + Cap",
        ponderar_prob=True, threshold=0.4, cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑯ Prob + Thresh 0.7 + Cap",
        ponderar_prob=True, threshold=0.3, cap_mediana_sub=True))

    resultados.append(simular_estrategia(
        "⑰ Prob + Ratio + Thresh 0.6",
        ponderar_prob=True, usar_ratio=True, threshold=0.4))

    resultados.append(simular_estrategia(
        "⑱ Prob + Ratio + Thresh 0.7",
        ponderar_prob=True, usar_ratio=True, threshold=0.3))

    resultados.append(simular_estrategia(
        "⑲ Mult 0.70 + Thresh 0.6",
        multiplicador_acordo=0.70, threshold=0.4))

    resultados.append(simular_estrategia(
        "⑳ Prob + Mult 0.70 + Thresh 0.6",
        ponderar_prob=True, multiplicador_acordo=0.70, threshold=0.4))

df_res = pd.DataFrame(resultados)

# ══════════════════════════════════════════════════════════════════════
# RANKING
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🏆 Ranking das estratégias")

# Ordenar por economia
df_rank = df_res.sort_values("Economia (%)", ascending=False).reset_index(drop=True)
df_rank.index += 1
df_rank.index.name = "Rank"

# Formato para exibição
def fmt(v):
    if abs(v) >= 1e6:
        return f"R$ {v/1e6:,.1f}mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_show = df_rank[["Estratégia", "Economia (%)", "MAPE acordo vs real (%)",
                    "Mediana erro (%)", "% superestimou",
                    "Falsos Negativos (FN)", "Falsos Positivos (FP)"]].copy()
df_show["Economia (%)"] = df_show["Economia (%)"].map(lambda x: f"{x:+.1f}%")
df_show["MAPE acordo vs real (%)"] = df_show["MAPE acordo vs real (%)"].map(lambda x: f"{x:.1f}%")
df_show["Mediana erro (%)"] = df_show["Mediana erro (%)"].map(lambda x: f"{x:.1f}%")
df_show["% superestimou"] = df_show["% superestimou"].map(lambda x: f"{x:.0f}%")

st.dataframe(df_show, use_container_width=True)

st.caption(
    "**Economia (%):** positivo = modelo economiza vs realidade. "
    "**MAPE:** erro percentual médio do acordo vs condenação real. "
    "**Mediana erro:** metade dos casos tem erro abaixo desse valor. "
    "**% superestimou:** em quantos % dos casos o acordo sugerido é maior que a condenação real."
)

# ══════════════════════════════════════════════════════════════════════
# GRÁFICOS COMPARATIVOS
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("📊 Comparações visuais")

# Gráfico 1: Economia vs MAPE (scatter — queremos alto à esquerda e embaixo)
fig1 = px.scatter(
    df_rank, x="MAPE acordo vs real (%)", y="Economia (%)",
    text="Estratégia", size="Acordos propostos",
    color="Economia (%)", color_continuous_scale="RdYlGn",
    title="Trade-off: Economia (%) vs Erro no valor (MAPE)",
    hover_data={"Falsos Negativos (FN)": True, "Falsos Positivos (FP)": True},
)
fig1.update_traces(textposition="top center", textfont_size=8)
fig1.update_layout(height=550)
fig1.add_hline(y=0, line_dash="dash", line_color="red",
               annotation_text="Break-even (sem economia)")
st.plotly_chart(fig1, use_container_width=True)
st.caption("Ideal: ponto no canto **superior esquerdo** (alta economia + baixo erro).")

# Gráfico 2: Barras comparativas de gasto
fig2 = go.Figure()
fig2.add_bar(
    x=df_rank["Estratégia"], y=df_rank["Custo acordos corretos (R$)"],
    name="Acordos corretos", marker_color="#2ecc71",
)
fig2.add_bar(
    x=df_rank["Estratégia"], y=df_rank["Custo FP (R$)"],
    name="Condenações (FP)", marker_color="#e74c3c",
)
fig2.add_bar(
    x=df_rank["Estratégia"], y=df_rank["Custo FN (R$)"],
    name="Acordos desnecessários (FN)", marker_color="#f39c12",
)
fig2.add_hline(y=df_rank["Gasto real (R$)"].iloc[0], line_dash="dash",
               line_color="black", annotation_text="Gasto real (sem modelo)")
fig2.update_layout(
    barmode="stack", title="Composição do gasto por estratégia",
    yaxis_title="Valor (R$)", height=500,
    xaxis_tickangle=-45, legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig2, use_container_width=True)

# Gráfico 3: Erro (MAPE + Mediana) por estratégia
fig3 = go.Figure()
fig3.add_bar(x=df_rank["Estratégia"], y=df_rank["MAPE acordo vs real (%)"],
             name="MAPE (%)", marker_color="#3498db")
fig3.add_bar(x=df_rank["Estratégia"], y=df_rank["Mediana erro (%)"],
             name="Mediana erro (%)", marker_color="#9b59b6")
fig3.update_layout(
    barmode="group", title="Erro na estimativa de condenação por estratégia",
    yaxis_title="Erro (%)", height=450, xaxis_tickangle=-45,
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig3, use_container_width=True)

# Gráfico 4: FN vs FP por estratégia
fig4 = go.Figure()
fig4.add_bar(x=df_rank["Estratégia"], y=df_rank["Falsos Negativos (FN)"],
             name="FN (acordos desnecessários)", marker_color="#f39c12")
fig4.add_bar(x=df_rank["Estratégia"], y=df_rank["Falsos Positivos (FP)"],
             name="FP (condenações pagas)", marker_color="#e74c3c")
fig4.update_layout(
    barmode="group", title="Trade-off: Falsos Negativos vs Falsos Positivos",
    yaxis_title="Nº processos", height=400, xaxis_tickangle=-45,
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# MELHOR ESTRATÉGIA
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🥇 Melhor estratégia")

# Melhor por economia
best_econ = df_rank.iloc[0]
# Melhor por MAPE (menor erro)
best_mape = df_rank.loc[df_rank["MAPE acordo vs real (%)"].idxmin()]
# Melhor "balanceada" (normalizar economia e MAPE, maximizar score)
df_rank["score"] = (
    df_rank["Economia (%)"] / df_rank["Economia (%)"].abs().max() * 50
    - df_rank["MAPE acordo vs real (%)"] / df_rank["MAPE acordo vs real (%)"].max() * 50
)
best_balanced = df_rank.loc[df_rank["score"].idxmax()]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 💰 Maior economia")
    st.metric(best_econ["Estratégia"], f"{best_econ['Economia (%)']:+.1f}%")
    st.caption(f"MAPE: {best_econ['MAPE acordo vs real (%)']:.1f}% | "
               f"FN: {best_econ['Falsos Negativos (FN)']:,} | "
               f"FP: {best_econ['Falsos Positivos (FP)']:,}")

with col2:
    st.markdown("#### 🎯 Menor erro (MAPE)")
    st.metric(best_mape["Estratégia"], f"MAPE {best_mape['MAPE acordo vs real (%)']:.1f}%")
    st.caption(f"Economia: {best_mape['Economia (%)']:+.1f}% | "
               f"FN: {best_mape['Falsos Negativos (FN)']:,} | "
               f"FP: {best_mape['Falsos Positivos (FP)']:,}")

with col3:
    st.markdown("#### ⚖️ Melhor balanceada")
    st.metric(best_balanced["Estratégia"],
              f"{best_balanced['Economia (%)']:+.1f}% econ / "
              f"{best_balanced['MAPE acordo vs real (%)']:.1f}% erro")
    st.caption(f"FN: {best_balanced['Falsos Negativos (FN)']:,} | "
               f"FP: {best_balanced['Falsos Positivos (FP)']:,}")

# Tabela completa detalhada
with st.expander("📋 Tabela completa com todos os detalhes"):
    df_full = df_rank.copy()
    for col in ["Gasto real (R$)", "Gasto modelo (R$)", "Economia (R$)",
                "Custo FN (R$)", "Custo FP (R$)", "Custo acordos corretos (R$)"]:
        df_full[col] = df_full[col].map(fmt)
    df_full["MAE acordo vs real"] = df_full["MAE acordo vs real"].map(
        lambda x: f"R$ {x:,.0f}".replace(",", "."))
    st.dataframe(df_full.drop(columns=["score"], errors="ignore"),
                 use_container_width=True)
