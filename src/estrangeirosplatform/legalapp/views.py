from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings
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

	return render(
		request,
		'legalapp/cases-list.html',
		{'cases': cases, 'query': query, 'active_nav': 'cases-list'},
	)


def create_case_page(request):
	from .pdf_import import (
		extract_documents_from_directory,
		extract_documents_from_uploads,
		upsert_case_from_documents,
	)

	default_subsidios_base_dir = '../../data/subsidios'

	context = {
		'error_message': '',
		'success_message': '',
		'created_case': None,
		'created_cases': [],
		'subsidios_base_dir': default_subsidios_base_dir,
		'active_nav': 'create-case',
	}

	if request.method == 'POST':
		import_mode = (request.POST.get('import_mode') or 'upload_pdf').strip()

		if import_mode == 'import_folder':
			base_dir_raw = (request.POST.get('subsidios_base_dir') or default_subsidios_base_dir).strip()
			context['subsidios_base_dir'] = base_dir_raw

			base_dir = Path(base_dir_raw).expanduser()
			if not base_dir.is_absolute():
				base_dir = (Path(settings.BASE_DIR) / base_dir).resolve()
			else:
				base_dir = base_dir.resolve()
			if not base_dir.exists() or not base_dir.is_dir():
				context['error_message'] = f'Pasta base de subsidios nao encontrada: {base_dir}'
				return render(request, 'legalapp/create-case.html', context)

			process_dirs = sorted(p for p in base_dir.iterdir() if p.is_dir())
			if not process_dirs:
				context['error_message'] = f'Nenhuma pasta de processo encontrada em: {base_dir}'
				return render(request, 'legalapp/create-case.html', context)

			created_cases = []
			errors = []
			for process_dir in process_dirs:
				try:
					documents_payload = extract_documents_from_directory(process_dir)
					legal_case, _summary_text = upsert_case_from_documents(
						documents_payload,
						case_name_hint=process_dir.name,
					)
					gerar_recomendacao_caso(legal_case)
					created_cases.append(legal_case)
				except ValueError as exc:
					errors.append(f'{process_dir.name}: {exc}')
				except Exception:
					errors.append(f'{process_dir.name}: falha inesperada ao processar pasta')

			if not created_cases:
				context['error_message'] = 'Nao foi possivel processar nenhuma pasta. ' + ' | '.join(errors)
				return render(request, 'legalapp/create-case.html', context)

			context['success_message'] = f'{len(created_cases)} processo(s) cadastrado(s)/atualizado(s) com sucesso pela pasta de subsidios.'
			if errors:
				context['success_message'] += ' Pastas com erro: ' + ' | '.join(errors)
			context['created_case'] = created_cases[0]
			context['created_cases'] = created_cases
			context['cases_url'] = reverse('legalapp:cases-list')
		else:
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
				gerar_recomendacao_caso(legal_case)
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
	try:
		recommendation = legal_case.recommendation
	except ObjectDoesNotExist:
		recommendation = None

	try:
		action = legal_case.action
	except ObjectDoesNotExist:
		action = None

	action_form = None

	if action is None:
		if request.method == 'POST':
			action_form = LawyerActionCreateForm(request.POST)
			action_form.instance.case = legal_case
			if action_form.is_valid():
				action_form.save()
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


def monitoramento_aderencia_page(request):
	actions = (
		LegalCase.objects.select_related('recommendation', 'action')
		.filter(action__isnull=False, recommendation__isnull=False)
	)

	total = actions.count()
	if total == 0:
		context = {
			'total': 0,
			'aderencia_acao_pct': 0.0,
			'aderencia_valor_pct': 0.0,
			'desvio_medio': 0.0,
			'rows': [],
			'active_nav': 'monitoramento-aderencia',
		}
		return render(request, 'legalapp/monitoramento-aderencia.html', context)

	rows = []
	aderentes_acao = 0
	total_acordos_aderentes = 0
	acordos_dentro_faixa = 0
	soma_shift_abs = 0.0
	qtd_shift = 0

	for case in actions:
		recommendation = case.recommendation
		action = case.action

		same_action = bool(action.same_action_taken)
		if same_action:
			aderentes_acao += 1

		valor_ok = action.valor_acordo_in_range
		shift = float(action.shift_valor_acordo) if action.shift_valor_acordo is not None else None
		if shift is not None:
			soma_shift_abs += abs(shift)
			qtd_shift += 1

		if recommendation.sugestao_acao == 'PROPOR_ACORDO' and action.acao == 'PROPOR_ACORDO':
			total_acordos_aderentes += 1
			if valor_ok is True:
				acordos_dentro_faixa += 1

		rows.append({
			'case_id': case.id,
			'numero_processo': case.numero_processo,
			'acao_recomendada': recommendation.sugestao_acao,
			'acao_tomada': action.acao,
			'aderente_acao': same_action,
			'valor_recomendado': recommendation.valor_para_acordo,
			'valor_tomado': action.valor_acordo,
			'aderente_valor': valor_ok,
			'shift_valor': action.shift_valor_acordo,
		})

	context = {
		'total': total,
		'aderencia_acao_pct': (aderentes_acao / total) * 100,
		'aderencia_valor_pct': ((acordos_dentro_faixa / total_acordos_aderentes) * 100) if total_acordos_aderentes else 0.0,
		'desvio_medio': (soma_shift_abs / qtd_shift) if qtd_shift else 0.0,
		'rows': rows,
		'active_nav': 'monitoramento-aderencia',
	}

	return render(request, 'legalapp/monitoramento-aderencia.html', context)


def monitoramento_efetividade_page(request):
	cases = (
		LegalCase.objects.select_related('recommendation', 'action')
		.filter(action__isnull=False, recommendation__isnull=False)
	)

	total = cases.count()
	if total == 0:
		context = {
			'total': 0,
			'taxa_efetividade_pct': 0.0,
			'taxa_exito_defesa_pct': 0.0,
			'taxa_aceitacao_acordos_pct': 0.0,
			'taxa_conversao_acordo_pct': 0.0,
			'custo_total_politica': 0.0,
			'custo_medio_caso': 0.0,
			'valor_esperado_total': 0.0,
			'economia_liquida_total': 0.0,
			'economia_media_por_acordo': 0.0,
			'taxa_casos_custo_abaixo_esperado_pct': 0.0,
			'exposicao_evitada_defesas_exito': 0.0,
			'rows': [],
			'active_nav': 'monitoramento-efetividade',
		}
		return render(request, 'legalapp/monitoramento-efetividade.html', context)

	defesas_concluidas = 0
	defesas_exito = 0
	total_recomendado_acordo = 0
	total_acao_acordo = 0
	total_acordos_aceitos = 0
	qtd_avaliados = 0
	qtd_efetivos = 0
	total_custo = 0.0
	total_valor_esperado = 0.0
	economia_liquida_total = 0.0
	qtd_acordos_comparaveis = 0
	qtd_casos_abaixo_esperado = 0
	exposicao_evitada_defesas_exito = 0.0
	rows = []

	for case in cases:
		recommendation = case.recommendation
		action = case.action

		if recommendation.sugestao_acao == 'PROPOR_ACORDO':
			total_recomendado_acordo += 1

		custo = 0.0
		valor_esperado = float(recommendation.valor_esperado_condenacao or 0)
		economia_liquida = 0.0
		efetivo = None
		criterio = 'Sem criterio'
		tem_custo_observado = False

		if action.acao == 'DEFENDER':
			if action.resultado_macro:
				defesas_concluidas += 1
				efetivo_defesa = action.resultado_macro == 'EXITO'
				efetivo = efetivo_defesa
				if efetivo:
					defesas_exito += 1
				criterio = 'Defesa com exito no resultado macro'

			if action.valor_condenacao is not None:
				custo = float(action.valor_condenacao)
				tem_custo_observado = True

			if efetivo:
				exposicao_evitada_defesas_exito += valor_esperado

		elif action.acao == 'PROPOR_ACORDO':
			total_acao_acordo += 1
			if action.valor_acordo is not None:
				custo = float(action.valor_acordo)
				tem_custo_observado = True
				total_acordos_aceitos += 1  # proxy: acordo registrado com valor informado

			if recommendation.sugestao_acao == 'PROPOR_ACORDO' and action.valor_acordo_in_range is not None:
				criterio = 'Acordo com faixa de aderencia calculada'
			else:
				criterio = 'Acordo sem faixa de aderencia comparavel'

		if valor_esperado > 0 and tem_custo_observado:
			limite_inferior = valor_esperado * 0.80
			limite_superior = valor_esperado * 1.20
			efetivo = limite_inferior <= custo <= limite_superior
			criterio = 'Efetivo financeiro quando custo observado fica dentro de +/-20% da condenacao esperada'
			qtd_avaliados += 1
			if efetivo:
				qtd_efetivos += 1

		if valor_esperado > 0:
			total_valor_esperado += valor_esperado
			economia_liquida = valor_esperado - custo
			economia_liquida_total += economia_liquida
			qtd_acordos_comparaveis += 1 if action.acao == 'PROPOR_ACORDO' else 0
			if custo <= valor_esperado:
				qtd_casos_abaixo_esperado += 1

		total_custo += custo

		rows.append({
			'case_id': case.id,
			'numero_processo': case.numero_processo,
			'acao_recomendada': recommendation.sugestao_acao,
			'acao_tomada': action.acao,
			'resultado_macro': action.resultado_macro,
			'valor_acordo': action.valor_acordo,
			'valor_condenacao': action.valor_condenacao,
			'valor_esperado_condenacao': recommendation.valor_esperado_condenacao,
			'economia_liquida': economia_liquida,
			'custo': custo,
			'efetivo': efetivo,
			'criterio': criterio,
		})

	context = {
		'total': total,
		'taxa_efetividade_pct': ((qtd_efetivos / qtd_avaliados) * 100) if qtd_avaliados else 0.0,
		'taxa_exito_defesa_pct': ((defesas_exito / defesas_concluidas) * 100) if defesas_concluidas else 0.0,
		'taxa_aceitacao_acordos_pct': ((total_acordos_aceitos / total_acao_acordo) * 100) if total_acao_acordo else 0.0,
		'taxa_conversao_acordo_pct': ((total_acao_acordo / total_recomendado_acordo) * 100) if total_recomendado_acordo else 0.0,
		'custo_total_politica': total_custo,
		'custo_medio_caso': (total_custo / total) if total else 0.0,
		'valor_esperado_total': total_valor_esperado,
		'economia_liquida_total': economia_liquida_total,
		'economia_media_por_acordo': (economia_liquida_total / qtd_acordos_comparaveis) if qtd_acordos_comparaveis else 0.0,
		'taxa_casos_custo_abaixo_esperado_pct': ((qtd_casos_abaixo_esperado / total) * 100) if total else 0.0,
		'exposicao_evitada_defesas_exito': exposicao_evitada_defesas_exito,
		'rows': rows,
		'active_nav': 'monitoramento-efetividade',
	}

	return render(request, 'legalapp/monitoramento-efetividade.html', context)


def gerar_recomendacao_caso(
	case: LegalCase,
	limiar_fixo: float = 3000.0,
	comparar_com_valor_causa: bool = True,
	settlement_factor: float = 0.60,
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
	# FRONTEIRA DE DECISAO CORRETA
	# ========================

	alpha = settlement_factor   # mesma logica do acordo

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