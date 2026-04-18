# Setup e Execucao

Guia minimo para instalar as dependencias e subir o backend Django localmente.

## Pre-requisitos

- Python 3.11+
- pip
- venv

## Passo a passo

Na raiz do repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Como o agente de IA usa a API da OpenAI, configure a chave antes de subir o projeto:

```bash
cp .env.example .env
```

No arquivo `.env`, preencha pelo menos:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Depois entre na pasta do projeto Django e execute as migracoes:

```bash
cd src/estrangeirosplatform
python manage.py migrate
```

Em seguida, inicie o servidor local:

```bash
python manage.py runserver
```

Acesso local:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/admin/

## Fluxo rapido

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env

cd src/estrangeirosplatform
python manage.py migrate
python manage.py runserver
```

## Troubleshooting

- `ModuleNotFoundError: No module named 'django'`:
  ative o ambiente virtual e reinstale as dependencias.
- Funcionalidades com IA nao respondem:
  verifique se `OPENAI_API_KEY` foi preenchida no arquivo `.env`.
- Porta ocupada:

```bash
python manage.py runserver 0.0.0.0:8001
```
