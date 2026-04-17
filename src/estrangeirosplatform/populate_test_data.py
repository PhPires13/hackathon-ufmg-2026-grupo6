#!/usr/bin/env python
"""
Script para popular banco de dados com casos de teste.
Executar: python manage.py shell < populate_test_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estrangeirosplatform.settings')
django.setup()

from decimal import Decimal
from legalapp.models import LegalCase, CaseRecommendation, CaseDocument

# Limpar dados anteriores (opcional)
LegalCase.objects.all().delete()

# Caso 1: Acordo sugerido e realizado (com valor próximo)
case1 = LegalCase.objects.create(
    numero_processo='1764353-89.2025.8.06.1818',
    uf='MG',
    assunto='NAO_RECONHECE_OPERACAO',
    sub_assunto='GOLPE',
    resultado_macro='NAO_EXITO',
    resultado_micro='ACORDO',
    valor_causa=Decimal('15000.00'),
    valor_condenacao=Decimal('2100.00'),
    has_contrato=False,
    has_extrato=True,
    has_comprovante_credito=True,
    has_dossie=True,
    has_demonstrativo_evolucao_divida=False,
    has_laudo_referenciado=False,
)

CaseRecommendation.objects.create(
    case=case1,
    agente_classificacao_risco='modelo-risco-v2',
    probabilidade_perder_caso=Decimal('0.6500'),
    valor_esperado_condenacao=Decimal('4200.00'),
    agente_sugestao_acordo='modelo-acordo-v2',
    sugestao_acao='PROPOR_ACORDO',
    valor_para_acordo=Decimal('2000.00'),
)

CaseDocument.objects.create(
    case=case1,
    document_type='EXTRATO_BANCARIO',
    file_name='extrato_conta_empresa_jan_2026.pdf',
)

CaseDocument.objects.create(
    case=case1,
    document_type='COMPROVANTE_DE_CREDITO',
    file_name='comprovante_transferencia_01032026.pdf',
)

print("✓ Caso 1 criado: Acordo sugerido e realizado")

# Caso 2: Defesa sugerida (sem resultado de acordo)
case2 = LegalCase.objects.create(
    numero_processo='1764354-89.2025.8.06.1819',
    uf='SP',
    assunto='NAO_RECONHECE_OPERACAO',
    sub_assunto='GENERICO',
    resultado_macro='EXITO',
    resultado_micro='PROCEDENCIA',
    valor_causa=Decimal('12000.00'),
    valor_condenacao=Decimal('0.00'),
    has_contrato=True,
    has_extrato=True,
    has_comprovante_credito=False,
    has_dossie=True,
    has_demonstrativo_evolucao_divida=True,
    has_laudo_referenciado=False,
)

CaseRecommendation.objects.create(
    case=case2,
    agente_classificacao_risco='modelo-risco-v2',
    probabilidade_perder_caso=Decimal('0.2200'),
    valor_esperado_condenacao=Decimal('500.00'),
    agente_sugestao_acordo='modelo-acordo-v2',
    sugestao_acao='DEFENDER',
    valor_para_acordo=Decimal('0.00'),
)

CaseDocument.objects.create(
    case=case2,
    document_type='CONTRATO',
    file_name='contrato_assinado_15022021.pdf',
)

CaseDocument.objects.create(
    case=case2,
    document_type='DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA',
    file_name='evolucao_divida_2021_2026.xlsx',
)

print("✓ Caso 2 criado: Defesa sugerida (sucesso em procedência)")

# Caso 3: Acordo sugerido mas não realizado
case3 = LegalCase.objects.create(
    numero_processo='1764355-89.2025.8.06.1820',
    uf='RJ',
    assunto='NAO_RECONHECE_OPERACAO',
    sub_assunto='GOLPE',
    resultado_macro='NAO_EXITO',
    resultado_micro='IMPROCEDENCIA',
    valor_causa=Decimal('8000.00'),
    valor_condenacao=Decimal('0.00'),
    has_contrato=False,
    has_extrato=False,
    has_comprovante_credito=False,
    has_dossie=False,
    has_demonstrativo_evolucao_divida=False,
    has_laudo_referenciado=False,
)

CaseRecommendation.objects.create(
    case=case3,
    agente_classificacao_risco='modelo-risco-v2',
    probabilidade_perder_caso=Decimal('0.7800'),
    valor_esperado_condenacao=Decimal('3500.00'),
    agente_sugestao_acordo='modelo-acordo-v2',
    sugestao_acao='PROPOR_ACORDO',
    valor_para_acordo=Decimal('1500.00'),
)

print("✓ Caso 3 criado: Acordo sugerido mas não realizado")

print("\n✅ Dados de teste populados com sucesso!")
print("\nAcesse os dashboards:")
print("  - Assistente: http://127.0.0.1:8000/assistente-advogado/?processo=1764353-89.2025.8.06.1818")
print("  - Monitoramento: http://127.0.0.1:8000/monitoramento-aderencia/")
