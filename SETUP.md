# Setup e Execução

> Preencha este arquivo com as instruções específicas da sua solução.

---

## Pré-requisitos

Liste aqui as dependências necessárias para rodar a solução:

- [ ] ...
- [ ] ...

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis necessárias:

```env
# Exemplo — adapte conforme sua solução
OPENAI_API_KEY=sua_chave_aqui
```

> **Nunca commite o arquivo `.env` com credenciais reais.**  
> Um arquivo `.env.example` com as variáveis (sem valores) já está incluído neste repo.

## Instalação

```bash
# Descreva aqui os passos de instalação
```

## Execução

```bash
# Descreva aqui como rodar a solução
```

## Dados

Coloque os arquivos de dados fornecidos na pasta `data/`. Consulte [`data/README.md`](./data/README.md) para instruções detalhadas.

Para importar os casos no Django a partir da nova estrutura (`sentencas.csv` + `subsidios/<id_processo>`):

```bash
cd src/estrangeirosplatform

# valida sem gravar
python manage.py import_cases_from_data_dir --data-dir ../../data --dry-run

# importa/atualiza no banco
python manage.py import_cases_from_data_dir --data-dir ../../data
```

O mesmo comando tambem aceita importacao por PDFs:

```bash
cd src/estrangeirosplatform

# Um processo (pasta com PDFs)
python manage.py import_cases_from_data_dir --source pdf --case-dir /caminho/para/pasta_do_caso

# Varios processos (cada subpasta pode ter PDFs em autos/)
python manage.py import_cases_from_data_dir --source pdf --processos-exemplo-dir ../../data/processos_exemplo
```

Modo automatico (tenta PDF se informado e tambem importa estrutura data):

```bash
python manage.py import_cases_from_data_dir --source auto --data-dir ../../data --processos-exemplo-dir ../../data/processos_exemplo
```

## Estrutura do Projeto

```
├── src/          # código-fonte
├── data/         # dados (não versionados — ver .gitignore)
├── docs/         # apresentação e documentação
├── .env.example  # variáveis de ambiente necessárias
├── SETUP.md      # este arquivo
└── README.md     # descrição do desafio
```
