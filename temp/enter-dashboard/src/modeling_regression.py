"""Modelo de regressão para prever valor de condenação + quantile regression + KNN similarity.

Melhorias implementadas:
1. GradientBoosting Regressor dedicado para prever condenação (apenas casos perdidos)
2. Quantile Regression para P25/P50/P75 direto
3. KNN para similarity scoring (substitui filtros exatos)
4. Features financeiras testadas iterativamente
5. Valor da causa como feature principal de regressão
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data_loader import SUBSIDIOS


CATEGORICAL_FEATS = ["UF", "Sub-assunto", "tribunal_sigla"]
BASE_NUMERIC_FEATS = SUBSIDIOS + ["num_subsidios", "log_valor_causa"]

# Features financeiras candidatas (testadas iterativamente)
CANDIDATE_FEATURES = [
    "ratio_causa_uf",        # valor_causa / média da UF
    "ratio_causa_sub",       # valor_causa / média do sub-assunto
    "causa_x_subsidios",     # log(valor_causa) * num_subsidios
    "zscore_causa_uf",       # z-score do valor da causa dentro da UF
]


@dataclass
class RegressionBundle:
    pipeline_median: Pipeline           # Predição pontual (mediana)
    pipeline_p25: Pipeline | None       # Quantile 25
    pipeline_p75: Pipeline | None       # Quantile 75
    knn_model: NearestNeighbors | None  # KNN para similaridade
    knn_X: np.ndarray | None            # Dados transformados para KNN
    knn_df: pd.DataFrame | None         # DataFrame original para KNN lookup
    preprocessor: ColumnTransformer
    numeric_feats: list[str]            # Features numéricas usadas (após seleção)
    accepted_features: list[str]        # Features candidatas aceitas
    rejected_features: list[str]        # Features candidatas rejeitadas
    metrics: dict
    feature_log: list[dict] = field(default_factory=list)


def _add_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona todas as features financeiras candidatas ao DataFrame."""
    df = df.copy()
    df["log_valor_causa"] = np.log1p(df["Valor da causa"])

    # Médias por grupo (calculadas no próprio df para evitar data leakage no treino)
    uf_means = df.groupby("UF")["Valor da causa"].transform("mean")
    sub_means = df.groupby("Sub-assunto")["Valor da causa"].transform("mean")
    uf_stds = df.groupby("UF")["Valor da causa"].transform("std").fillna(1)

    df["ratio_causa_uf"] = df["Valor da causa"] / uf_means.replace(0, 1)
    df["ratio_causa_sub"] = df["Valor da causa"] / sub_means.replace(0, 1)
    df["causa_x_subsidios"] = df["log_valor_causa"] * df["num_subsidios"]
    df["zscore_causa_uf"] = (df["Valor da causa"] - uf_means) / uf_stds

    return df


def _build_preprocessor(numeric_feats: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATS),
        ("num", StandardScaler(), numeric_feats),
    ])


def _build_quantile_model(quantile: float) -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        loss="quantile", alpha=quantile,
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        learning_rate=0.1, random_state=42,
    )


def _iterative_feature_selection(
    X_train: pd.DataFrame, y_train: pd.Series,
    X_test: pd.DataFrame, y_test: pd.Series,
    base_feats: list[str], candidates: list[str],
) -> tuple[list[str], list[str], list[dict]]:
    """Testa cada feature candidata e mantém apenas as que reduzem MAE."""
    pre_base = _build_preprocessor(base_feats)
    model_base = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        learning_rate=0.1, random_state=42,
    )
    pipe_base = Pipeline([("pre", pre_base), ("reg", model_base)])
    pipe_base.fit(X_train[CATEGORICAL_FEATS + base_feats], y_train)
    base_mae = mean_absolute_error(
        y_test, pipe_base.predict(X_test[CATEGORICAL_FEATS + base_feats])
    )

    accepted = []
    rejected = []
    log = [{"feature": "(base)", "mae": base_mae, "delta": 0, "status": "base"}]
    current_feats = list(base_feats)
    current_mae = base_mae

    for feat in candidates:
        if feat not in X_train.columns:
            rejected.append(feat)
            log.append({"feature": feat, "mae": None, "delta": None, "status": "indisponível"})
            continue

        test_feats = current_feats + [feat]
        pre = _build_preprocessor(test_feats)
        model = GradientBoostingRegressor(
            n_estimators=200, max_depth=5, min_samples_leaf=20,
            learning_rate=0.1, random_state=42,
        )
        pipe = Pipeline([("pre", pre), ("reg", model)])
        pipe.fit(X_train[CATEGORICAL_FEATS + test_feats], y_train)
        new_mae = mean_absolute_error(
            y_test, pipe.predict(X_test[CATEGORICAL_FEATS + test_feats])
        )
        delta = new_mae - current_mae

        if new_mae < current_mae:
            accepted.append(feat)
            current_feats.append(feat)
            current_mae = new_mae
            log.append({"feature": feat, "mae": new_mae, "delta": delta, "status": "✅ aceita"})
        else:
            rejected.append(feat)
            log.append({"feature": feat, "mae": new_mae, "delta": delta, "status": "❌ rejeitada"})

    return accepted, rejected, log


@st.cache_resource(show_spinner="Treinando modelo de regressão para condenação...")
def train_regression_model(df_hash: int, sample_n: int = 30000) -> RegressionBundle:
    """Treina modelo de regressão em casos perdidos para prever condenação."""
    from .data_loader import load_data
    df_full = load_data()

    # Apenas casos perdidos com condenação > 0
    df_lost = df_full[
        (df_full["sucesso"] == 0) &
        (df_full["Valor da condenação/indenização"] > 0)
    ].copy()

    if sample_n and len(df_lost) > sample_n:
        df_lost = df_lost.sample(sample_n, random_state=42)

    # Adicionar features financeiras
    df_lost = _add_financial_features(df_lost)
    y = df_lost["Valor da condenação/indenização"]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df_lost, y, test_size=0.2, random_state=42,
    )

    # ── Seleção iterativa de features ──
    accepted, rejected, feature_log = _iterative_feature_selection(
        X_train, y_train, X_test, y_test,
        BASE_NUMERIC_FEATS, CANDIDATE_FEATURES,
    )
    final_numeric = BASE_NUMERIC_FEATS + accepted
    all_feats = CATEGORICAL_FEATS + final_numeric

    # ── Treinar modelo final (mediana = quantile 0.5) ──
    pre = _build_preprocessor(final_numeric)
    model_median = GradientBoostingRegressor(
        loss="quantile", alpha=0.5,
        n_estimators=300, max_depth=5, min_samples_leaf=20,
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
    pre_knn.fit(df_lost[all_feats])
    X_knn_transformed = pre_knn.transform(df_lost[all_feats])
    knn = NearestNeighbors(n_neighbors=min(20, len(df_lost)), metric="euclidean")
    knn.fit(X_knn_transformed)

    # ── Métricas no test set ──
    y_pred_median = pipe_median.predict(X_test[all_feats])
    y_pred_p25 = pipe_p25.predict(X_test[all_feats])
    y_pred_p75 = pipe_p75.predict(X_test[all_feats])

    # Clamp predictions to [0, valor_causa]
    valor_causa_test = X_test["Valor da causa"].values
    y_pred_median = np.clip(y_pred_median, 0, valor_causa_test)
    y_pred_p25 = np.clip(y_pred_p25, 0, valor_causa_test)
    y_pred_p75 = np.clip(y_pred_p75, 0, valor_causa_test)

    mae = mean_absolute_error(y_test, y_pred_median)
    mape = mean_absolute_percentage_error(y_test, y_pred_median) * 100

    # Cobertura do intervalo P25-P75 (quantos valores reais caem dentro)
    in_range = ((y_test.values >= y_pred_p25) & (y_test.values <= y_pred_p75)).mean()

    metrics = {
        "mae": mae,
        "mape": mape,
        "cobertura_p25_p75": in_range,
        "n_treino": len(X_train),
        "n_teste": len(X_test),
        "n_features": len(final_numeric) + len(CATEGORICAL_FEATS),
    }

    return RegressionBundle(
        pipeline_median=pipe_median,
        pipeline_p25=pipe_p25,
        pipeline_p75=pipe_p75,
        knn_model=knn,
        knn_X=X_knn_transformed,
        knn_df=df_lost.reset_index(drop=True),
        preprocessor=pre_knn,
        numeric_feats=final_numeric,
        accepted_features=accepted,
        rejected_features=rejected,
        metrics=metrics,
        feature_log=feature_log,
    )


def predict_conviction(
    bundle: RegressionBundle,
    dados: dict,
    df_ref: pd.DataFrame,
    valor_causa: float,
    n_neighbors: int = 15,
) -> dict:
    """Prediz condenação usando ensemble: regressão + KNN + cap no valor da causa."""
    from .data_loader import SUBSIDIOS as SUBS

    # Construir DataFrame de entrada com features financeiras
    row = {
        "UF": dados["UF"],
        "Sub-assunto": dados["Sub-assunto"],
        "tribunal_sigla": dados["tribunal_sigla"],
        **{s: dados[s] for s in SUBS},
        "num_subsidios": dados["num_subsidios"],
        "Valor da causa": valor_causa,
    }
    X_input = pd.DataFrame([row])
    X_input = _add_financial_features(X_input)
    all_feats = CATEGORICAL_FEATS + bundle.numeric_feats

    # ── Predição por regressão ──
    pred_median = float(bundle.pipeline_median.predict(X_input[all_feats])[0])
    pred_p25 = float(bundle.pipeline_p25.predict(X_input[all_feats])[0])
    pred_p75 = float(bundle.pipeline_p75.predict(X_input[all_feats])[0])

    # ── Predição por KNN ──
    X_input_transformed = bundle.preprocessor.transform(X_input[all_feats])
    distances, indices = bundle.knn_model.kneighbors(
        X_input_transformed, n_neighbors=min(n_neighbors, len(bundle.knn_df))
    )
    neighbors = bundle.knn_df.iloc[indices[0]]
    knn_cond = neighbors["Valor da condenação/indenização"]
    knn_median = knn_cond.median()
    knn_p25 = knn_cond.quantile(0.25)
    knn_p75 = knn_cond.quantile(0.75)
    knn_mean_dist = distances[0].mean()

    # ── Ensemble: peso maior para regressão, KNN como ajuste ──
    # Quanto mais próximos os vizinhos (dist menor), mais peso ao KNN
    max_dist = distances[0].max() if distances[0].max() > 0 else 1
    knn_weight = max(0.15, 0.40 * (1 - knn_mean_dist / max_dist))
    reg_weight = 1 - knn_weight

    final_median = reg_weight * pred_median + knn_weight * knn_median
    final_p25 = reg_weight * pred_p25 + knn_weight * knn_p25
    final_p75 = reg_weight * pred_p75 + knn_weight * knn_p75

    # ── Cap no valor da causa ──
    final_median = np.clip(final_median, 0, valor_causa)
    final_p25 = np.clip(final_p25, 0, valor_causa)
    final_p75 = np.clip(final_p75, 0, valor_causa)

    # Garantir ordem P25 <= median <= P75
    final_p25 = min(final_p25, final_median)
    final_p75 = max(final_p75, final_median)

    return {
        "cond_median": final_median,
        "cond_p25": final_p25,
        "cond_p75": final_p75,
        "reg_median": np.clip(pred_median, 0, valor_causa),
        "reg_p25": np.clip(pred_p25, 0, valor_causa),
        "reg_p75": np.clip(pred_p75, 0, valor_causa),
        "knn_median": np.clip(knn_median, 0, valor_causa),
        "knn_p25": np.clip(knn_p25, 0, valor_causa),
        "knn_p75": np.clip(knn_p75, 0, valor_causa),
        "knn_weight": knn_weight,
        "reg_weight": reg_weight,
        "knn_mean_dist": knn_mean_dist,
        "n_neighbors": len(neighbors),
        "neighbors_ufs": neighbors["UF"].value_counts().head(3).to_dict(),
        "neighbors_subs": neighbors["Sub-assunto"].value_counts().head(3).to_dict(),
    }


def calcular_faixa_acordo_v2(
    pred: dict, valor_causa: float, prob_derrota: float,
) -> dict:
    """Calcula faixa de acordo usando predições do modelo de regressão.

    Estratégia otimizada (Prob + Mult 0.70 + Thresh 0.6):
    - Piso: 50% do P25 predito (oferta agressiva)
    - Teto: 70% da mediana predita (mais conservador)
    - Ideal: ponderado pela prob_derrota (quanto menos certeza, menor o valor)
    """
    cond_estimada = pred["cond_median"]
    p25 = pred["cond_p25"]
    p75 = pred["cond_p75"]

    # Piso: 50% do P25 predito (mais agressivo que antes)
    piso = max(p25 * 0.50, 0)
    # Teto: 70% da mediana predita (reduzido de 95%)
    teto = cond_estimada * 0.70
    # Garantir que teto >= piso
    teto = max(teto, piso * 1.05)

    # Ideal: interpolação ponderada pela prob de derrota
    # Quanto menor a certeza de derrota, mais próximo do piso
    ideal_base = piso + (teto - piso) * prob_derrota
    # Ponderação adicional: multiplica pelo prob_derrota para reduzir valor em casos incertos
    ideal = ideal_base * prob_derrota

    # Garantir que ideal >= piso e <= teto
    ideal = np.clip(ideal, piso * prob_derrota, teto)

    # Cap tudo no valor da causa
    piso = min(piso, valor_causa)
    teto = min(teto, valor_causa)
    ideal = min(ideal, valor_causa)

    economia_vs_cond = cond_estimada - ideal
    economia_vs_causa = valor_causa - ideal

    return {
        "piso": piso,
        "teto": teto,
        "ideal": ideal,
        "cond_estimada": cond_estimada,
        "cond_p25": p25,
        "cond_p75": p75,
        "economia_vs_cond": economia_vs_cond,
        "economia_vs_causa": economia_vs_causa,
        "pct_economia": economia_vs_cond / cond_estimada if cond_estimada > 0 else 0,
    }
