# Enter Dashboard — Hackathon UFMG

Dashboard analítico em Streamlit para explorar **60.000 sentenças** do Banco UFMG em casos de *não reconhecimento de contratação de empréstimo*. Responde a pergunta central:

> **Quais fatores (UF, comarca, sub-assunto, subsídios) mais influenciam o desfecho do processo e o valor de condenação?**

Os insights do dashboard alimentam a **política de acordos** do desafio.

## Estrutura

```
enter-dashboard/
├── app.py                             # Home — KPIs e exposição financeira
├── pages/
│   ├── 1_Fatores_Categoricos.py       # UF, comarca, sub-assunto × resultado
│   ├── 2_Subsidios.py                 # Impacto individual e combinado dos 6 subsídios
│   ├── 3_Valores_Financeiros.py       # Causa × condenação + exposição esperada
│   └── 4_Modelo_Preditivo.py          # Logistic + Random Forest + SHAP
├── src/
│   ├── data_loader.py                 # Carrega XLSX → parquet, aplica filtros
│   ├── cnj_parser.py                  # Extrai ano/tribunal/comarca do nº CNJ
│   ├── analysis.py                    # Cramér's V, lift, taxa condicional
│   ├── modeling.py                    # Treino + SHAP
│   └── charts.py                      # Wrappers Plotly
├── data/
│   └── base.parquet                   # Gerado na primeira execução
├── requirements.txt
└── README.md
```

## Setup

```bash
cd enter-dashboard
pip install -r requirements.txt
```

O dashboard procura o XLSX nesta ordem:
1. `$ENTER_XLSX_PATH` (env var)
2. `enter-dashboard/data/Hackaton_Enter_Base_Candidatos.xlsx`
3. `enter-dashboard/data/base.xlsx`
4. `../Hackaton_Enter_Base_Candidatos.xlsx` (pasta pai Enter/)

A configuração padrão já funciona se o projeto estiver dentro da pasta `Enter/`.

## Rodar

```bash
streamlit run app.py
```

Abre em `http://localhost:8501`.

**Primeira execução:** ~30s para ler o XLSX e gerar o parquet de cache. Execuções subsequentes: <2s.

## O que cada página responde

### Home (`app.py`)
- Taxa global de êxito
- Valor em jogo, condenações pagas, economia histórica
- Distribuição dos 5 resultados micro
- Êxito por sub-assunto (Golpe vs Genérico)

### 1 — Fatores Categóricos
- **Ranking Cramér's V:** qual variável categórica mais se associa ao resultado
- **Sankey** Sub-assunto → Macro → Micro
- **Heatmap UF × Resultado micro** (% por UF)
- **Top 20 comarcas** por volume + taxa de êxito
- Sub-assunto × resultado

### 2 — Subsídios (núcleo da análise)
- **Lift de cada subsídio:** P(êxito|presente) vs P(êxito|ausente), diferença em pp
- **Gráfico lado a lado** da taxa de êxito com vs sem cada subsídio
- **Nº de subsídios × taxa de êxito** (bar + line)
- **Correlação entre subsídios** (quem anda junto?)
- **Top combinações** (playbooks vencedores vs combinações com alta condenação)

### 3 — Valores Financeiros
- Scatter Causa × Condenação colorido por resultado
- Boxplot de condenação por resultado, UF, sub-assunto
- Condenação média por nº de subsídios
- **Exposição esperada por UF** = P(perder) × E[condenação | perder] — útil para priorizar política

### 4 — Modelo Preditivo
- Logistic Regression ou Random Forest (toggle)
- Métricas: accuracy, ROC AUC, precision/recall, matriz de confusão
- Feature importance (RF) ou coeficientes (Logistic)
- **SHAP global:** barra + beeswarm
- **Explicar caso individual:** seleciona nº do processo, mostra waterfall SHAP

## Notas técnicas

- `Êxito` = banco não é condenado (`Resultado micro` ∈ {Improcedência, Extinção})
- `Não êxito` = banco paga algo (Procedência, Parcial procedência, Acordo)
- Dataset é **balanceado por UF** (2.308 casos/UF) — interpretar comparações com cuidado
- Cidade não existe na base; usamos **código de comarca** extraído do CNJ (últimos 4 dígitos)
- O modelo usa 30k de amostra (estratificada) para treinar rápido; rodar na base inteira é trivial mudando `sample_n` em `modeling.py`
