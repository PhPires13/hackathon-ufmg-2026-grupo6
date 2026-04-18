from django.db.models import Q
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import CharField
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from .forms import LawyerActionCreateForm
from .models import LegalCase


def legal_cases_page(request):
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
		context['cases_url'] = reverse('legalapp:legal-cases')

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


