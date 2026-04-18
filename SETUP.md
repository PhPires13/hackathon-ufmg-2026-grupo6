# Setup e Execucao

Guia minimo para instalar as dependencias e subir o Django localmente.

## Pre-requisitos

- Python 3.11+
- pip

## Passo a passo

Na raiz do repositorio: `pip install -r requirements.txt`

Como o agente de IA usa a API da OpenAI, configure a chave antes de subir o projeto:
`cp .env.example .env`

No arquivo `.env`, preencha pelo menos:

```env
OPENAI_API_KEY='sua_chave_aqui'
```

Depois entre na pasta do projeto Django e execute as migracoes do banco de dados:

```bash
cd src/estrangeirosplatform
python manage.py migrate
```

Em seguida, inicie o servidor local: `python manage.py runserver`

Acesso local:
- http://127.0.0.1:8000/

## Fluxo rapido

```bash
pip install -r requirements.txt
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
- Porta ocupada: `python manage.py runserver 0.0.0.0:8001`
