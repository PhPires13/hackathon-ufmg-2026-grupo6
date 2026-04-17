from django.core.validators import RegexValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


CASE_DOCUMENT_TYPE_CHOICES = (
	('AUTOS_PROCESSO', 'AUTOS_PROCESSO'),
	('CONTRATO', 'CONTRATO'),
	('EXTRATO_BANCARIO', 'EXTRATO_BANCARIO'),
	('COMPROVANTE_DE_CREDITO', 'COMPROVANTE_DE_CREDITO'),
	('DOSSIE', 'DOSSIE'),
	('DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA', 'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA'),
	('LAUDO_REFERENCIA', 'LAUDO_REFERENCIA'),
)

RECOMMENDATION_ACTION_CHOICES = (
	('DEFENDER', 'DEFENDER'),
	('PROPOR_ACORDO', 'PROPOR_ACORDO')
)

UF_CHOICES = (
	('AC', 'AC'),
	('AL', 'AL'),
	('AM', 'AM'),
	('AP', 'AP'),
	('BA', 'BA'),
	('CE', 'CE'),
	('DF', 'DF'),
	('ES', 'ES'),
	('GO', 'GO'),
	('MA', 'MA'),
	('MG', 'MG'),
	('MS', 'MS'),
	('MT', 'MT'),
	('PA', 'PA'),
	('PB', 'PB'),
	('PE', 'PE'),
	('PI', 'PI'),
	('PR', 'PR'),
	('RJ', 'RJ'),
	('RN', 'RN'),
	('RO', 'RO'),
	('RS', 'RS'),
	('SC', 'SC'),
	('SE', 'SE'),
	('SP', 'SP'),
	('TO', 'TO'),
)

ASSUNTO_CHOICES = (
	('NAO_RECONHECE_OPERACAO', 'NAO_RECONHECE_OPERACAO'),
)

SUB_ASSUNTO_CHOICES = (
	('GENERICO', 'GENERICO'),
	('GOLPE', 'GOLPE'),
)

RESULTADO_MACRO_CHOICES = (
	('NAO_EXITO', 'NAO_EXITO'),
	('EXITO', 'EXITO'),
)

RESULTADO_MICRO_CHOICES = (
	('ACORDO', 'ACORDO'),
	('EXTINCAO', 'EXTINCAO'),
	('IMPROCEDENCIA', 'IMPROCEDENCIA'),
	('PARCIAL_PROCEDENCIA', 'PARCIAL_PROCEDENCIA'),
	('PROCEDENCIA', 'PROCEDENCIA'),
)


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class LegalCase(TimeStampedModel):
	numero_processo = models.CharField(
		max_length=25,
		unique=True,
		null=True,
		blank=True,
		validators=[
			RegexValidator(
				regex=r'^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$',
				message='Número do processo deve seguir o padrão CNJ (ex: 1764352-89.2025.8.06.1818).',
			)
		],
	)
	uf = models.CharField(max_length=2, choices=UF_CHOICES)
	assunto = models.CharField(
		max_length=64,
		choices=ASSUNTO_CHOICES,
		default='NAO_RECONHECE_OPERACAO',
	)
	sub_assunto = models.CharField(max_length=20, choices=SUB_ASSUNTO_CHOICES)
	resultado_macro = models.CharField(max_length=12, choices=RESULTADO_MACRO_CHOICES)
	resultado_micro = models.CharField(max_length=24, choices=RESULTADO_MICRO_CHOICES)
	valor_causa = models.DecimalField(max_digits=10, decimal_places=2)
	valor_condenacao = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	# Subsídios disponibilizados para o caso.
	has_contrato = models.BooleanField(default=False)
	has_extrato = models.BooleanField(default=False)
	has_comprovante_credito = models.BooleanField(default=False)
	has_dossie = models.BooleanField(default=False)
	has_demonstrativo_evolucao_divida = models.BooleanField(default=False)
	has_laudo_referenciado = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.numero_processo


class CaseDocument(TimeStampedModel):
	case = models.ForeignKey(
		LegalCase,
		on_delete=models.CASCADE,
		related_name='documents',
	)
	document_type = models.CharField(max_length=40, choices=CASE_DOCUMENT_TYPE_CHOICES)
	file_name = models.CharField(max_length=255)
	file_path = models.FileField(upload_to='legalapp/documents/', blank=True, null=True)
	extracted_text = models.TextField(blank=True, default='')
	metadata = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['case_id', 'document_type', 'file_name']
		constraints = [
			models.UniqueConstraint(
				fields=['case', 'document_type', 'file_name'],
				name='unique_case_document_entry',
			)
		]

	def __str__(self):
		return f'{self.case.numero_processo} - {self.document_type}'


class CaseRecommendation(TimeStampedModel):
	case = models.OneToOneField(
		LegalCase,
		on_delete=models.CASCADE,
		related_name='recommendation',
	)
	agente_classificacao_risco = models.CharField(max_length=120)
	probabilidade_perder_caso = models.DecimalField(
		max_digits=5,
		decimal_places=4,
		validators=[MinValueValidator(0), MaxValueValidator(1)],
	)
	valor_esperado_condenacao = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	agente_sugestao_acordo = models.CharField(max_length=120)
	sugestao_acao = models.CharField(max_length=13, choices=RECOMMENDATION_ACTION_CHOICES)
	valor_para_acordo = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.case.numero_processo} - {self.sugestao_acao}'
