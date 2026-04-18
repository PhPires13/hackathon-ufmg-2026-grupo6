from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from legalapp.pdf_import import extract_documents_from_directory, upsert_case_from_documents


class Command(BaseCommand):
    help = (
        'Le a pasta de um processo com PDFs, extrai dados importantes, '
        'salva no banco e gera um arquivo TXT com o resumo.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--case-dir',
            type=str,
            default='../../Caso_01_0801234-56-2024-8-10-0001',
            help='Caminho para a pasta do caso com os arquivos PDF.',
        )
        parser.add_argument(
            '--output-txt',
            type=str,
            default='',
            help='Caminho completo do TXT de saida. Se vazio, salva dentro da pasta do caso.',
        )

    def handle(self, *args, **options):
        case_dir_raw = (options.get('case_dir') or '').strip()
        output_txt_raw = (options.get('output_txt') or '').strip()

        if not case_dir_raw:
            raise CommandError('Informe --case-dir com a pasta contendo os PDFs.')

        case_dir = Path(case_dir_raw).expanduser().resolve()
        if not case_dir.exists() or not case_dir.is_dir():
            raise CommandError(f'Pasta do caso nao encontrada: {case_dir}')

        try:
            extracted_documents = extract_documents_from_directory(case_dir)
            legal_case, summary_text = upsert_case_from_documents(
                documents_payload=extracted_documents,
                case_name_hint=case_dir.name,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        output_path = (
            Path(output_txt_raw).expanduser().resolve()
            if output_txt_raw
            else case_dir / 'extracao_dados_importantes.txt'
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary_text, encoding='utf-8')

        self.stdout.write(f'Caso processado: {legal_case.numero_processo}')
        self.stdout.write(f'Documentos importados: {len(extracted_documents)}')
        self.stdout.write(f'TXT gerado em: {output_path}')
