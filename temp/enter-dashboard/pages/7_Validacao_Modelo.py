"""Página 7 — Validação do Modelo: análise de erro na classificação e na estimativa de condenação."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_data, render_sidebar_filters, apply_sidebar_filters, SUBSIDIOS
from src.modeling import train_model
from src.modeling_regression import (
    train_regression_model, predict_conviction, _add_financial_features,
    CATEGORICAL_FEATS,
)

st.set_page_config(page_title="Validação do Modelo", page_icon="🧪", layout="wide")

df = load_data()
render_sidebar_filters(df)
filtered = apply_sidebar_filters(df)

st.title("🧪 Validação do Modelo")
st.caption(
    "Análise de erro do modelo de classificação (êxito/não êxito) e do modelo de "
    "regressão (valor de condenação), testados contra o banco de dados real."
)

if len(filtered) == 0:
    st.warning("Nenhum processo atende aos filtros.")
    st.stop()

# ── Treinar modelos ──
bundle = train_model(df_hash=len(df), model_kind="rf")
reg_bundle = train_regression_model(df_hash=len(df))

# ══════════════════════════════════════════════════════════════════════
# PARTE 1: CLASSIFICAÇÃO (Êxito / Não Êxito)
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("📊 Parte 1 — Erro na classificação (Êxito vs Não Êxito)")

# Filtrar apenas dados de TESTE (20% que o modelo nunca viu)
test_indices = bundle.test_indices
if test_indices is not None:
    # Interseção entre índices de teste e a base filtrada
    valid_test = filtered.index.intersection(test_indices)
    filtered_test = filtered.loc[valid_test]
    st.info(f"🧪 Avaliando apenas os **{len(filtered_test):,}** processos do **test set (20%)** "
            f"— dados que o modelo **nunca viu** durante o treinamento.")
else:
    filtered_test = filtered
    st.warning("⚠️ Índices de teste não disponíveis. Usando toda a base filtrada.")

if len(filtered_test) < 50:
    st.warning("Poucos processos no test set com os filtros atuais.")
    st.stop()

# Predizer no test set
X_cls = filtered_test[["UF", "Sub-assunto", "tribunal_sigla"] + SUBSIDIOS +
                 ["num_subsidios", "Valor da causa"]].copy()
X_cls["Valor da causa"] = np.log1p(X_cls["Valor da causa"])
y_real = filtered_test["sucesso"].values

proba = bundle.pipeline.predict_proba(X_cls)[:, 1]
y_pred = (proba >= 0.5).astype(int)

# Métricas gerais
n_total = len(y_real)
acertos = (y_pred == y_real).sum()
accuracy = acertos / n_total

tp = ((y_pred == 1) & (y_real == 1)).sum()  # Previu êxito, foi êxito
tn = ((y_pred == 0) & (y_real == 0)).sum()  # Previu não êxito, foi não êxito
fp = ((y_pred == 1) & (y_real == 0)).sum()  # Previu êxito, foi não êxito (ERRO CRÍTICO)
fn = ((y_pred == 0) & (y_real == 1)).sum()  # Previu não êxito, foi êxito

precision_exito = tp / (tp + fp) if (tp + fp) > 0 else 0
recall_exito = tp / (tp + fn) if (tp + fn) > 0 else 0
precision_nao = tn / (tn + fn) if (tn + fn) > 0 else 0
recall_nao = tn / (tn + fp) if (tn + fp) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Processos analisados", f"{n_total:,}".replace(",", "."))
c2.metric("Acurácia geral", f"{accuracy:.1%}")
c3.metric("Acertos", f"{acertos:,}".replace(",", "."))
c4.metric("Erros", f"{n_total - acertos:,}".replace(",", "."))

st.markdown("---")

# Matriz de confusão
col_cm, col_detail = st.columns([1, 1.2])

with col_cm:
    cm = pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["Real: Não êxito", "Real: Êxito"],
        columns=["Pred: Não êxito", "Pred: Êxito"],
    )
    fig_cm = px.imshow(cm, text_auto=True, color_continuous_scale="Blues",
                       title="Matriz de Confusão")
    st.plotly_chart(fig_cm, use_container_width=True)

with col_detail:
    st.markdown("#### Detalhamento dos erros")
    st.markdown(f"""
| Métrica | Êxito | Não Êxito |
|---------|-------|-----------|
| **Precision** | {precision_exito:.1%} | {precision_nao:.1%} |
| **Recall** | {recall_exito:.1%} | {recall_nao:.1%} |
| **Verdadeiros** | {tp:,} (TP) | {tn:,} (TN) |
| **Falsos** | {fp:,} (FP) | {fn:,} (FN) |
""")
    st.warning(
        f"⚠️ **{fp:,} processos** foram classificados como Êxito mas eram **Não Êxito** (Falso Positivo). "
        "Nesses casos, o banco não proporia acordo e acabaria sendo condenado — "
        "esse é o tipo de erro mais custoso."
    )

# Erro por UF
st.markdown("---")
st.markdown("#### Acurácia por UF")
res = filtered_test.copy()
res["pred"] = y_pred
res["acertou"] = (res["pred"] == res["sucesso"]).astype(int)
res["falso_positivo"] = ((res["pred"] == 1) & (res["sucesso"] == 0)).astype(int)

uf_acc = (res.groupby("UF")
          .agg(n=("acertou", "size"),
               acuracia=("acertou", "mean"),
               taxa_fp=("falso_positivo", "mean"))
          .reset_index()
          .sort_values("acuracia"))

fig_uf = px.bar(uf_acc, x="UF", y="acuracia",
                color="acuracia", color_continuous_scale="RdYlGn",
                hover_data={"n": True, "taxa_fp": ":.1%"},
                title="Acurácia do classificador por UF")
fig_uf.update_yaxes(tickformat=".0%", title="Acurácia")
fig_uf.update_layout(xaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_uf, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# PARTE 2: REGRESSÃO (Valor de Condenação)
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("💰 Parte 2 — Erro na estimativa de valor de condenação")
st.caption(
    "Avalia o erro do modelo de regressão em dois cenários: "
    "(A) casos que o modelo previu como Não Êxito, e "
    "(B) **casos que o modelo errou** (previu Êxito mas foi Não Êxito — Falsos Positivos), "
    "onde o banco seria surpreendido pela condenação."
)

# Pegar apenas casos que foram realmente perdidos (condenação > 0)
lost_real = filtered_test[(filtered_test["sucesso"] == 0) &
                     (filtered_test["Valor da condenação/indenização"] > 0)].copy()

if len(lost_real) < 10:
    st.warning("Poucos casos perdidos para análise de regressão.")
    st.stop()

# Predizer condenação para cada caso perdido (em batches para performance)
st.info(f"Calculando estimativas de condenação para {len(lost_real):,} casos perdidos...")

all_feats = CATEGORICAL_FEATS + reg_bundle.numeric_feats
lost_fe = _add_financial_features(lost_real)
X_reg = lost_fe[all_feats]

pred_median = reg_bundle.pipeline_median.predict(X_reg)
pred_p25 = reg_bundle.pipeline_p25.predict(X_reg)
pred_p75 = reg_bundle.pipeline_p75.predict(X_reg)

# Clip ao valor da causa
vc = lost_real["Valor da causa"].values
pred_median = np.clip(pred_median, 0, vc)
pred_p25 = np.clip(pred_p25, 0, vc)
pred_p75 = np.clip(pred_p75, 0, vc)

cond_real = lost_real["Valor da condenação/indenização"].values

# Calcular erros
erro_abs = np.abs(pred_median - cond_real)
erro_pct = np.where(cond_real > 0, erro_abs / cond_real * 100, 0)
dentro_faixa = (cond_real >= pred_p25) & (cond_real <= pred_p75)

# Separar: modelo previu Não Êxito vs modelo previu Êxito (FP)
# Usar o array de predições com os índices corretos
lost_real_idx = lost_real.index
pred_map = pd.Series(y_pred, index=filtered_test.index)
pred_cls_lost = pred_map.reindex(lost_real_idx).values

mask_previu_nao_exito = pred_cls_lost == 0  # Modelo previu Não Êxito (certo)
mask_falso_positivo = pred_cls_lost == 1    # Modelo previu Êxito, mas era Não Êxito (FP)

# ── Métricas gerais ──
mae_global = erro_abs.mean()
mape_global = erro_pct.mean()
cobertura = dentro_faixa.mean()

m1, m2, m3, m4 = st.columns(4)
m1.metric("MAE global", f"R$ {mae_global:,.0f}".replace(",", "."))
m2.metric("MAPE global", f"{mape_global:.1f}%")
m3.metric("Cobertura P25-P75", f"{cobertura:.1%}")
m4.metric("Casos avaliados", f"{len(lost_real):,}".replace(",", "."))

st.markdown("---")

# ── Cenário A: Modelo previu Não Êxito (acertou a classe) ──
st.markdown("#### 🅰️ Cenário A: Modelo previu Não Êxito corretamente")
st.caption("Nesses casos, o banco proporia um acordo. O erro no valor estima quão precisa seria a proposta.")

n_a = mask_previu_nao_exito.sum()
if n_a > 0:
    mae_a = erro_abs[mask_previu_nao_exito].mean()
    mape_a = erro_pct[mask_previu_nao_exito].mean()
    cob_a = dentro_faixa[mask_previu_nao_exito].mean()
    mediana_erro_a = np.median(erro_pct[mask_previu_nao_exito])

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Casos", f"{n_a:,}".replace(",", "."))
    a2.metric("MAE", f"R$ {mae_a:,.0f}".replace(",", "."))
    a3.metric("MAPE médio", f"{mape_a:.1f}%")
    a4.metric("Cobertura P25-P75", f"{cob_a:.1%}")

    # Distribuição do erro percentual
    fig_hist_a = px.histogram(
        x=erro_pct[mask_previu_nao_exito], nbins=50,
        title="Distribuição do erro percentual (Cenário A)",
        labels={"x": "Erro percentual (%)", "y": "Frequência"},
        color_discrete_sequence=["#2ecc71"],
    )
    fig_hist_a.add_vline(x=mediana_erro_a, line_dash="dash", line_color="red",
                         annotation_text=f"Mediana: {mediana_erro_a:.1f}%")
    st.plotly_chart(fig_hist_a, use_container_width=True)
else:
    st.info("Nenhum caso neste cenário com os filtros atuais.")

# ── Cenário B: Falsos Positivos (previu Êxito, foi Não Êxito) ──
st.markdown("---")
st.markdown("#### 🅱️ Cenário B: Falsos Positivos (previu Êxito, foi Não Êxito)")
st.caption(
    "⚠️ Esses são os casos mais **perigosos**: o modelo sugeriu contestar (êxito), "
    "mas o banco perdeu. Nesse cenário, não haveria proposta de acordo e a condenação "
    "seria paga integralmente. Analisamos aqui qual teria sido a condenação real."
)

n_b = mask_falso_positivo.sum()
if n_b > 0:
    cond_fp = cond_real[mask_falso_positivo]
    pred_fp = pred_median[mask_falso_positivo]
    erro_fp = erro_pct[mask_falso_positivo]
    prejuizo_total = cond_fp.sum()
    cond_media_fp = cond_fp.mean()
    mae_b = erro_abs[mask_falso_positivo].mean()
    mape_b = erro_fp.mean()
    cob_b = dentro_faixa[mask_falso_positivo].mean()

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Casos (Falsos Positivos)", f"{n_b:,}".replace(",", "."))
    b2.metric("Prejuízo total (sem acordo)", f"R$ {prejuizo_total/1e6:,.1f} mi".replace(",", "."))
    b3.metric("Condenação média", f"R$ {cond_media_fp:,.0f}".replace(",", "."))
    b4.metric("MAPE da estimativa", f"{mape_b:.1f}%")

    b5, b6, b7 = st.columns(3)
    b5.metric("MAE", f"R$ {mae_b:,.0f}".replace(",", "."))
    b6.metric("Cobertura P25-P75", f"{cob_b:.1%}")
    b7.metric("% dos casos perdidos", f"{n_b/len(lost_real):.1%}")

    st.error(
        f"💸 Se o modelo fosse seguido cegamente, **{n_b:,} processos** não receberiam "
        f"proposta de acordo e o banco pagaria **R$ {prejuizo_total/1e6:,.1f} milhões** "
        f"em condenações que poderiam ter sido negociadas."
    )

    # Distribuição do erro
    fig_hist_b = px.histogram(
        x=erro_fp, nbins=30,
        title="Distribuição do erro percentual (Falsos Positivos)",
        labels={"x": "Erro percentual (%)", "y": "Frequência"},
        color_discrete_sequence=["#e74c3c"],
    )
    fig_hist_b.add_vline(x=np.median(erro_fp), line_dash="dash", line_color="black",
                         annotation_text=f"Mediana: {np.median(erro_fp):.1f}%")
    st.plotly_chart(fig_hist_b, use_container_width=True)

    # Scatter: predição vs real (FP)
    fig_sc = px.scatter(
        x=cond_fp, y=pred_fp, opacity=0.5,
        title="Falsos Positivos: Condenação real vs Estimativa do modelo",
        labels={"x": "Condenação real (R$)", "y": "Estimativa do modelo (R$)"},
        color_discrete_sequence=["#e74c3c"],
    )
    max_val = max(cond_fp.max(), pred_fp.max()) * 1.1
    fig_sc.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                     line=dict(dash="dash", color="gray"))
    fig_sc.update_layout(height=450)
    st.plotly_chart(fig_sc, use_container_width=True)
    st.caption("Pontos na diagonal = estimativa perfeita. Acima = modelo superestimou. Abaixo = subestimou.")
else:
    st.success("✅ Nenhum Falso Positivo com os filtros atuais!")

# ══════════════════════════════════════════════════════════════════════
# PARTE 3: ANÁLISE COMBINADA
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("📋 Parte 3 — Resumo consolidado e impacto financeiro")

# Scatter global: predição vs real
st.markdown("#### Condenação real vs Estimativa (todos os casos perdidos)")
fig_all = px.scatter(
    x=cond_real, y=pred_median, opacity=0.3,
    color=np.where(mask_falso_positivo, "Falso Positivo", "Previu Não Êxito"),
    color_discrete_map={"Falso Positivo": "#e74c3c", "Previu Não Êxito": "#2ecc71"},
    title="Condenação real vs Estimativa do modelo (todos os casos perdidos)",
    labels={"x": "Condenação real (R$)", "y": "Estimativa (R$)", "color": "Cenário"},
)
max_v = max(cond_real.max(), pred_median.max()) * 1.1
fig_all.add_shape(type="line", x0=0, y0=0, x1=max_v, y1=max_v,
                  line=dict(dash="dash", color="gray"))
fig_all.update_traces(marker=dict(size=4))
fig_all.update_layout(height=500)
st.plotly_chart(fig_all, use_container_width=True)

# Erro por UF (regressão)
st.markdown("#### Erro percentual médio por UF")
lost_with_errs = lost_real.copy()
lost_with_errs["erro_pct"] = erro_pct
lost_with_errs["dentro_faixa"] = dentro_faixa
lost_with_errs["fp"] = mask_falso_positivo

uf_reg = (lost_with_errs.groupby("UF")
          .agg(n=("erro_pct", "size"),
               mape=("erro_pct", "mean"),
               cobertura=("dentro_faixa", "mean"),
               n_fp=("fp", "sum"))
          .reset_index()
          .sort_values("mape", ascending=False))

fig_uf_reg = px.bar(
    uf_reg, x="UF", y="mape",
    color="cobertura", color_continuous_scale="RdYlGn",
    hover_data={"n": True, "n_fp": True, "cobertura": ":.1%"},
    title="MAPE por UF (cor = cobertura P25-P75)",
)
fig_uf_reg.update_yaxes(title="MAPE (%)")
fig_uf_reg.update_layout(xaxis={"categoryorder": "total descending"})
st.plotly_chart(fig_uf_reg, use_container_width=True)

# Tabela resumo final
st.markdown("#### Tabela resumo")
resumo = pd.DataFrame([
    {"Cenário": "A — Previu Não Êxito (correto)",
     "Casos": n_a, "MAE": f"R$ {mae_a:,.0f}" if n_a > 0 else "—",
     "MAPE": f"{mape_a:.1f}%" if n_a > 0 else "—",
     "Cobertura P25-P75": f"{cob_a:.1%}" if n_a > 0 else "—"},
    {"Cenário": "B — Falso Positivo (previu Êxito, foi Não Êxito)",
     "Casos": n_b, "MAE": f"R$ {mae_b:,.0f}" if n_b > 0 else "—",
     "MAPE": f"{mape_b:.1f}%" if n_b > 0 else "—",
     "Cobertura P25-P75": f"{cob_b:.1%}" if n_b > 0 else "—"},
    {"Cenário": "GLOBAL (todos os perdidos)",
     "Casos": len(lost_real), "MAE": f"R$ {mae_global:,.0f}",
     "MAPE": f"{mape_global:.1f}%",
     "Cobertura P25-P75": f"{cobertura:.1%}"},
])
st.dataframe(resumo, use_container_width=True, hide_index=True)

# Métricas do modelo de regressão
with st.expander("⚙️ Métricas do modelo de regressão (test set interno)"):
    rm = reg_bundle.metrics
    st.markdown(f"""
- **MAE (test set):** R$ {rm['mae']:,.0f}
- **MAPE (test set):** {rm['mape']:.1f}%
- **Cobertura P25-P75 (test set):** {rm['cobertura_p25_p75']:.1%}
- **N treino:** {rm['n_treino']:,} | **N teste:** {rm['n_teste']:,}
- **Features aceitas:** {', '.join(reg_bundle.accepted_features) or 'nenhuma extra'}
- **Features rejeitadas:** {', '.join(reg_bundle.rejected_features) or 'nenhuma'}
""")
    st.markdown("**Log de seleção iterativa de features:**")
    st.dataframe(pd.DataFrame(reg_bundle.feature_log), hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# PARTE 4: IMPACTO FINANCEIRO — MODELO vs REALIDADE
# ══════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🏦 Parte 4 — Impacto financeiro: Modelo vs Realidade")
st.caption(
    "Simulação: se o advogado tivesse seguido **todas** as sugestões do modelo, "
    "quanto o banco teria economizado? Considera que acordos são aceitos no "
    "**valor ideal sugerido** (mediana ponderada) pelo modelo."
)

# ── Gasto REAL (o que de fato aconteceu) ──
# Todos os processos não-êxito pagaram a condenação real
gasto_real_total = filtered_test.loc[filtered_test["sucesso"] == 0, "Valor da condenação/indenização"].sum()
n_perdidos_total = (filtered_test["sucesso"] == 0).sum()
n_ganhos_total = (filtered_test["sucesso"] == 1).sum()

# ── Gasto HIPOTÉTICO com o modelo (estratégia otimizada) ──
# Estratégia: Prob + Mult 0.70 + Thresh 0.6
#   - prob_derrota >= 0.6: propõe acordo (valor ideal com prob-weighting)
#   - prob_derrota < 0.6: contesta

# Probabilidades de derrota para todos os processos
proba_derrota_all = 1 - proba
propoe_acordo = proba_derrota_all >= 0.6  # Threshold otimizado

# Predições P25 e Mediana para TODOS os processos
filtered_fe = _add_financial_features(filtered_test.copy())
X_reg_filtered = filtered_fe[all_feats]
pred_p25_all = reg_bundle.pipeline_p25.predict(X_reg_filtered)
pred_p50_all = reg_bundle.pipeline_median.predict(X_reg_filtered)
pred_p25_all = np.clip(pred_p25_all, 0, filtered_test["Valor da causa"].values)
pred_p50_all = np.clip(pred_p50_all, 0, filtered_test["Valor da causa"].values)

# Calcular valor IDEAL (estratégia otimizada: Prob + Mult 0.70)
piso_all = pred_p25_all * 0.50
teto_all = pred_p50_all * 0.70
teto_all = np.maximum(teto_all, piso_all * 1.05)
ideal_base = piso_all + (teto_all - piso_all) * proba_derrota_all
ideal_all = ideal_base * proba_derrota_all  # ponderação pela prob
ideal_all = np.clip(ideal_all, piso_all * proba_derrota_all, teto_all)
ideal_all = np.clip(ideal_all, 0, filtered_test["Valor da causa"].values)

# Calcular gastos
all_lost = filtered_test[filtered_test["sucesso"] == 0].copy()
if len(all_lost) > 0:
    cond_real_all = all_lost["Valor da condenação/indenização"].values
    lost_mask = filtered_test["sucesso"] == 0
    valor_acordo = ideal_all[lost_mask.values]

    # Decisão por processo perdido: usou acordo ou não?
    propoe_lost = propoe_acordo[lost_mask.values]

    gasto_modelo = np.where(
        propoe_lost,            # Propôs acordo (prob >= 0.6)
        valor_acordo,           # Paga o valor ideal do acordo
        cond_real_all,          # Não propôs acordo → paga condenação integral
    )

    gasto_modelo_total = gasto_modelo.sum()

    # Processos que o modelo previu êxito E realmente foram êxito → custo 0

    # Processos que propôs acordo mas na verdade o banco ganharia (FN)
    all_won = filtered_test[filtered_test["sucesso"] == 1].copy()
    won_mask = filtered_test["sucesso"] == 1
    propoe_won = propoe_acordo[won_mask.values]
    n_fn = propoe_won.sum()

    if n_fn > 0:
        ideal_won = ideal_all[won_mask.values]
        ideal_fn = ideal_won[propoe_won]
        custo_acordos_desnecessarios = ideal_fn.sum()
    else:
        custo_acordos_desnecessarios = 0

    gasto_modelo_completo = gasto_modelo_total + custo_acordos_desnecessarios

    # ── Economia ──
    economia = gasto_real_total - gasto_modelo_completo
    economia_pct = (economia / gasto_real_total * 100) if gasto_real_total > 0 else 0

    # ── Exibição ──
    def fmt(v):
        if abs(v) >= 1e6:
            return f"R$ {v/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.markdown("### 💰 Comparação de gastos")

    g1, g2, g3 = st.columns(3)
    g1.metric("💸 Gasto REAL (condenações pagas)", fmt(gasto_real_total))
    g2.metric("🤖 Gasto COM o modelo", fmt(gasto_modelo_completo))

    if economia > 0:
        g3.metric("✅ Economia obtida", fmt(economia),
                  delta=f"{economia_pct:.1f}% de economia", delta_color="normal")
    else:
        g3.metric("❌ Custo adicional", fmt(abs(economia)),
                  delta=f"{abs(economia_pct):.1f}% a mais", delta_color="inverse")

    st.markdown("---")

    # Detalhamento
    st.markdown("#### 📊 Composição dos gastos com o modelo")

    n_acordos_corretos = propoe_lost.sum()  # Propôs acordo para caso perdido (acerto)
    gasto_acordos_corretos = gasto_modelo[propoe_lost].sum()

    n_fp_gastos = (~propoe_lost).sum()  # Não propôs acordo, era Não Êxito (FP)
    gasto_fp = gasto_modelo[~propoe_lost].sum()

    comp_df = pd.DataFrame([
        {"Componente": "Acordos propostos (previu Não Êxito, acertou)",
         "Nº processos": n_acordos_corretos,
         "Valor": gasto_acordos_corretos},
        {"Componente": "Condenações pagas (Falsos Positivos)",
         "Nº processos": n_fp_gastos,
         "Valor": gasto_fp},
        {"Componente": "Acordos desnecessários (Falsos Negativos)",
         "Nº processos": n_fn,
         "Valor": custo_acordos_desnecessarios},
        {"Componente": "TOTAL COM MODELO",
         "Nº processos": n_acordos_corretos + n_fp_gastos + n_fn,
         "Valor": gasto_modelo_completo},
    ])
    comp_df["Valor (R$)"] = comp_df["Valor"].map(fmt)
    st.dataframe(comp_df[["Componente", "Nº processos", "Valor (R$)"]],
                 use_container_width=True, hide_index=True)

    # ── Comparação: Acordos corretos vs Condenação real ──
    st.markdown("---")
    st.markdown("#### 🔎 Acordos corretos vs Condenação real (apenas casos que o modelo acertou)")
    st.caption(
        "Para os processos que o modelo previu corretamente como Não Êxito, "
        "compara o valor que seria pago em acordo vs o valor real da condenação."
    )

    if n_acordos_corretos > 0:
        acordo_corretos = valor_acordo[propoe_lost]
        cond_corretos = cond_real_all[propoe_lost]

        total_acordo = acordo_corretos.sum()
        total_cond = cond_corretos.sum()
        economia_acordos = total_cond - total_acordo
        economia_acordos_pct = (economia_acordos / total_cond * 100) if total_cond > 0 else 0

        acordo_medio = acordo_corretos.mean()
        cond_media = cond_corretos.mean()
        economia_media = cond_media - acordo_medio

        # Métricas
        v1, v2, v3 = st.columns(3)
        v1.metric("Total pago em acordos (modelo)", fmt(total_acordo))
        v2.metric("Total que seria pago em condenações (real)", fmt(total_cond))
        if economia_acordos > 0:
            v3.metric("Economia nos acordos corretos", fmt(economia_acordos),
                      delta=f"{economia_acordos_pct:.1f}% de economia", delta_color="normal")
        else:
            v3.metric("Custo extra nos acordos", fmt(abs(economia_acordos)),
                      delta=f"{abs(economia_acordos_pct):.1f}% a mais", delta_color="inverse")

        v4, v5, v6 = st.columns(3)
        v4.metric("Acordo médio por processo", fmt(acordo_medio))
        v5.metric("Condenação média real", fmt(cond_media))
        v6.metric("Economia média por processo", fmt(economia_media))

        # Gráfico de barras: acordo vs condenação
        fig_av = go.Figure()
        fig_av.add_bar(x=["Valor total"], y=[total_cond],
                       name="Condenação real", marker_color="#e74c3c",
                       text=[fmt(total_cond)], textposition="outside")
        fig_av.add_bar(x=["Valor total"], y=[total_acordo],
                       name="Acordo proposto (ideal)", marker_color="#2ecc71",
                       text=[fmt(total_acordo)], textposition="outside")
        fig_av.add_bar(x=["Valor médio/processo"], y=[cond_media],
                       name="Cond. média", marker_color="#e74c3c", showlegend=False,
                       text=[fmt(cond_media)], textposition="outside")
        fig_av.add_bar(x=["Valor médio/processo"], y=[acordo_medio],
                       name="Acordo médio", marker_color="#2ecc71", showlegend=False,
                       text=[fmt(acordo_medio)], textposition="outside")
        fig_av.update_layout(
            barmode="group", title="Acordos corretos: valor proposto vs condenação real",
            yaxis_title="Valor (R$)", height=400,
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_av, use_container_width=True)

        # Distribuição: diferença por processo
        diff_por_processo = cond_corretos - acordo_corretos
        pct_economizou = (diff_por_processo > 0).mean()

        st.markdown(f"**{pct_economizou:.1%}** dos acordos propostos teriam valor "
                    f"**menor** que a condenação real (economia para o banco).")

        fig_diff = px.histogram(
            x=diff_por_processo, nbins=60,
            title="Diferença por processo: Condenação real − Acordo proposto",
            labels={"x": "Condenação real − Acordo (R$)", "y": "Frequência"},
            color_discrete_sequence=["#3498db"],
        )
        fig_diff.add_vline(x=0, line_dash="dash", line_color="red",
                           annotation_text="Break-even")
        fig_diff.add_vline(x=diff_por_processo.mean(), line_dash="dash", line_color="green",
                           annotation_text=f"Média: {fmt(diff_por_processo.mean())}")
        st.plotly_chart(fig_diff, use_container_width=True)
        st.caption("Valores positivos = banco economiza com acordo. Negativos = acordo custou mais que condenação.")
    # Gráfico de barras comparativo
    fig_comp = go.Figure()
    fig_comp.add_bar(
        x=["Realidade (sem modelo)"], y=[gasto_real_total],
        name="Gasto real", marker_color="#e74c3c",
        text=[fmt(gasto_real_total)], textposition="outside",
    )
    fig_comp.add_bar(
        x=["Com modelo (acordos + FPs + FNs)"], y=[gasto_modelo_completo],
        name="Gasto com modelo", marker_color="#2ecc71",
        text=[fmt(gasto_modelo_completo)], textposition="outside",
    )
    fig_comp.update_layout(
        title="Gasto total: Realidade vs Com o modelo",
        yaxis_title="Valor (R$)", showlegend=False, height=400,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Gráfico de composição do gasto do modelo (stacked bar)
    fig_stack = go.Figure()
    fig_stack.add_bar(x=["Composição do gasto com modelo"],
                      y=[gasto_acordos_corretos], name="Acordos (acertos)",
                      marker_color="#2ecc71")
    fig_stack.add_bar(x=["Composição do gasto com modelo"],
                      y=[gasto_fp], name="Condenações (FP)",
                      marker_color="#e74c3c")
    fig_stack.add_bar(x=["Composição do gasto com modelo"],
                      y=[custo_acordos_desnecessarios], name="Acordos desnecessários (FN)",
                      marker_color="#f39c12")
    fig_stack.update_layout(barmode="stack", yaxis_title="Valor (R$)", height=400,
                            title="De onde vem o gasto quando se usa o modelo?")
    st.plotly_chart(fig_stack, use_container_width=True)

    # Resumo textual
    st.markdown("---")
    if economia > 0:
        st.success(
            f"📊 **Resumo:** Seguindo todas as sugestões do modelo, o banco gastaria "
            f"**{fmt(gasto_modelo_completo)}** em vez de **{fmt(gasto_real_total)}**, "
            f"uma economia de **{fmt(economia)} ({economia_pct:.1f}%)**.\n\n"
            f"Essa economia vem de {n_acordos_corretos:,} acordos propostos a valores "
            f"inferiores às condenações reais, descontados os custos de "
            f"{n_fp_gastos:,} Falsos Positivos (condenações pagas integralmente) e "
            f"{n_fn:,} Falsos Negativos (acordos propostos desnecessariamente)."
        )
    else:
        st.error(
            f"📊 **Resumo:** Neste cenário, o modelo geraria um custo adicional de "
            f"**{fmt(abs(economia))}**, principalmente devido a Falsos Negativos "
            f"(acordos propostos desnecessariamente em casos que o banco ganharia)."
        )

else:
    st.info("Nenhum caso perdido na base filtrada para análise financeira.")
