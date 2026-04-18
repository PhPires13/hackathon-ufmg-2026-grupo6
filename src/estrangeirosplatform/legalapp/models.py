from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
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

ACTION_CHOICES = (
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
		validators=[
			RegexValidator(
				regex=r'^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$',
				message='Número do processo deve seguir o padrão CNJ (ex: 1764352-89.2025.8.06.1818).',
			)
		],
	)
	uf = models.CharField(max_length=2, null=True, choices=UF_CHOICES)
	assunto = models.CharField(
		max_length=64,
		null = True,
		choices=ASSUNTO_CHOICES,
		default='NAO_RECONHECE_OPERACAO',
	)
	sub_assunto = models.CharField(max_length=20, null=True, choices=SUB_ASSUNTO_CHOICES)
	valor_causa = models.DecimalField(max_digits=10, decimal_places=2, null=True)

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
	sugestao_acao = models.CharField(max_length=13, choices=ACTION_CHOICES)
	valor_para_acordo = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		null=True,
		validators=[MinValueValidator(0)],
	)
	insight_ia = models.TextField(blank=True, default='')

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.case.numero_processo} - {self.sugestao_acao}'


class LawyerAction(TimeStampedModel):
	case = models.OneToOneField(
		LegalCase,
		on_delete=models.CASCADE,
		related_name='action',
	)
	acao = models.CharField(max_length=13, choices=ACTION_CHOICES)

	# IF acao = PROPOR_ACORDO
	valor_acordo = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		null=True,
		validators=[MinValueValidator(0)],
	)

	# IF acao = DEFENDER
	resultado_macro = models.CharField(max_length=12, null=True, choices=RESULTADO_MACRO_CHOICES)
	resultado_micro = models.CharField(max_length=24, null=True, choices=RESULTADO_MICRO_CHOICES)
	valor_condenacao = models.DecimalField(max_digits=10, decimal_places=2, null=True)

	# Compare against recommendation
	same_action_taken = models.BooleanField()
	valor_acordo_in_range = models.BooleanField(null=True)
	shift_valor_acordo = models.DecimalField(max_digits=10, decimal_places=2, null=True)

	class Meta:
		ordering = ['-created_at']

	def _calculate_recommendation_alignment(self):
		try:
			recommendation = self.case.recommendation
		except ObjectDoesNotExist:
			recommendation = None

		if recommendation is None:
			self.same_action_taken = False
			self.valor_acordo_in_range = None
			self.shift_valor_acordo = None
			return

		self.same_action_taken = (self.acao == recommendation.sugestao_acao)

		if (
			self.acao == 'PROPOR_ACORDO'
			and recommendation.sugestao_acao == 'PROPOR_ACORDO'
			and self.valor_acordo is not None
			and recommendation.valor_para_acordo is not None
		):
			valor_recomendado = recommendation.valor_para_acordo
			limite_inferior = valor_recomendado * Decimal('0.80')
			limite_superior = valor_recomendado * Decimal('1.20')
			self.valor_acordo_in_range = limite_inferior <= self.valor_acordo <= limite_superior
			if valor_recomendado != 0:
				self.shift_valor_acordo = ((self.valor_acordo - valor_recomendado) / valor_recomendado) * Decimal('100')
			else:
				self.shift_valor_acordo = None
		else:
			self.valor_acordo_in_range = None
			self.shift_valor_acordo = None

	def save(self, *args, **kwargs):
		self._calculate_recommendation_alignment()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.case.numero_processo} - {self.acao}'
