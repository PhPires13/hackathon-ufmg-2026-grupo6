from django.shortcuts import render

from .models import CaseDocument, CaseRecommendation, LegalCase


DOCUMENT_EVIDENCE_LABELS = {
	'CONTRATO': 'Contrato juntado aos autos',
	'EXTRATO_BANCARIO': 'Extrato bancario com movimentacoes',
	'COMPROVANTE_DE_CREDITO': 'Comprovante de credito apresentado',
	'DOSSIE': 'Dossie complementar anexado',
	'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA': 'Demonstrativo de evolucao da divida anexado',
	'LAUDO_REFERENCIA': 'Laudo de referencia inserido',
}


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


def lawyer_assistant_view(request):
	case_number = (request.GET.get('processo') or '').strip()
	recommendation = None
	lookup_error = None

	if case_number:
		recommendation = (
			CaseRecommendation.objects.select_related('case')
			.filter(case__numero_processo=case_number)
			.first()
		)
		if recommendation is None:
			lookup_error = 'Processo nao encontrado ou sem recomendacao cadastrada.'
	else:
		recommendation = CaseRecommendation.objects.select_related('case').first()
		if recommendation is None:
			lookup_error = 'Nao ha recomendacoes cadastradas para exibir na interface.'

	context = {
		'case_number': case_number,
		'lookup_error': lookup_error,
		'assistant_data': None,
	}

	if recommendation:
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
		}

	return render(request, 'legalapp/lawyer_assistant.html', context)
