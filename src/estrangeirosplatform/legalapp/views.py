from __future__ import annotations

import numpy as np
import pandas as pd
from django.db.models import Q
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import CharField
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from .models import LegalCase, CaseRecommendation
from .ml_service import (
	_load_checkpoints,
	_to_decimal,
	_build_feature_row,
	_make_matrix,
)

from .forms import LawyerActionCreateForm
from .models import LegalCase


def cases_list_page(request):
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

	return render(request, 'legalapp/cases-list.html', {'cases': cases, 'query': query})


def create_case_page(request):
	from .pdf_import import extract_documents_from_uploads, upsert_case_from_documents

	context = {
		'error_message': '',
		'success_message': '',
		'created_case': None,
	}

	if request.method == 'POST':
		uploaded_files = request.FILES.getlist('pdf_files')

		if not uploaded_files:
			context['error_message'] = 'Envie pelo menos um arquivo PDF.'
			return render(request, 'legalapp/create-case.html', context)

		invalid_files = [f.name for f in uploaded_files if not f.name.lower().endswith('.pdf')]
		if invalid_files:
			context['error_message'] = (
				'Apenas PDFs sao permitidos. Arquivos invalidos: '
				+ ', '.join(invalid_files)
			)
			return render(request, 'legalapp/create-case.html', context)

		try:
			documents_payload = extract_documents_from_uploads(uploaded_files)
			legal_case, _summary_text = upsert_case_from_documents(documents_payload)
		except ValueError as exc:
			context['error_message'] = str(exc)
			return render(request, 'legalapp/create-case.html', context)
		except Exception:
			context['error_message'] = 'Nao foi possivel processar os arquivos enviados.'
			return render(request, 'legalapp/create-case.html', context)

		context['success_message'] = 'Processo cadastrado e extraido com sucesso.'
		context['created_case'] = legal_case
		context['cases_url'] = reverse('legalapp:cases-list')

	return render(request, 'legalapp/create-case.html', context)


def case_detail_page(request, case_id):
	legal_case = get_object_or_404(
		LegalCase.objects.prefetch_related('documents').select_related('recommendation', 'action'),
		id=case_id,
	)
	recommendation = gerar_recomendacao_caso(legal_case)

	try:
		action = legal_case.action
	except ObjectDoesNotExist:
		action = None

	action_form = None

	if action is None:
		if request.method == 'POST':
			action_form = LawyerActionCreateForm(request.POST)
			if action_form.is_valid():
				new_action = action_form.save(commit=False)
				new_action.case = legal_case
				new_action.save()
				return redirect('legalapp:case-detail', case_id=legal_case.id)
		else:
			action_form = LawyerActionCreateForm()

	context = {
		'case': legal_case,
		'documents': legal_case.documents.all(),
		'recommendation': recommendation,
		'action': action,
		'action_form': action_form,
	}

	return render(request, 'legalapp/case-detail.html', context)


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
		valor_para_acordo = settlement_factor * expected_loss
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