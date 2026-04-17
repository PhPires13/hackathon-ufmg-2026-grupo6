from django.core.management.base import BaseCommand

from legalapp.agent.inference import generate_recommendations_for_queryset
from legalapp.models import LegalCase


class Command(BaseCommand):
    help = 'Gera ou atualiza recomendacoes de acordo/defesa para os casos cadastrados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--processo',
            type=str,
            default='',
            help='Numero CNJ de um processo especifico para gerar recomendacao.',
        )

    def handle(self, *args, **options):
        processo = (options.get('processo') or '').strip()

        queryset = LegalCase.objects.all()
        if processo:
            queryset = queryset.filter(numero_processo=processo)

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('Nenhum caso encontrado para gerar recomendacao.'))
            return

        count = generate_recommendations_for_queryset(queryset)
        self.stdout.write(self.style.SUCCESS(f'Recomendacoes geradas/atualizadas: {count}'))
