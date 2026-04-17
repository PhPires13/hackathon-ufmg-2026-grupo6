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


@override_settings(ROOT_URLCONF='legalapp.urls')
class AdherenceMonitoringViewTests(TestCase):
	def _make_case(self, numero, resultado_micro, valor_condenacao):
		return LegalCase.objects.create(
			numero_processo=numero,
			uf='MG',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GOLPE',
			resultado_macro='NAO_EXITO',
			resultado_micro=resultado_micro,
			valor_causa=Decimal('10000.00'),
			valor_condenacao=valor_condenacao,
		)

	def _make_recommendation(self, case, sugestao_acao, valor_para_acordo):
		return CaseRecommendation.objects.create(
			case=case,
			agente_classificacao_risco='modelo-risco-v1',
			probabilidade_perder_caso=Decimal('0.6000'),
			valor_esperado_condenacao=Decimal('3000.00'),
			agente_sugestao_acordo='modelo-acordo-v1',
			sugestao_acao=sugestao_acao,
			valor_para_acordo=valor_para_acordo,
		)

	def setUp(self):
		# Caso 1: sugeriu ACORDO, fez ACORDO, valor proximo (5% desvio)
		case1 = self._make_case('1000001-00.2025.8.06.0001', 'ACORDO', Decimal('2100.00'))
		self._make_recommendation(case1, 'PROPOR_ACORDO', Decimal('2000.00'))

		# Caso 2: sugeriu ACORDO, nao fez ACORDO (nao aderiu)
		case2 = self._make_case('1000002-00.2025.8.06.0001', 'IMPROCEDENCIA', Decimal('0.00'))
		self._make_recommendation(case2, 'PROPOR_ACORDO', Decimal('1500.00'))

		# Caso 3: sugeriu DEFESA, nao fez ACORDO (aderiu)
		case3 = self._make_case('1000003-00.2025.8.06.0001', 'IMPROCEDENCIA', Decimal('0.00'))
		self._make_recommendation(case3, 'DEFENDER', Decimal('0.00'))

	def test_adherence_monitoring_renders(self):
		response = self.client.get('/monitoramento-aderencia/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Monitoramento de Aderencia')

	def test_adherence_metrics_are_correct(self):
		response = self.client.get('/monitoramento-aderencia/')
		ctx = response.context

		# 3 casos com recomendacao
		self.assertEqual(ctx['total'], 3)
		# caso1 (acordo aderiu) + caso3 (defesa aderiu) = 2
		self.assertEqual(ctx['aderiu_count'], 2)
		# caso2 nao aderiu
		self.assertEqual(ctx['nao_aderiu_count'], 1)
		# aderencia = 2/3 = 66.7%
		self.assertAlmostEqual(ctx['aderencia_pct'], 66.7, places=0)

	def test_acordo_sugerido_e_feito(self):
		response = self.client.get('/monitoramento-aderencia/')
		ctx = response.context

		# apenas caso1 sugeriu e fez acordo
		self.assertEqual(ctx['acordo_sugerido_e_feito'], 1)

	def test_valor_proximo_do_sugerido(self):
		response = self.client.get('/monitoramento-aderencia/')
		ctx = response.context

		# caso1: desvio 5% (dentro do threshold de 20%) -> proximo
		self.assertEqual(ctx['valores_proximos'], 1)
		self.assertEqual(ctx['acordos_com_valor_avaliavel'], 1)
		self.assertAlmostEqual(ctx['valor_proximo_pct'], 100.0, places=0)


@override_settings(ROOT_URLCONF='legalapp.urls')
class EffectivenessMonitoringViewTests(TestCase):
	def setUp(self):
		# Caso 1: Acordo sugerido e aceito com economia
		case1 = LegalCase.objects.create(
			numero_processo='2000001-00.2025.8.06.0001',
			uf='MG',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GOLPE',
			resultado_macro='NAO_EXITO',
			resultado_micro='ACORDO',
			valor_causa=Decimal('10000.00'),
			valor_condenacao=Decimal('2200.00'),
		)
		CaseRecommendation.objects.create(
			case=case1,
			agente_classificacao_risco='modelo-risco-v1',
			probabilidade_perder_caso=Decimal('0.6500'),
			valor_esperado_condenacao=Decimal('5000.00'),
			agente_sugestao_acordo='modelo-acordo-v1',
			sugestao_acao='PROPOR_ACORDO',
			valor_para_acordo=Decimal('2500.00'),
		)

		# Caso 2: Acordo sugerido mas rejeitado
		case2 = LegalCase.objects.create(
			numero_processo='2000002-00.2025.8.06.0001',
			uf='SP',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GOLPE',
			resultado_macro='NAO_EXITO',
			resultado_micro='IMPROCEDENCIA',
			valor_causa=Decimal('8000.00'),
			valor_condenacao=Decimal('0.00'),
		)
		CaseRecommendation.objects.create(
			case=case2,
			agente_classificacao_risco='modelo-risco-v1',
			probabilidade_perder_caso=Decimal('0.7500'),
			valor_esperado_condenacao=Decimal('4500.00'),
			agente_sugestao_acordo='modelo-acordo-v1',
			sugestao_acao='PROPOR_ACORDO',
			valor_para_acordo=Decimal('2000.00'),
		)

		# Caso 3: Defesa sugerida e mantida (condenacao evitada)
		case3 = LegalCase.objects.create(
			numero_processo='2000003-00.2025.8.06.0001',
			uf='RJ',
			assunto='NAO_RECONHECE_OPERACAO',
			sub_assunto='GENERICO',
			resultado_macro='EXITO',
			resultado_micro='PROCEDENCIA',
			valor_causa=Decimal('7000.00'),
			valor_condenacao=Decimal('0.00'),
		)
		CaseRecommendation.objects.create(
			case=case3,
			agente_classificacao_risco='modelo-risco-v1',
			probabilidade_perder_caso=Decimal('0.3000'),
			valor_esperado_condenacao=Decimal('3000.00'),
			agente_sugestao_acordo='modelo-acordo-v1',
			sugestao_acao='DEFENDER',
			valor_para_acordo=Decimal('0.00'),
		)

	def test_effectiveness_monitoring_renders(self):
		response = self.client.get('/monitoramento-efetividade/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Monitoramento de Efetividade')

	def test_acceptance_rate_calculation(self):
		response = self.client.get('/monitoramento-efetividade/')
		ctx = response.context

		# 2 acordos sugeridos, 1 aceito = 50%
		self.assertEqual(ctx['acordos_sugeridos'], 2)
		self.assertEqual(ctx['acordos_aceitos'], 1)
		self.assertEqual(ctx['acordos_rejeitados'], 1)
		self.assertAlmostEqual(ctx['taxa_aceitacao_pct'], 50.0, places=0)

	def test_estimated_savings_calculation(self):
		response = self.client.get('/monitoramento-efetividade/')
		ctx = response.context

		# Caso 1: 5000 (esperado) - 2200 (realizado) = 2800 economia efetiva
		# Caso 2: acordo rejeitado, nao conta economia efetiva
		# Caso 3: 3000 (esperado) - 0 (realizado) = 3000 economia (defesa bem-sucedida)
		# Total efetivo: 2800 + 3000 = 5800
		self.assertIn('5', ctx['economia_total_efetiva'])  # R$ 5.800,00

	def test_damage_reduction(self):
		response = self.client.get('/monitoramento-efetividade/')
		ctx = response.context

		# Condenacoes evitadas: Caso 3 (defesa bem-sucedida) = 3000
		self.assertIn('3', ctx['condenacoes_evitadas'])
