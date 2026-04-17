from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MODEL_VERSION = 'policy_v1'


@dataclass
class FeatureVector:
    contrato: int
    extrato: int
    comprovante: int
    dossie: int
    demonstrativo: int
    laudo: int
    qtd_docs: int
    doc_score: int


@dataclass
class InferenceResult:
    prob_perder: Decimal
    valor_esperado_condenacao: Decimal
    sugestao_acao: str
    valor_para_acordo: Decimal
    agente_classificacao_risco: str
    agente_sugestao_acordo: str


class FeatureEngineeringService:
    @staticmethod
    def build_features(legal_case) -> FeatureVector:
        contrato = int(bool(legal_case.has_contrato))
        extrato = int(bool(legal_case.has_extrato))
        comprovante = int(bool(legal_case.has_comprovante_credito))
        dossie = int(bool(legal_case.has_dossie))
        demonstrativo = int(bool(legal_case.has_demonstrativo_evolucao_divida))
        laudo = int(bool(legal_case.has_laudo_referenciado))

        qtd_docs = contrato + extrato + comprovante + dossie + demonstrativo + laudo
        doc_score = (3 * contrato) + (3 * extrato) + (2 * comprovante) + (1 * demonstrativo)

        return FeatureVector(
            contrato=contrato,
            extrato=extrato,
            comprovante=comprovante,
            dossie=dossie,
            demonstrativo=demonstrativo,
            laudo=laudo,
            qtd_docs=qtd_docs,
            doc_score=doc_score,
        )


class RiskModelService:
    @staticmethod
    def estimate_loss_probability(legal_case, f: FeatureVector) -> float:
        # Heuristica alinhada ao notebook: menos evidencias fortes -> maior risco.
        score = 0.18
        score += 0.22 * (1 - f.contrato)
        score += 0.20 * (1 - f.extrato)
        score += 0.15 * (1 - f.comprovante)
        score += 0.08 * (1 - f.dossie)

        if legal_case.sub_assunto == 'GOLPE':
            score += 0.07

        score -= min(f.doc_score / 30.0, 0.20)

        return max(0.02, min(0.98, score))

    @staticmethod
    def estimate_predicted_condemnation(legal_case) -> float:
        valor_condenacao = float(legal_case.valor_condenacao or 0)
        valor_causa = float(legal_case.valor_causa or 0)

        if valor_condenacao > 0:
            return valor_condenacao

        # Fallback quando nao ha historico consolidado no caso.
        return max(valor_causa * 0.30, 500.0)


class DecisionPolicyService:
    @staticmethod
    def decide(expected_loss: float) -> tuple[str, float]:
        sugestao_acao = 'PROPOR_ACORDO' if expected_loss > 3000 else 'DEFENDER'
        valor_para_acordo = expected_loss * 0.70 if sugestao_acao == 'PROPOR_ACORDO' else 0.0
        return sugestao_acao, valor_para_acordo


def _to_decimal_4(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def _to_decimal_2(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class RecommendationPipeline:
    @staticmethod
    def run(legal_case) -> InferenceResult:
        features = FeatureEngineeringService.build_features(legal_case)
        prob_perder = RiskModelService.estimate_loss_probability(legal_case, features)
        valor_predito = RiskModelService.estimate_predicted_condemnation(legal_case)
        expected_loss = prob_perder * valor_predito
        sugestao_acao, valor_para_acordo = DecisionPolicyService.decide(expected_loss)

        return InferenceResult(
            prob_perder=_to_decimal_4(prob_perder),
            valor_esperado_condenacao=_to_decimal_2(expected_loss),
            sugestao_acao=sugestao_acao,
            valor_para_acordo=_to_decimal_2(valor_para_acordo),
            agente_classificacao_risco=f'notebook-risk-{MODEL_VERSION}',
            agente_sugestao_acordo=f'notebook-policy-{MODEL_VERSION}',
        )


def infer_recommendation_payload(legal_case) -> dict:
    result = RecommendationPipeline.run(legal_case)
    return {
        'agente_classificacao_risco': result.agente_classificacao_risco,
        'probabilidade_perder_caso': result.prob_perder,
        'valor_esperado_condenacao': result.valor_esperado_condenacao,
        'agente_sugestao_acordo': result.agente_sugestao_acordo,
        'sugestao_acao': result.sugestao_acao,
        'valor_para_acordo': result.valor_para_acordo,
    }
