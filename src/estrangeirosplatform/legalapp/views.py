from __future__ import annotations

import numpy as np
import pandas as pd
from django.db.models import Q
from django.db.models.functions import Cast
from django.shortcuts import render
from django.db.models import CharField

from .models import LegalCase, CaseRecommendation
from .ml_service import (
	_load_checkpoints,
	_to_decimal,
	_build_feature_row,
	_make_matrix,
)


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

	# fronteira de decisão
	valor_causa = float(case.valor_causa) if case.valor_causa is not None else 0.0
	limiar = valor_causa if (comparar_com_valor_causa and valor_causa > 0) else limiar_fixo

	if expected_loss > limiar:
		sugestao_acao = "PROPOR_ACORDO"
		valor_para_acordo = settlement_factor * valor_condenacao_estimado
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



	query = request.GET.get('q', '').strip()
	cases = LegalCase.objects.select_related('recommendation', 'action')

	if query:
		cases = (
			cases.annotate(
				valor_causa_str=Cast('valor_causa', output_field=CharField()),
				recommendation_prob_str=Cast('recommendation__probabilidade_perder_caso', output_field=CharField()),
				recommendation_expected_value_str=Cast('recommendation__valor_esperado_condenacao', output_field=CharField()),
				recommendation_settlement_value_str=Cast('recommendation__valor_para_acordo', output_field=CharField()),
				action_settlement_value_str=Cast('action__valor_acordo', output_field=CharField()),
				action_condenation_value_str=Cast('action__valor_condenacao', output_field=CharField()),
			)
			.filter(
				Q(numero_processo__icontains=query)
				| Q(uf__icontains=query)
				| Q(assunto__icontains=query)
				| Q(sub_assunto__icontains=query)
				| Q(valor_causa_str__icontains=query)
				| Q(recommendation__sugestao_acao__icontains=query)
				| Q(recommendation_prob_str__icontains=query)
				| Q(recommendation_expected_value_str__icontains=query)
				| Q(recommendation_settlement_value_str__icontains=query)
				| Q(action__acao__icontains=query)
				| Q(action__resultado_macro__icontains=query)
				| Q(action__resultado_micro__icontains=query)
				| Q(action_settlement_value_str__icontains=query)
				| Q(action_condenation_value_str__icontains=query)
			)
		)

	return render(request, 'legalapp/legal-cases.html', {'cases': cases, 'query': query})


def create_case_page(request):
	return render(request, 'legalapp/create-case.html')

