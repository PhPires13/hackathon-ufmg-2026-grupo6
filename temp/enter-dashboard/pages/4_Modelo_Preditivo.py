"""Página 4 — Modelo preditivo (Logistic + RF) com SHAP."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import shap

from src.data_loader import load_data, render_sidebar_filters, SUBSIDIOS
from src.modeling import train_model, compute_shap

st.set_page_config(page_title="Modelo Preditivo", page_icon="🤖", layout="wide")

df = load_data()
render_sidebar_filters(df)

st.title("🤖 Modelo Preditivo — O que mais pesa no resultado?")
st.caption(
    "Treinamos modelos de classificação para prever *Êxito* (banco não é condenado). "
    "Os coeficientes e a importância de features respondem, em conjunto, qual variável "
    "mais influencia o desfecho."
)

# Nota: filtros não afetam o modelo (treino único na base completa para estabilidade)
st.info(
    "⚙️ O modelo é treinado na base completa (60k) independentemente dos filtros da sidebar — "
    "assim as métricas ficam estáveis. Use a seção 'Explicar caso individual' abaixo "
    "para selecionar um processo específico."
)

tipo = st.radio(
    "Modelo:", ["Random Forest (recomendado)", "Logistic Regression"],
    horizontal=True,
)
model_kind = "rf" if "Random" in tipo else "logistic"

bundle = train_model(df_hash=len(df), model_kind=model_kind)
m = bundle.metrics

# ======================== Métricas ========================
st.subheader("📏 Desempenho no conjunto de teste (20% hold-out estratificado)")
c1, c2, c3 = st.columns(3)
c1.metric("Accuracy", f"{m['accuracy']:.1%}")
c2.metric("ROC AUC", f"{m['roc_auc']:.3f}")
c3.metric("N (teste)", f"{len(bundle.y_test):,}".replace(",", "."))

rep = m["report"]
rep_df = pd.DataFrame(rep).T[["precision", "recall", "f1-score", "support"]].round(3)
st.dataframe(rep_df, use_container_width=True)

# Matriz confusão
cm = m["confusion"]
cm_df = pd.DataFrame(cm, index=["Real: Não êxito", "Real: Êxito"],
                     columns=["Pred: Não êxito", "Pred: Êxito"])
fig = px.imshow(cm_df, text_auto=True, color_continuous_scale="Blues",
                title="Matriz de confusão")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================== Feature importance ========================
st.subheader("🎯 Importância das features")
if model_kind == "rf":
    clf = bundle.pipeline.named_steps["clf"]
    importances = pd.DataFrame({
        "feature": bundle.feature_names,
        "importance": clf.feature_importances_,
    }).sort_values("importance", ascending=True).tail(25)
    fig = px.bar(importances, x="importance", y="feature", orientation="h",
                 title="Top 25 features (Random Forest)")
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)
else:
    clf = bundle.pipeline.named_steps["clf"]
    coefs = pd.DataFrame({
        "feature": bundle.feature_names,
        "coef": clf.coef_[0],
    })
    coefs["abs"] = coefs["coef"].abs()
    coefs = coefs.sort_values("abs", ascending=True).tail(25)
    coefs["effect"] = coefs["coef"].map(lambda x: "Favorece Êxito" if x > 0 else "Favorece Não-êxito")
    fig = px.bar(coefs, x="coef", y="feature", color="effect",
                 orientation="h",
                 color_discrete_map={"Favorece Êxito": "#2ecc71", "Favorece Não-êxito": "#e74c3c"},
                 title="Top 25 coeficientes da Logistic Regression")
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================== SHAP ========================
st.subheader("🧠 SHAP — Explicabilidade global e local")
st.caption(
    "SHAP decompõe cada predição em contribuições por feature. O gráfico de barras mostra "
    "a **importância média absoluta** de cada feature; o beeswarm mostra o **sentido** "
    "(valores altos da feature empurram para Êxito ou Não-êxito)."
)

with st.spinner("Calculando SHAP (pode levar 20-40s)..."):
    sv, X_t, feat_names, X_sample = compute_shap(bundle, max_samples=500)

col_a, col_b = st.columns(2)
with col_a:
    mean_abs = np.abs(sv).mean(axis=0)
    shap_imp = pd.DataFrame({"feature": feat_names, "mean_abs_shap": mean_abs})
    shap_imp = shap_imp.sort_values("mean_abs_shap", ascending=True).tail(20)
    fig = px.bar(shap_imp, x="mean_abs_shap", y="feature", orientation="h",
                 title="SHAP — Top 20 features por |impacto médio|")
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.caption("**Beeswarm SHAP** (matplotlib) — distribuição de contribuições por feature")
    fig2, ax = plt.subplots(figsize=(8, 7))
    shap.summary_plot(sv, X_t, feature_names=feat_names, show=False, max_display=20)
    st.pyplot(fig2, clear_figure=True)

st.divider()

# ======================== Explicar caso individual ========================
st.subheader("🔍 Explicar um caso individual")
numeros = sorted(df["Número do processo"].sample(200, random_state=1).tolist())
n_sel = st.selectbox("Selecione um número de processo (amostra de 200):", numeros)

if n_sel:
    caso = df[df["Número do processo"] == n_sel].iloc[0]
    cA, cB, cC = st.columns(3)
    cA.metric("UF", caso["UF"])
    cB.metric("Sub-assunto", caso["Sub-assunto"])
    cC.metric("Valor da causa", f"R$ {caso['Valor da causa']:,.0f}".replace(",", "."))

    cD, cE, cF = st.columns(3)
    cD.metric("Resultado real", caso["Resultado micro"])
    cE.metric("Qtd subsídios", int(caso["num_subsidios"]))
    cF.metric("Condenação real", f"R$ {caso['Valor da condenação/indenização']:,.0f}".replace(",", "."))

    st.markdown("**Subsídios disponíveis neste caso:**")
    subs_presentes = [s for s in SUBSIDIOS if caso[s] == 1]
    subs_ausentes = [s for s in SUBSIDIOS if caso[s] == 0]
    st.write("✅ Presentes:", ", ".join(subs_presentes) if subs_presentes else "_nenhum_")
    st.write("❌ Ausentes:", ", ".join(subs_ausentes) if subs_ausentes else "_nenhum_")

    # Predição
    X_one = caso[["UF", "Sub-assunto", "tribunal_sigla"] + SUBSIDIOS +
                 ["num_subsidios", "Valor da causa"]].to_frame().T
    X_one["Valor da causa"] = np.log1p(X_one["Valor da causa"].astype(float))
    proba = bundle.pipeline.predict_proba(X_one)[0, 1]
    st.markdown(f"### 🎯 Probabilidade de ÊXITO prevista: **{proba:.1%}**")

    # Waterfall SHAP
    with st.spinner("Gerando waterfall..."):
        pre = bundle.pipeline.named_steps["pre"]
        clf = bundle.pipeline.named_steps["clf"]
        X_one_t = pre.transform(X_one)
        if model_kind == "rf":
            exp = shap.TreeExplainer(clf)
            sv_one = exp.shap_values(X_one_t)
            if isinstance(sv_one, list):
                sv_one = sv_one[1]
            elif sv_one.ndim == 3:
                sv_one = sv_one[:, :, 1]
            base_val = exp.expected_value
            if isinstance(base_val, (list, np.ndarray)) and len(np.atleast_1d(base_val)) > 1:
                base_val = base_val[1]
        else:
            exp = shap.LinearExplainer(clf, pre.transform(bundle.X_train.sample(500, random_state=0)))
            sv_one = exp.shap_values(X_one_t)
            base_val = exp.expected_value

        explanation = shap.Explanation(
            values=sv_one[0], base_values=float(np.atleast_1d(base_val)[0]),
            data=X_one_t[0], feature_names=feat_names,
        )
        fig3, ax = plt.subplots(figsize=(9, 6))
        shap.plots.waterfall(explanation, max_display=15, show=False)
        st.pyplot(fig3, clear_figure=True)
