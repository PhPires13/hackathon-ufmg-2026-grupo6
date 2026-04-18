from __future__ import annotations

from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import pickle

import numpy as np
import pandas as pd

from .models import LegalCase, CaseRecommendation


# Caminho relativo aos artifacts dentro do app
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
RISK_MODEL_PATH = ARTIFACTS_DIR / "risk_model.pkl"
COST_MODEL_PATH = ARTIFACTS_DIR / "cost_model.pkl"


@lru_cache(maxsize=1)
def _load_checkpoints() -> tuple[dict, dict]:
    """Carrega os checkpoints dos modelos com cache."""
    try:
        with open(RISK_MODEL_PATH, "rb") as f:
            risk_ckpt = pickle.load(f)
        with open(COST_MODEL_PATH, "rb") as f:
            cost_ckpt = pickle.load(f)
    except ModuleNotFoundError as exc:
        missing_module = getattr(exc, "name", None) or str(exc)
        raise RuntimeError(
            f"Nao foi possivel carregar os checkpoints. Dependencia ausente: {missing_module}. "
            "Instale as dependencias do projeto (ex.: pip install -r requirements.txt)."
        ) from exc
    return risk_ckpt, cost_ckpt


def _to_decimal(value: float, places: str) -> Decimal:
    """Converte float para Decimal com arredondamento correto."""
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _normalize_assunto(assunto: str | None) -> str:
    """Mapeia enum do Django para o formato que o modelo viu no treino."""
    mapping = {
        "NAO_RECONHECE_OPERACAO": "Nao reconhece operacao",
    }
    if not assunto:
        return "desconhecido"
    return mapping.get(assunto, assunto)


def _normalize_sub_assunto(sub_assunto: str | None) -> str:
    """Mapeia enum do Django para o formato que o modelo viu no treino."""
    mapping = {
        "GENERICO": "Generico",
        "GOLPE": "Golpe",
    }
    if not sub_assunto:
        return "desconhecido"
    return mapping.get(sub_assunto, sub_assunto)


def _build_feature_row(case: LegalCase) -> dict:
    """Constrói a linha de features a partir do LegalCase."""
    contrato = int(bool(case.has_contrato))
    extrato = int(bool(case.has_extrato))
    comprovante = int(bool(case.has_comprovante_credito))
    dossie = int(bool(case.has_dossie))
    demonstrativo = int(bool(case.has_demonstrativo_evolucao_divida))
    laudo = int(bool(case.has_laudo_referenciado))

    qtd_docs = contrato + extrato + comprovante + dossie + demonstrativo + laudo

    assunto = _normalize_assunto(case.assunto)
    sub_assunto = _normalize_sub_assunto(case.sub_assunto)
    uf = case.uf or "desconhecido"

    valor_causa = float(case.valor_causa) if case.valor_causa is not None else 0.0

    return {
        "numero_do_processo": case.numero_processo,
        "valor_da_causa": valor_causa,
        "contrato": contrato,
        "extrato": extrato,
        "comprovante_de_credito": comprovante,
        "dossie": dossie,
        "demonstrativo_de_evolucao_da_divida": demonstrativo,
        "laudo_referenciado": laudo,
        "qtd_docs": qtd_docs,
        "docs_faltantes": 6 - qtd_docs,
        "doc_ratio": qtd_docs / 6.0,
        "doc_score": 3 * contrato + 3 * extrato + 2 * comprovante + 1 * demonstrativo,
        "tem_todos_docs": int(qtd_docs == 6),
        "docs_essenciais": contrato + extrato + comprovante,
        "docs_probatorios": dossie + demonstrativo + laudo,
        "combo_docs": f"{contrato}_{extrato}_{comprovante}",
        "assunto": assunto,
        "sub_assunto": sub_assunto,
        "uf": uf,
        "assunto_sub_assunto": f"{assunto}__{sub_assunto}",
        "uf_assunto": f"{uf}__{assunto}",
    }


def _make_matrix(df_input: pd.DataFrame, ckpt: dict, feature_list_key: str) -> pd.DataFrame:
    """Prepara a matrix de features com one-hot encoding e reindex."""
    features = ckpt[feature_list_key]
    x = pd.get_dummies(df_input[features].copy(), drop_first=True)
    return x.reindex(columns=ckpt["feature_columns"], fill_value=0)


def gerar_recomendacao_caso(
    case: LegalCase,
    limiar_fixo: float = 3000.0,
    comparar_com_valor_causa: bool = True,
    settlement_factor: float = 0.30,
) -> CaseRecommendation:
    """
    Recebe LegalCase, roda os 2 modelos, calcula expected_loss
    e cria/atualiza CaseRecommendation.
    
    Args:
        case: LegalCase instance
        limiar_fixo: Limiar de decisão em reais (default 3000)
        comparar_com_valor_causa: Se True, usa valor_causa como limiar se > 0
        settlement_factor: Fator multiplicador para valor de acordo (0.30 = 30% do expected_loss)
    
    Returns:
        CaseRecommendation criado ou atualizado
    """
    risk_ckpt, cost_ckpt = _load_checkpoints()

    row = _build_feature_row(case)
    df_one = pd.DataFrame([row])

    # P(perder)
    x_risk = _make_matrix(df_one, risk_ckpt, "risk_features")
    prob_perder = float(risk_ckpt["model"].predict_proba(x_risk)[:, 1][0])

    # valor_condenacao_estimado
    x_cost = _make_matrix(df_one, cost_ckpt, "cost_features")
    valor_condenacao_estimado = float(np.expm1(cost_ckpt["model"].predict(x_cost))[0])
    valor_condenacao_estimado = max(0.0, valor_condenacao_estimado)

    # expected_loss
    expected_loss = prob_perder * valor_condenacao_estimado

    # ========================
    # FRONTEIRA DE DECISÃO CORRETA
    # ========================

    alpha = settlement_factor  # mesma lógica do acordo
    
    if prob_perder > alpha:
        sugestao_acao = "PROPOR_ACORDO"
        valor_para_acordo = alpha * valor_condenacao_estimado
    else:
        sugestao_acao = "DEFENDER"
        valor_para_acordo = None

    recommendation, _ = CaseRecommendation.objects.update_or_create(
        case=case,
        defaults={
            "probabilidade_perder_caso": _to_decimal(prob_perder, "0.0001"),
            "valor_esperado_condenacao": _to_decimal(expected_loss, "0.01"),
            "sugestao_acao": sugestao_acao,
            "valor_para_acordo": (_to_decimal(valor_para_acordo, "0.01") if valor_para_acordo is not None else None),
        },
    )
    return recommendation
