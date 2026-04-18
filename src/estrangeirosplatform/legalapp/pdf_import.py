import re
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from .models import CaseDocument, LegalCase


DOC_TYPE_BY_FILENAME = {
    'autos': 'AUTOS_PROCESSO',
    'contrato': 'CONTRATO',
    'extrato': 'EXTRATO_BANCARIO',
    'bacen': 'COMPROVANTE_DE_CREDITO',
    'comprovante': 'COMPROVANTE_DE_CREDITO',
    'dossie': 'DOSSIE',
    'dosse': 'DOSSIE',
    'demonstrativo': 'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA',
    'evolucao': 'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA',
    'laudo': 'LAUDO_REFERENCIA',
}

CASE_FLAG_BY_DOC_TYPE = {
    'CONTRATO': 'has_contrato',
    'EXTRATO_BANCARIO': 'has_extrato',
    'COMPROVANTE_DE_CREDITO': 'has_comprovante_credito',
    'DOSSIE': 'has_dossie',
    'DEMONSTRATIVO_DE_EVOLUCAO_DA_DIVIDA': 'has_demonstrativo_evolucao_divida',
    'LAUDO_REFERENCIA': 'has_laudo_referenciado',
}

CNJ_DOTTED_RE = re.compile(r'(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})')
CNJ_HYPHEN_RE = re.compile(r'(\d{7})-(\d{2})-(\d{4})-(\d)-(\d{2})-(\d{4})')
MONEY_RE = re.compile(r'R\$\s*([0-9\.]{1,15},[0-9]{2})')


def normalize_numero_processo(text: str) -> str:
    text = (text or '').strip()

    dotted_match = CNJ_DOTTED_RE.search(text)
    if dotted_match:
        return dotted_match.group(0)

    hyphen_match = CNJ_HYPHEN_RE.search(text)
    if hyphen_match:
        return (
            f'{hyphen_match.group(1)}-{hyphen_match.group(2)}.'
            f'{hyphen_match.group(3)}.{hyphen_match.group(4)}.'
            f'{hyphen_match.group(5)}.{hyphen_match.group(6)}'
        )

    return ''


def infer_document_type(file_name: str) -> str:
    lowered = (file_name or '').lower()

    for token, document_type in DOC_TYPE_BY_FILENAME.items():
        if token in lowered:
            return document_type

    return 'AUTOS_PROCESSO'


def pdf_path_to_text(file_path: Path) -> tuple[str, int]:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or '' for page in reader.pages]
    return '\n\n'.join(pages), len(reader.pages)


def pdf_bytes_to_text(content: bytes) -> tuple[str, int]:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or '' for page in reader.pages]
    return '\n\n'.join(pages), len(reader.pages)


def text_file_to_text(file_path: Path) -> tuple[str, int]:
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = file_path.read_text(encoding='latin-1', errors='ignore')
    return content, 1


def docx_file_to_text(file_path: Path) -> tuple[str, int]:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError('Para ler arquivos DOCX instale a dependencia python-docx.') from exc

    document = Document(str(file_path))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    content = '\n'.join(paragraphs)
    return content, max(len(paragraphs), 1)


def image_file_to_text(file_path: Path) -> tuple[str, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('Para OCR em imagens instale a dependencia Pillow.') from exc

    try:
        import pytesseract
    except ImportError as exc:
        raise ValueError('Para OCR em imagens instale a dependencia pytesseract.') from exc

    try:
        image = Image.open(file_path)
        content = pytesseract.image_to_string(image, lang='por+eng')
        return content, 1
    except Exception as exc:
        raise ValueError(
            'Nao foi possivel executar OCR da imagem. Verifique se o Tesseract esta instalado no sistema.'
        ) from exc


def parse_decimal_brl(value: str) -> Decimal:
    normalized = value.replace('.', '').replace(',', '.').strip()
    try:
        return Decimal(normalized)
    except Exception:
        return Decimal('0')


def find_valor_causa(full_text: str) -> Decimal:
    patterns = [
        r'valor\s+da\s+causa[^R$]{0,80}R\$\s*([0-9\.]{1,15},[0-9]{2})',
        r'valor\s+causa[^R$]{0,80}R\$\s*([0-9\.]{1,15},[0-9]{2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return parse_decimal_brl(match.group(1))

    money_values = [parse_decimal_brl(m.group(1)) for m in MONEY_RE.finditer(full_text)]
    if money_values:
        return max(money_values)

    return Decimal('1000.00')


def infer_sub_assunto(full_text: str) -> str:
    lowered = full_text.lower()
    golpe_keywords = ['golpe', 'fraude', 'estelionato', 'nao reconhece']
    if any(keyword in lowered for keyword in golpe_keywords):
        return 'GOLPE'
    return 'GENERICO'


def build_summary_text(case: LegalCase, documents_payload: list[dict]) -> str:
    lines = [
        'EXTRACAO DE DADOS IMPORTANTES DO PROCESSO',
        '',
        f'Numero do processo: {case.numero_processo or "NAO ENCONTRADO"}',
        f'UF: {case.uf}',
        f'Assunto: {case.assunto}',
        f'Sub assunto: {case.sub_assunto}',
        f'Valor da causa: R$ {case.valor_causa}',
        '',
        'SUBSIDIOS IDENTIFICADOS:',
        f'- Contrato: {"SIM" if case.has_contrato else "NAO"}',
        f'- Extrato bancario: {"SIM" if case.has_extrato else "NAO"}',
        f'- Comprovante de credito: {"SIM" if case.has_comprovante_credito else "NAO"}',
        f'- Dossie: {"SIM" if case.has_dossie else "NAO"}',
        (
            '- Demonstrativo de evolucao da divida: '
            f'{"SIM" if case.has_demonstrativo_evolucao_divida else "NAO"}'
        ),
        f'- Laudo referenciado: {"SIM" if case.has_laudo_referenciado else "NAO"}',
        '',
        'DOCUMENTOS PROCESSADOS:',
    ]

    for payload in documents_payload:
        lines.append(
            '- '
            f'{payload["file_name"]} '
            f'| tipo: {payload["document_type"]} '
            f'| paginas: {payload["pages"]} '
            f'| caracteres extraidos: {payload["text_len"]}'
        )

    return '\n'.join(lines) + '\n'


def upsert_case_from_documents(
    documents_payload: list[dict],
    case_name_hint: str = '',
) -> tuple[LegalCase, str]:
    all_text_parts = [item['extracted_text'] for item in documents_payload]
    full_text = '\n\n'.join(all_text_parts)

    numero_processo = normalize_numero_processo(case_name_hint) or normalize_numero_processo(full_text)
    if not numero_processo:
        raise ValueError('Nao foi possivel identificar um numero CNJ valido.')

    legal_case, _created = LegalCase.objects.update_or_create(  # type: ignore[attr-defined]
        numero_processo=numero_processo,
        defaults={
            'uf': 'MG',
            'assunto': 'NAO_RECONHECE_OPERACAO',
            'sub_assunto': infer_sub_assunto(full_text),
            'valor_causa': find_valor_causa(full_text),
        },
    )

    for flag_name in CASE_FLAG_BY_DOC_TYPE.values():
        setattr(legal_case, flag_name, False)

    for payload in documents_payload:
        flag_name = CASE_FLAG_BY_DOC_TYPE.get(payload['document_type'])
        if flag_name:
            setattr(legal_case, flag_name, True)

        defaults = {
            'extracted_text': payload['extracted_text'][:50000],
            'metadata': {
                'source_path': payload.get('source_path', ''),
                'pages': payload['pages'],
                'text_length': payload['text_len'],
            },
        }
        if payload.get('file_path'):
            defaults['file_path'] = payload['file_path']

        CaseDocument.objects.update_or_create(  # type: ignore[attr-defined]
            case=legal_case,
            document_type=payload['document_type'],
            file_name=payload['file_name'],
            defaults=defaults,
        )

    legal_case.save()
    summary_text = build_summary_text(legal_case, documents_payload)
    return legal_case, summary_text


def extract_documents_from_directory(case_dir: Path) -> list[dict]:
    text_suffixes = {'.txt', '.text', '.md'}
    docx_suffixes = {'.docx'}
    image_suffixes = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}
    allowed_suffixes = {'.pdf'} | text_suffixes | docx_suffixes | image_suffixes
    candidate_files = sorted(
        f for f in case_dir.iterdir()
        if f.is_file() and f.suffix.lower() in allowed_suffixes
    )
    if not candidate_files:
        raise ValueError(f'Nenhum arquivo suportado encontrado em: {case_dir}')

    documents_payload = []
    for input_file in candidate_files:
        suffix = input_file.suffix.lower()
        if suffix == '.pdf':
            extracted_text, pages = pdf_path_to_text(input_file)
        elif suffix in text_suffixes:
            extracted_text, pages = text_file_to_text(input_file)
        elif suffix in docx_suffixes:
            extracted_text, pages = docx_file_to_text(input_file)
        elif suffix in image_suffixes:
            extracted_text, pages = image_file_to_text(input_file)
        else:
            raise ValueError(f'Tipo de arquivo nao suportado: {input_file.name}')

        documents_payload.append({
            'file_name': input_file.name,
            'file_path': str(input_file),
            'source_path': str(input_file),
            'document_type': infer_document_type(input_file.name),
            'extracted_text': extracted_text,
            'pages': pages,
            'text_len': len(extracted_text),
        })

    return documents_payload


def extract_documents_from_uploads(uploaded_files) -> list[dict]:
    documents_payload = []

    for upload in uploaded_files:
        file_name = upload.name
        extracted_text, pages = pdf_bytes_to_text(upload.read())
        upload.seek(0)

        documents_payload.append({
            'file_name': file_name,
            'source_path': f'upload:{file_name}',
            'document_type': infer_document_type(file_name),
            'extracted_text': extracted_text,
            'pages': pages,
            'text_len': len(extracted_text),
        })

    if not documents_payload:
        raise ValueError('Nenhum PDF foi enviado.')

    return documents_payload
