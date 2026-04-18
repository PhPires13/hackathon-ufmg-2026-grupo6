from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .views import gerar_recomendacao_caso
from .models import CaseRecommendation, LegalCase

logger = logging.getLogger(__name__)


@receiver(post_save, sender=LegalCase, dispatch_uid='legalcase_generate_recommendation_on_create')
def generate_recommendation_on_case_create(sender, instance: LegalCase, created: bool, **kwargs):
    if not created:
        return

    def _run_recommendation():
        try:
            gerar_recomendacao_caso(instance)
        except Exception:
            logger.exception('Failed to generate ML recommendation for LegalCase id=%s. Using fallback defaults.', instance.id)
            CaseRecommendation.objects.update_or_create(
                case=instance,
                defaults={
                    'probabilidade_perder_caso': Decimal('0.0000'),
                    'valor_esperado_condenacao': Decimal('0.00'),
                    'sugestao_acao': 'DEFENDER',
                    'valor_para_acordo': None,
                },
            )

    transaction.on_commit(_run_recommendation)


