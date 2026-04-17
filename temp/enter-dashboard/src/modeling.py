"""Modelagem preditiva do êxito e explicabilidade via SHAP."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, roc_auc_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data_loader import SUBSIDIOS


@dataclass
class ModelBundle:
    pipeline: Pipeline
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    y_pred: np.ndarray
    y_proba: np.ndarray
    feature_names: list[str]
    metrics: dict


CATEGORICAL_FEATS = ["UF", "Sub-assunto", "tribunal_sigla"]
NUMERIC_FEATS = SUBSIDIOS + ["num_subsidios", "Valor da causa"]


def _prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = df[CATEGORICAL_FEATS + NUMERIC_FEATS].copy()
    X["Valor da causa"] = np.log1p(X["Valor da causa"])
    y = df["sucesso"].astype(int)
    return X, y


def _build_pipeline(model_kind: str) -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATS),
        ("num", StandardScaler() if model_kind == "logistic" else "passthrough", NUMERIC_FEATS),
    ])
    if model_kind == "logistic":
        clf = LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=-1)
    else:
        clf = RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=20,
            n_jobs=-1, random_state=42, class_weight="balanced",
        )
    return Pipeline([("pre", pre), ("clf", clf)])


def _feature_names_from_pipeline(pipe: Pipeline) -> list[str]:
    pre = pipe.named_steps["pre"]
    cat_names = list(pre.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATS))
    return cat_names + NUMERIC_FEATS


@st.cache_resource(show_spinner="Treinando modelo...")
def train_model(df_hash: int, model_kind: str = "rf", sample_n: int = 30000) -> ModelBundle:
    """df_hash é apenas para invalidar cache quando os dados mudam."""
    from .data_loader import load_data
    df = load_data()
    if sample_n and len(df) > sample_n:
        df = df.sample(sample_n, random_state=42)

    X, y = _prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    pipe = _build_pipeline(model_kind)
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
        "report": classification_report(y_test, y_pred, output_dict=True,
                                        target_names=["Não êxito", "Êxito"]),
        "confusion": confusion_matrix(y_test, y_pred),
    }
    return ModelBundle(
        pipeline=pipe, X_train=X_train, X_test=X_test,
        y_train=y_train, y_test=y_test, y_pred=y_pred, y_proba=y_proba,
        feature_names=_feature_names_from_pipeline(pipe), metrics=metrics,
    )


@st.cache_resource(show_spinner="Calculando valores SHAP...")
def compute_shap(_bundle: ModelBundle, max_samples: int = 1000):
    """Retorna (shap_values, X_sample_transformed, feature_names).
    Usa TreeExplainer (RF) ou LinearExplainer (Logistic)."""
    import shap
    pre = _bundle.pipeline.named_steps["pre"]
    clf = _bundle.pipeline.named_steps["clf"]
    X_sample = _bundle.X_test.sample(min(max_samples, len(_bundle.X_test)), random_state=0)
    X_t = pre.transform(X_sample)

    if isinstance(clf, RandomForestClassifier):
        explainer = shap.TreeExplainer(clf)
        sv = explainer.shap_values(X_t)
        # Para binário, pega classe 1 (Êxito)
        if isinstance(sv, list):
            sv = sv[1]
        elif sv.ndim == 3:
            sv = sv[:, :, 1]
    else:
        explainer = shap.LinearExplainer(clf, X_t)
        sv = explainer.shap_values(X_t)

    return sv, X_t, _bundle.feature_names, X_sample
