from __future__ import annotations

import csv
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from legalapp.models import LegalCase, LawyerAction
from legalapp.pdf_import import normalize_numero_processo


def _strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text or '')
        if not unicodedata.combining(c)
    )


def _normalize_text(text: str) -> str:
    return _strip_accents((text or '').strip()).upper()


def _parse_decimal(raw: str) -> Decimal | None:
    value = (raw or '').strip().replace(' ', '')
    if not value:
        return None

    filtered = ''.join(ch for ch in value if ch.isdigit() or ch in ',.-')
    if not filtered:
        return None

    if ',' in filtered and '.' in filtered:
        if filtered.rfind(',') > filtered.rfind('.'):
            filtered = filtered.replace('.', '').replace(',', '.')
        else:
            filtered = filtered.replace(',', '')
    elif ',' in filtered:
        right = filtered.split(',')[-1]
        if len(right) == 2:
            filtered = filtered.replace('.', '').replace(',', '.')
        else:
            filtered = filtered.replace(',', '')

    try:
        return Decimal(filtered)
    except InvalidOperation:
        return None


def _map_resultado_macro(raw: str) -> str | None:
    text = _normalize_text(raw)
    if not text:
        return None
    if 'NAO EXITO' in text or 'NAO_EXITO' in text:
        return 'NAO_EXITO'
    if 'EXITO' in text:
        return 'EXITO'
    return None


def _map_resultado_micro(raw: str) -> str | None:
    text = _normalize_text(raw)
    if not text:
        return None
    if 'ACORDO' in text:
        return 'ACORDO'
    if 'EXTINC' in text:
        return 'EXTINCAO'
    if 'IMPROCED' in text:
        return 'IMPROCEDENCIA'
    if 'PARCIAL' in text:
        return 'PARCIAL_PROCEDENCIA'
    if 'PROCED' in text:
        return 'PROCEDENCIA'
    return None


def _find_first(row: dict, candidates: list[str]) -> str:
    lowered = {k.lower().strip(): v for k, v in row.items()}
    for key in candidates:
        if key in lowered and lowered[key] is not None:
            return str(lowered[key])
    return ''


class Command(BaseCommand):
    help = (
        'Carrega acoes do advogado (LawyerAction) a partir de sentencas.csv '
        'ou outro CSV de resultados, vinculando por numero de processo.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='../../data/sentencas.csv',
            help='Caminho para CSV com resultados dos processos.',
        )

    def handle(self, *args, **options):
        csv_path_raw = (options.get('csv_path') or '').strip()
        if not csv_path_raw:
            raise CommandError('Informe --csv-path com um arquivo CSV valido.')

        csv_path = Path(csv_path_raw).expanduser()
        if not csv_path.is_absolute():
            csv_path = (Path(settings.BASE_DIR) / csv_path).resolve()

        if not csv_path.exists() or not csv_path.is_file():
            raise CommandError(f'Arquivo CSV nao encontrado: {csv_path}')

        if csv_path.stat().st_size == 0:
            raise CommandError(
                f'CSV vazio: {csv_path}. Coloque os dados reais antes de importar LawyerAction.'
            )

        with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError(f'CSV sem cabecalho: {csv_path}')

            created = 0
            updated = 0
            skipped_missing_case = 0
            skipped_invalid_process = 0
            skipped_invalid_value = 0

            for row in reader:
                raw_numero = _find_first(
                    row,
                    ['numero do processo', 'numero_processo', 'número do processo'],
                )
                numero = normalize_numero_processo(raw_numero)
                if not numero:
                    skipped_invalid_process += 1
                    continue

                try:
                    legal_case = LegalCase.objects.select_related('recommendation').get(
                        numero_processo=numero,
                    )
                except LegalCase.DoesNotExist:
                    skipped_missing_case += 1
                    continue

                macro = _map_resultado_macro(_find_first(row, ['resultado macro', 'resultado_macro']))
                micro = _map_resultado_micro(_find_first(row, ['resultado micro', 'resultado_micro']))
                valor = _parse_decimal(
                    _find_first(
                        row,
                        [
                            'valor da condenacao/indenizacao',
                            'valor da condenação/indenização',
                            'valor_condenacao',
                        ],
                    )
                )

                if valor is None:
                    skipped_invalid_value += 1
                    continue

                acao = 'PROPOR_ACORDO' if micro == 'ACORDO' else 'DEFENDER'

                defaults = {
                    'acao': acao,
                    'valor_acordo': None,
                    'resultado_macro': None,
                    'resultado_micro': None,
                    'valor_condenacao': None,
                    'same_action_taken': False,
                    'valor_acordo_in_range': None,
                    'shift_valor_acordo': None,
                }

                if acao == 'PROPOR_ACORDO':
                    defaults['valor_acordo'] = valor
                else:
                    defaults['resultado_macro'] = macro or 'NAO_EXITO'
                    defaults['resultado_micro'] = micro or 'PARCIAL_PROCEDENCIA'
                    defaults['valor_condenacao'] = valor

                recommendation = getattr(legal_case, 'recommendation', None)
                if recommendation is not None:
                    defaults['same_action_taken'] = (acao == recommendation.sugestao_acao)
                    if (
                        acao == 'PROPOR_ACORDO'
                        and recommendation.sugestao_acao == 'PROPOR_ACORDO'
                        and defaults['valor_acordo'] is not None
                        and recommendation.valor_para_acordo is not None
                    ):
                        valor_recomendado = recommendation.valor_para_acordo
                        limite_inferior = valor_recomendado * Decimal('0.80')
                        limite_superior = valor_recomendado * Decimal('1.20')
                        defaults['valor_acordo_in_range'] = (
                            limite_inferior <= defaults['valor_acordo'] <= limite_superior
                        )
                        defaults['shift_valor_acordo'] = defaults['valor_acordo'] - valor_recomendado

                _obj, was_created = LawyerAction.objects.update_or_create(
                    case=legal_case,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS('Importacao concluida para LawyerAction.'))
        self.stdout.write(f'Arquivo lido: {csv_path}')
        self.stdout.write(f'Criados: {created}')
        self.stdout.write(f'Atualizados: {updated}')
        self.stdout.write(f'Ignorados (processo inexistente no LegalCase): {skipped_missing_case}')
        self.stdout.write(f'Ignorados (numero CNJ invalido): {skipped_invalid_process}')
        self.stdout.write(f'Ignorados (valor condenacao invalido): {skipped_invalid_value}')
