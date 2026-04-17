from django.db.models import Q
from django.db.models.functions import Cast
from django.shortcuts import render
from django.db.models import CharField

from .models import LegalCase


def legal_case_list(request):
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

	return render(request, 'legalapp/legalcases.html', {'cases': cases, 'query': query})
