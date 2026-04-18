# Setup e Execucao

Guia completo para instalar e rodar a solucao Django localmente.

---

## Pre-requisitos

- Python 3.11+ (recomendado)
- `pip` habilitado
- Linux/macOS/WSL ou Windows com terminal
- (Opcional) `tesseract-ocr` no sistema para OCR em PDFs escaneados

Exemplo de instalacao do Tesseract no Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

## Variaveis de ambiente

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

2. Preencha o `.env` com os valores necessarios:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Observacoes:
- O backend atual roda sem chave OpenAI para o fluxo principal de telas e importacoes.
- Nunca versione o arquivo `.env` com credenciais reais.

## Instalacao

Na raiz do repositorio:

```bash
# 1) criar ambiente virtual
python3 -m venv .venv

# 2) ativar ambiente virtual
source .venv/bin/activate

# 3) instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

## Inicializacao do banco (migrate)

Os comandos Django devem ser executados na pasta do projeto Django:

```bash
cd src/estrangeirosplatform

# aplicar migracoes
python manage.py migrate
```

Opcional (trocar nome do arquivo sqlite):

```bash
DJANGO_DB_NAME=db_alt.sqlite3 python manage.py migrate
```

## Carga de dados

Coloque os arquivos do hackathon em `data/` seguindo o padrao descrito em [data/README.md](data/README.md).

### 1) Importar casos a partir de documentos (PDF/TXT)

Comando disponivel no projeto: `import_case_from_pdfs`.

```bash
cd src/estrangeirosplatform

# exemplo: importar um caso de uma pasta contendo autos/subsidios
python manage.py import_case_from_pdfs --case-dir ../../data/processos_exemplo/processo_01

# opcional: definir arquivo de resumo de saida
python manage.py import_case_from_pdfs \
  --case-dir ../../data/processos_exemplo/processo_01 \
  --output-txt ../../data/processos_exemplo/processo_01/extracao_dados_importantes.txt
```

### 2) Importar acoes/resultados do advogado via CSV

Comando disponivel no projeto: `import_lawyer_actions_from_sentencas`.

```bash
cd src/estrangeirosplatform

# usa data/sentencas.csv por padrao
python manage.py import_lawyer_actions_from_sentencas

# ou apontar outro arquivo
python manage.py import_lawyer_actions_from_sentencas --csv-path ../../data/sentencas.csv
```

Importante:
- Esse comando vincula os registros pelo numero do processo.
- Portanto, primeiro importe/crie os `LegalCase` no banco (por exemplo, via `import_case_from_pdfs`).

### 3) (Opcional) Popular base de teste rapida

```bash
cd src/estrangeirosplatform
python manage.py shell < populate_test_data.py
```

## Execucao (runserver)

Com o ambiente virtual ativado:

```bash
cd src/estrangeirosplatform
python manage.py runserver
```

Acesse no navegador:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/admin/

## Fluxo rapido (do zero)

```bash
# raiz do repositorio
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env

cd src/estrangeirosplatform
python manage.py migrate
python manage.py import_case_from_pdfs --case-dir ../../data/processos_exemplo/processo_01
python manage.py import_lawyer_actions_from_sentencas --csv-path ../../data/sentencas.csv
python manage.py runserver
```

## Dashboard analitico (opcional)

```bash
cd temp/enter-dashboard
pip install -r requirements.txt
streamlit run app.py
```

Abrir em http://localhost:8501.

## Troubleshooting

- Erro `ModuleNotFoundError: No module named 'django'`:
  ative o ambiente virtual e reinstale dependencias.
- Erro de arquivo CSV nao encontrado:
  valide o caminho informado em `--csv-path`.
- Erro de pasta de caso nao encontrada:
  valide o caminho informado em `--case-dir`.
- Porta ocupada no `runserver`:

```bash
python manage.py runserver 0.0.0.0:8001
```

## Estrutura do projeto

```text
.
├── src/                  # codigo-fonte
│   └── estrangeirosplatform/
│       ├── manage.py
│       └── legalapp/
├── data/                 # dados do hackathon
├── temp/enter-dashboard/ # dashboard Streamlit
├── docs/                 # apresentacao e documentacao
├── .env.example          # exemplo de variaveis de ambiente
├── requirements.txt      # dependencias Python
└── SETUP.md              # este guia
```
