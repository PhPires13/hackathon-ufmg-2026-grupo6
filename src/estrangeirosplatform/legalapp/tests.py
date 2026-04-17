from decimal import Decimal

from django.test import TestCase, override_settings

from .models import CaseDocument, CaseRecommendation, LegalCase


@override_settings(ROOT_URLCONF='legalapp.urls')
class LawyerAssistantViewTests(TestCase):
	def setUp(self):
		self.reference_case = LegalCase.objects.create(
			numero_processo='1764352-89.2025.8.06.1818',
			uf='MG',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GOLPE',
			resultado_macro='NAO_EXITO',
			resultado_micro='ACORDO',
			valor_causa=Decimal('10000.00'),
			valor_condenacao=Decimal('2500.00'),
			has_contrato=False,
			has_extrato=True,
			has_comprovante_credito=False,
			has_dossie=True,
			has_demonstrativo_evolucao_divida=False,
			has_laudo_referenciado=False,
		)

		self.target_case = LegalCase.objects.create(
			numero_processo='1764353-89.2025.8.06.1818',
			uf='MG',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GOLPE',
			resultado_macro='NAO_EXITO',
			resultado_micro='PROCEDENCIA',
			valor_causa=Decimal('12000.00'),
			valor_condenacao=Decimal('3500.00'),
			has_contrato=False,
			has_extrato=False,
			has_comprovante_credito=False,
			has_dossie=False,
			has_demonstrativo_evolucao_divida=False,
			has_laudo_referenciado=False,
		)

		CaseDocument.objects.create(
			case=self.target_case,
			document_type='EXTRATO_BANCARIO',
			file_name='extrato_jan_2026.pdf',
		)

		CaseRecommendation.objects.create(
			case=self.target_case,
			agente_classificacao_risco='modelo-risco-v1',
			probabilidade_perder_caso=Decimal('0.7200'),
			valor_esperado_condenacao=Decimal('4100.50'),
			agente_sugestao_acordo='modelo-acordo-v1',
			sugestao_acao='PROPOR_ACORDO',
			valor_para_acordo=Decimal('2800.75'),
		)

	def test_lawyer_assistant_shows_recommendation(self):
		response = self.client.get(
			'/assistente-advogado/',
			{'processo': self.target_case.numero_processo},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Decisao sugerida: ACORDO')
		self.assertContains(response, 'Recomendamos ACORDO pois')
		self.assertContains(response, 'R$ 2.800,75')
		self.assertContains(response, 'extrato_jan_2026.pdf')

	def test_lawyer_assistant_returns_error_for_unknown_case(self):
		response = self.client.get('/assistente-advogado/', {'processo': '0000000-00.0000.0.00.0000'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Processo nao encontrado ou sem recomendacao cadastrada.')
