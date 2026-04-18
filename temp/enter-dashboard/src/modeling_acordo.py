"""Modelo de regressão para prever valor de acordo (ratio acordo/causa).

Treina em casos que finalizaram com acordo para prever o ratio
valor_acordo / valor_causa baseado em UF, Sub-assunto, subsídios, etc.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data_loader import SUBSIDIOS


CATEGORICAL_FEATS = ["UF", "Sub-assunto", "tribunal_sigla"]
BASE_NUMERIC_FEATS = SUBSIDIOS + ["num_subsidios", "log_valor_causa"]


@dataclass
class AcordoBundle:
    pipeline_median: Pipeline           # Predição do ratio mediano
    pipeline_p25: Pipeline | None       # Quantile 25
    pipeline_p75: Pipeline | None       # Quantile 75
    knn_model: NearestNeighbors | None
    knn_X: np.ndarray | None
    knn_df: pd.DataFrame | None
    preprocessor: ColumnTransformer
    numeric_feats: list[str]
    metrics: dict
    test_indices: np.ndarray | None = None


def _add_features_acordo(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona features para o modelo de acordo."""
    df = df.copy()
    df["log_valor_causa"] = np.log1p(df["Valor da causa"])

    # Médias por grupo
    uf_means = df.groupby("UF")["Valor da causa"].transform("mean")
    sub_means = df.groupby("Sub-assunto")["Valor da causa"].transform("mean")

    df["ratio_causa_uf"] = df["Valor da causa"] / uf_means.replace(0, 1)
    df["ratio_causa_sub"] = df["Valor da causa"] / sub_means.replace(0, 1)
    df["causa_x_subsidios"] = df["log_valor_causa"] * df["num_subsidios"]

    return df


def _build_preprocessor(numeric_feats: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATS),
        ("num", StandardScaler(), numeric_feats),
    ])


def _build_quantile_model(quantile: float) -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        loss="quantile", alpha=quantile,
        n_estimators=150, max_depth=4, min_samples_leaf=10,
        learning_rate=0.1, random_state=42,
    )


@st.cache_resource(show_spinner="Treinando modelo de previsão de acordo...")
def train_acordo_model(df_hash: int) -> AcordoBundle:
    """Treina modelo para prever ratio acordo/causa em casos finalizados com acordo."""
    from .data_loader import load_data
    df_full = load_data()

    # Apenas casos com Resultado micro == "Acordo"
    df_acordo = df_full[df_full["Resultado micro"] == "Acordo"].copy()

    if len(df_acordo) < 20:
        st.error("Poucos casos de acordo no banco de dados para treinar modelo.")
        st.stop()

    # Target: ratio acordo/causa
    df_acordo["ratio_acordo"] = (
        df_acordo["Valor da condenação/indenização"] /
        df_acordo["Valor da causa"].replace(0, np.nan)
    ).fillna(0)

    # Adicionar features
    df_acordo = _add_features_acordo(df_acordo)
    y = df_acordo["ratio_acordo"]

    # Features numéricas finais
    final_numeric = BASE_NUMERIC_FEATS + ["ratio_causa_uf", "ratio_causa_sub", "causa_x_subsidios"]
    all_feats = CATEGORICAL_FEATS + final_numeric

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df_acordo, y, test_size=0.2, random_state=42,
    )

    # ── Treinar modelo mediana (quantile 0.5) ──
    pre = _build_preprocessor(final_numeric)
    model_median = GradientBoostingRegressor(
        loss="quantile", alpha=0.5,
        n_estimators=150, max_depth=4, min_samples_leaf=10,
        learning_rate=0.1, random_state=42,
    )
    pipe_median = Pipeline([("pre", pre), ("reg", model_median)])
    pipe_median.fit(X_train[all_feats], y_train)

    # ── Quantile P25 ──
    pre_p25 = _build_preprocessor(final_numeric)
    pipe_p25 = Pipeline([("pre", pre_p25), ("reg", _build_quantile_model(0.25))])
    pipe_p25.fit(X_train[all_feats], y_train)

    # ── Quantile P75 ──
    pre_p75 = _build_preprocessor(final_numeric)
    pipe_p75 = Pipeline([("pre", pre_p75), ("reg", _build_quantile_model(0.75))])
    pipe_p75.fit(X_train[all_feats], y_train)

    # ── KNN para similaridade ──
    pre_knn = _build_preprocessor(final_numeric)
    pre_knn.fit(df_acordo[all_feats])
    X_knn_transformed = pre_knn.transform(df_acordo[all_feats])
    knn = NearestNeighbors(n_neighbors=min(15, len(df_acordo)), metric="euclidean")
    knn.fit(X_knn_transformed)

    # ── Métricas no test set ──
    y_pred_median = pipe_median.predict(X_test[all_feats])
    y_pred_p25 = pipe_p25.predict(X_test[all_feats])
    y_pred_p75 = pipe_p75.predict(X_test[all_feats])

    y_pred_median = np.clip(y_pred_median, 0, 1)
    y_pred_p25 = np.clip(y_pred_p25, 0, 1)
    y_pred_p75 = np.clip(y_pred_p75, 0, 1)

    mae = mean_absolute_error(y_test, y_pred_median)
    # MAPE para ratios
    mape = np.mean(np.abs(y_test - y_pred_median) / y_test.replace(0, np.nan).fillna(1)) * 100
    in_range = ((y_test.values >= y_pred_p25) & (y_test.values <= y_pred_p75)).mean()

    metrics = {
        "mae_ratio": mae,
        "mape": mape,
        "cobertura_p25_p75": in_range,
        "n_treino": len(X_train),
        "n_teste": len(X_test),
        "n_total_acordos": len(df_acordo),
        "ratio_medio_treino": y_train.mean(),
        "ratio_mediano_treino": y_train.median(),
    }

    return AcordoBundle(
        pipeline_median=pipe_median,
        pipeline_p25=pipe_p25,
        pipeline_p75=pipe_p75,
        knn_model=knn,
        knn_X=X_knn_transformed,
        knn_df=df_acordo.reset_index(drop=True),
        preprocessor=pre_knn,
        numeric_feats=final_numeric,
        metrics=metrics,
        test_indices=X_test.index.values,
    )


def predict_acordo(
    bundle: AcordoBundle,
    dados: dict,
    valor_causa: float,
    n_neighbors: int = 10,
) -> dict:
    """Prediz o ratio acordo/causa usando ensemble: regressão + KNN."""
    from .data_loader import SUBSIDIOS as SUBS

    row = {
        "UF": dados["UF"],
        "Sub-assunto": dados["Sub-assunto"],
        "tribunal_sigla": dados["tribunal_sigla"],
        **{s: dados[s] for s in SUBS},
        "num_subsidios": dados["num_subsidios"],
        "Valor da causa": valor_causa,
    }
    X_input = pd.DataFrame([row])
    X_input = _add_features_acordo(X_input)
    all_feats = CATEGORICAL_FEATS + bundle.numeric_feats

    # Predição por regressão
    pred_median = float(bundle.pipeline_median.predict(X_input[all_feats])[0])
    pred_p25 = float(bundle.pipeline_p25.predict(X_input[all_feats])[0])
    pred_p75 = float(bundle.pipeline_p75.predict(X_input[all_feats])[0])

    # Predição por KNN
    X_input_transformed = bundle.preprocessor.transform(X_input[all_feats])
    distances, indices = bundle.knn_model.kneighbors(
        X_input_transformed, n_neighbors=min(n_neighbors, len(bundle.knn_df))
    )
    neighbors = bundle.knn_df.iloc[indices[0]]
    knn_ratios = neighbors["ratio_acordo"]
    knn_median = knn_ratios.median()
    knn_p25 = knn_ratios.quantile(0.25)
    knn_p75 = knn_ratios.quantile(0.75)
    knn_mean_dist = distances[0].mean()

    # Ensemble
    max_dist = distances[0].max() if distances[0].max() > 0 else 1
    knn_weight = max(0.20, 0.50 * (1 - knn_mean_dist / max_dist))
    reg_weight = 1 - knn_weight

    final_median = np.clip(reg_weight * pred_median + knn_weight * knn_median, 0, 1)
    final_p25 = np.clip(reg_weight * pred_p25 + knn_weight * knn_p25, 0, 1)
    final_p75 = np.clip(reg_weight * pred_p75 + knn_weight * knn_p75, 0, 1)

    # Garantir ordem
    final_p25 = min(final_p25, final_median)
    final_p75 = max(final_p75, final_median)

    return {
        "ratio_median": final_median,
        "ratio_p25": final_p25,
        "ratio_p75": final_p75,
        "valor_acordo_median": final_median * valor_causa,
        "valor_acordo_p25": final_p25 * valor_causa,
        "valor_acordo_p75": final_p75 * valor_causa,
        "knn_weight": knn_weight,
        "reg_weight": reg_weight,
        "knn_mean_dist": knn_mean_dist,
        "n_neighbors": len(neighbors),
        "neighbors_ufs": neighbors["UF"].value_counts().head(3).to_dict(),
        "neighbors_subs": neighbors["Sub-assunto"].value_counts().head(3).to_dict(),
        "neighbors_ratios": knn_ratios.values.tolist(),
    }
