from django.shortcuts import render
from django.utils import timezone

from .agent.inference import upsert_case_recommendation
from .models import CaseDocument, CaseRecommendation, LegalCase


DOCUMENT_EVIDENCE_LABELS = {
	'CONTRATO': 'Contrato juntado aos autos',
	'EXTRATO_BANCARIO': 'Extrato bancario com movimentacoes',
	'COMPROVANTE_DE_CREDITO': 'Comprovante de credito apresentado',
	'DOSSIE': 'Dossie complementar anexado',
	'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA': 'Demonstrativo de evolucao da divida anexado',
	'LAUDO_REFERENCIA': 'Laudo de referencia inserido',
}


def home_view(request):
	return render(request, 'legalapp/home.html')


def _format_currency(value):
	if value is None:
		return 'R$ 0,00'

	amount = f'{value:,.2f}'
	amount = amount.replace(',', 'X').replace('.', ',').replace('X', '.')
	return f'R$ {amount}'


def _build_evidence_list(legal_case):
	evidences = []

	if legal_case.has_contrato:
		evidences.append('Flag de subsidio: ha indicio de contrato no processo')
	if legal_case.has_extrato:
		evidences.append('Flag de subsidio: extrato bancario disponivel')
	if legal_case.has_comprovante_credito:
		evidences.append('Flag de subsidio: comprovante de credito disponivel')
	if legal_case.has_dossie:
		evidences.append('Flag de subsidio: dossie disponivel')
	if legal_case.has_demonstrativo_evolucao_divida:
		evidences.append('Flag de subsidio: demonstrativo de evolucao da divida disponivel')
	if legal_case.has_laudo_referenciado:
		evidences.append('Flag de subsidio: laudo referenciado disponivel')

	documents = CaseDocument.objects.filter(case=legal_case).order_by('document_type', 'file_name')
	for document in documents:
		label = DOCUMENT_EVIDENCE_LABELS.get(document.document_type, document.document_type)
		evidences.append(f'{label} ({document.file_name})')

	if not evidences:
		evidences.append('Nao ha evidencias documentais relevantes registradas para este processo')

	return evidences


def _build_justification(legal_case, recommendation):
	has_strong_contract_proof = (
		legal_case.has_contrato
		or legal_case.has_comprovante_credito
		or CaseDocument.objects.filter(
			case=legal_case,
			document_type__in=['CONTRATO', 'COMPROVANTE_DE_CREDITO'],
		).exists()
	)

	agreement_history = LegalCase.objects.filter(
		assunto=legal_case.assunto,
		sub_assunto=legal_case.sub_assunto,
		resultado_micro='ACORDO',
	).exclude(pk=legal_case.pk)

	similar_cases_count = LegalCase.objects.filter(
		assunto=legal_case.assunto,
		sub_assunto=legal_case.sub_assunto,
	).exclude(pk=legal_case.pk).count()

	agreement_rate = 0
	if similar_cases_count:
		agreement_rate = (agreement_history.count() / similar_cases_count) * 100

	if recommendation.sugestao_acao == 'PROPOR_ACORDO':
		reasons = []
		if not has_strong_contract_proof:
			reasons.append('nao ha prova forte de contratacao')
		if agreement_history.exists():
			reasons.append('ha historico de condenacao ou acordo em casos similares')
		if not reasons:
			reasons.append('o risco projetado de perda indica melhor custo-beneficio no acordo')

		return (
			'Recomendamos ACORDO pois '
			+ ' e '.join(reasons)
			+ f'. Taxa de acordos em casos similares: {agreement_rate:.1f}%. '
			+ f'Probabilidade de perda estimada: {recommendation.probabilidade_perder_caso:.2%}.'
		)

	defense_reasons = []
	if has_strong_contract_proof:
		defense_reasons.append('ha prova material de contratacao ou credito')
	if recommendation.probabilidade_perder_caso < 0.35:
		defense_reasons.append('a probabilidade de perda esta baixa')
	if not defense_reasons:
		defense_reasons.append('a expectativa economica favorece sustentar a defesa')

	return (
		'Recomendamos DEFESA pois '
		+ ' e '.join(defense_reasons)
		+ f'. Taxa de acordos em casos similares: {agreement_rate:.1f}%. '
		+ f'Probabilidade de perda estimada: {recommendation.probabilidade_perder_caso:.2%}.'
	)


_VALOR_PROXIMO_THRESHOLD = 20  # desvio maximo em % para considerar valor "proximo"


def _adherence_status(recommendation):
	"""Retorna 'aderiu', 'nao_aderiu' ou 'sem_resultado'."""
	if recommendation.decisao_advogado == 'ACEITA':
		return 'aderiu'
	if recommendation.decisao_advogado == 'REJEITADA':
		return 'nao_aderiu'
	return 'sem_resultado'


def _valor_desvio_pct(recommendation):
	"""Desvio % entre valor_condenacao e valor_para_acordo.
	Retorna None quando nao se aplica.
	"""
	if recommendation.sugestao_acao != 'PROPOR_ACORDO':
		return None
	if _is_agreement_accepted(recommendation) is not True:
		return None
	sugerido = recommendation.valor_para_acordo
	real = recommendation.case.valor_condenacao
	if not sugerido:
		return None
	return float(abs(real - sugerido) / sugerido * 100)


def _is_agreement_accepted(recommendation):
	if recommendation.decisao_advogado == 'ACEITA':
		return True
	if recommendation.decisao_advogado == 'REJEITADA':
		return False
	return None


def adherence_monitoring_view(request):
	recommendations = (
		CaseRecommendation.objects.select_related('case')
		.order_by('-created_at')
	)

	total = recommendations.count()
	aderiu_count = 0
	nao_aderiu_count = 0
	acordo_sugerido_e_feito = 0
	valores_proximos = 0
	acordos_com_valor_avaliavel = 0

	rows = []
	for rec in recommendations:
		status = _adherence_status(rec)
		desvio = _valor_desvio_pct(rec)

		aderiu = status == 'aderiu'
		if aderiu:
			aderiu_count += 1
		elif status == 'nao_aderiu':
			nao_aderiu_count += 1

		acordo_feito = (
			rec.sugestao_acao == 'PROPOR_ACORDO'
			and _is_agreement_accepted(rec) is True
		)
		if acordo_feito:
			acordo_sugerido_e_feito += 1

		if desvio is not None:
			acordos_com_valor_avaliavel += 1
			if desvio <= _VALOR_PROXIMO_THRESHOLD:
				valores_proximos += 1

		rows.append({
			'numero_processo': rec.case.numero_processo,
			'sugestao': 'ACORDO' if rec.sugestao_acao == 'PROPOR_ACORDO' else 'DEFESA',
			'resultado': rec.case.resultado_micro,
			'aderiu': aderiu,
			'status_label': 'Aderiu' if aderiu else ('Nao avaliavel' if status == 'sem_resultado' else 'Nao aderiu'),
			'valor_sugerido': _format_currency(rec.valor_para_acordo),
			'valor_real': _format_currency(rec.case.valor_condenacao),
			'desvio_pct': f'{desvio:.1f}%' if desvio is not None else '—',
			'valor_proximo': (desvio is not None and desvio <= _VALOR_PROXIMO_THRESHOLD),
		})

	aderencia_pct = (aderiu_count / total * 100) if total else 0
	valor_proximo_pct = (
		(valores_proximos / acordos_com_valor_avaliavel * 100)
		if acordos_com_valor_avaliavel else 0
	)

	context = {
		'total': total,
		'aderiu_count': aderiu_count,
		'nao_aderiu_count': nao_aderiu_count,
		'sem_resultado_count': total - aderiu_count - nao_aderiu_count,
		'aderencia_pct': round(aderencia_pct, 1),
		'acordo_sugerido_e_feito': acordo_sugerido_e_feito,
		'valores_proximos': valores_proximos,
		'acordos_com_valor_avaliavel': acordos_com_valor_avaliavel,
		'valor_proximo_pct': round(valor_proximo_pct, 1),
		'threshold': _VALOR_PROXIMO_THRESHOLD,
		'rows': rows,
	}

	return render(request, 'legalapp/adherence_monitoring.html', context)


def lawyer_assistant_view(request):
	case_number = (request.GET.get('processo') or request.POST.get('processo') or '').strip()
	recommendation = None
	lookup_error = None
	action_feedback = None
	available_case_numbers = list(
		LegalCase.objects.order_by('numero_processo').values_list('numero_processo', flat=True)
	)

	if case_number:
		recommendation = (
			CaseRecommendation.objects.select_related('case')
			.filter(case__numero_processo=case_number)
			.first()
		)
		if recommendation is None:
			legal_case = LegalCase.objects.filter(numero_processo=case_number).first()
			if legal_case is not None:
				recommendation = upsert_case_recommendation(legal_case)
				action_feedback = 'Recomendacao gerada automaticamente pelo modelo de decisao.'
			else:
				lookup_error = 'Processo nao encontrado ou sem recomendacao cadastrada.'
	else:
		recommendation = CaseRecommendation.objects.select_related('case').first()
		if recommendation is None:
			legal_case = LegalCase.objects.first()
			if legal_case is not None:
				recommendation = upsert_case_recommendation(legal_case)
				action_feedback = 'Recomendacao gerada automaticamente pelo modelo de decisao.'
			else:
				lookup_error = 'Nao ha recomendacoes cadastradas para exibir na interface.'

	context = {
		'case_number': case_number,
		'lookup_error': lookup_error,
		'action_feedback': action_feedback,
		'assistant_data': None,
		'available_case_numbers': available_case_numbers,
	}

	if recommendation:
		if request.method == 'POST':
			decision = request.POST.get('decision')
			if decision in {'ACEITA', 'REJEITADA'}:
				recommendation.decisao_advogado = decision
				recommendation.decisao_advogado_at = timezone.now()
				recommendation.save(update_fields=['decisao_advogado', 'decisao_advogado_at', 'updated_at'])
				action_feedback = (
					'Decisao registrada: recomendacao aceita.'
					if decision == 'ACEITA'
					else 'Decisao registrada: recomendacao rejeitada.'
				)
			elif decision == 'LIMPAR':
				recommendation.decisao_advogado = None
				recommendation.decisao_advogado_at = None
				recommendation.save(update_fields=['decisao_advogado', 'decisao_advogado_at', 'updated_at'])
				action_feedback = 'Decisao do advogado removida.'

		legal_case = recommendation.case
		context['assistant_data'] = {
			'numero_processo': legal_case.numero_processo,
			'decisao_sugerida': 'ACORDO' if recommendation.sugestao_acao == 'PROPOR_ACORDO' else 'DEFESA',
			'justificativa': _build_justification(legal_case, recommendation),
			'valor_acordo': _format_currency(recommendation.valor_para_acordo),
			'valor_esperado': _format_currency(recommendation.valor_esperado_condenacao),
			'evidencias': _build_evidence_list(legal_case),
			'agente_classificacao_risco': recommendation.agente_classificacao_risco,
			'agente_sugestao_acordo': recommendation.agente_sugestao_acordo,
			'decisao_advogado': recommendation.decisao_advogado,
			'decisao_advogado_at': recommendation.decisao_advogado_at,
		}
		context['action_feedback'] = action_feedback

	return render(request, 'legalapp/lawyer_assistant.html', context)


def effectiveness_monitoring_view(request):
	recommendations = (
		CaseRecommendation.objects.select_related('case')
		.order_by('-created_at')
	)

	total = recommendations.count()
	acordos_sugeridos = 0
	acordos_aceitos = 0
	acordos_rejeitados = 0
	acordos_sem_decisao = 0
	total_economia = 0
	total_economia_efetiva = 0
	casos_com_nova_condenacao = 0
	total_condenacoes_evitadas = 0

	rows = []
	for rec in recommendations:
		acordo_sugerido = rec.sugestao_acao == 'PROPOR_ACORDO'
		acordo_realizado = _is_agreement_accepted(rec)
		
		if acordo_sugerido:
			acordos_sugeridos += 1
			# economia potencial: valor esperado - valor sugerido
			economia_potencial = rec.valor_esperado_condenacao - rec.valor_para_acordo
			total_economia += economia_potencial
			
			if acordo_realizado is True:
				acordos_aceitos += 1
				# economia efetiva: valor esperado - valor real pago
				economia_efetiva = rec.valor_esperado_condenacao - rec.case.valor_condenacao
				total_economia_efetiva += economia_efetiva
			elif acordo_realizado is False:
				acordos_rejeitados += 1
			else:
				acordos_sem_decisao += 1
		
		# para défesa sugerida e mantida (sem acordo)
		if (
			rec.sugestao_acao == 'DEFENDER'
			and rec.case.resultado_micro != 'ACORDO'
		):
			casos_com_nova_condenacao += 1
			# economia em relação à expectativa
			condenacao_evitada = rec.valor_esperado_condenacao - rec.case.valor_condenacao
			economia_defesa = max(0, condenacao_evitada)
			total_condenacoes_evitadas += economia_defesa
			total_economia_efetiva += economia_defesa
		
		# monta linha de tabela
		acordo_status = '—'
		economia_valor = 0
		
		if acordo_sugerido:
			if acordo_realizado is True:
				acordo_status = 'Aceito'
				economia_valor = rec.valor_esperado_condenacao - rec.case.valor_condenacao
			elif acordo_realizado is False:
				acordo_status = 'Rejeitado'
				economia_valor = 0
			else:
				acordo_status = 'N/A'
				economia_valor = 0
		else:
			# defesa
			acordo_status = 'N/A'
			economia_valor = max(0, rec.valor_esperado_condenacao - rec.case.valor_condenacao)
		
		rows.append({
			'numero_processo': rec.case.numero_processo,
			'sugestao': 'ACORDO' if acordo_sugerido else 'DEFESA',
			'status_acordo': acordo_status,
			'valor_esperado': _format_currency(rec.valor_esperado_condenacao),
			'valor_realizado': _format_currency(rec.case.valor_condenacao),
			'economia': _format_currency(economia_valor),
			'economia_valor_raw': float(economia_valor),
		})
		
	# calcula taxas
	taxa_aceitacao_acordos = 0
	acordos_decididos = acordos_aceitos + acordos_rejeitados
	if acordos_decididos:
		taxa_aceitacao_acordos = (acordos_aceitos / acordos_decididos) * 100
		
	# economia média por caso com acordo bem-sucedido
	economia_media_acordo = 0
	if acordos_aceitos:
		economia_media_acordo = total_economia_efetiva / acordos_aceitos
		
	context = {
		'total_casos': total,
		'acordos_sugeridos': acordos_sugeridos,
		'acordos_decididos': acordos_decididos,
		'acordos_aceitos': acordos_aceitos,
		'acordos_rejeitados': acordos_rejeitados,
		'acordos_sem_decisao': acordos_sem_decisao,
		'taxa_aceitacao_pct': round(taxa_aceitacao_acordos, 1),
		'economia_total_potencial': _format_currency(total_economia),
		'economia_total_efetiva': _format_currency(total_economia_efetiva),
		'economia_media_acordo': _format_currency(economia_media_acordo),
		'condenacoes_evitadas': _format_currency(total_condenacoes_evitadas),
		'rows': rows,
	}

	return render(request, 'legalapp/effectiveness_monitoring.html', context)
