---
theme: seriph
title: 'Política de Acordos Banco UFMG'
info: |
  Hackathon UFMG 2026 — Enter AI Challenge · Grupo Estrangeiros
  Triador inteligente para decisão defesa × acordo em processos de não reconhecimento de empréstimo.
class: text-left
transition: view-transition
mdc: true
highlighter: shiki
drawings:
  persist: false
fonts:
  sans: 'Inter'
  mono: 'JetBrains Mono'
colorSchema: dark
---

<style>
@import './styles/index.css';
</style>

<div class="h-full flex flex-col justify-between py-8">

<div class="flex items-center gap-3">
  <img src="/enter-logo.svg" alt="Enter AI" class="w-10 h-10" />
  <div class="eyebrow">Enter AI Challenge · Hackathon UFMG 2026 · Grupo Estrangeiros</div>
</div>

<div class="flex-1 flex flex-col justify-center">
  <h1 class="text-7xl font-extrabold leading-none tracking-tight">
    Política de acordos,<br/>
    <span class="accent">automatizada com rigor.</span>
  </h1>

  <div class="mt-10 max-w-2xl text-xl text-gray-700 leading-snug">
    Um triador de processos que decide <strong>defesa × acordo</strong> em segundos —
    e sugere o valor ótimo para cada caso.
  </div>
</div>

<div class="flex justify-between items-end text-xs text-gray-500 uppercase tracking-widest">
  <div>Banco UFMG · 18 de abril de 2026</div>
  <div>pressione <kbd class="border border-gray-300 rounded px-2 py-0.5 font-mono text-[11px]">Space</kbd> para avançar</div>
</div>

</div>

<!--
Abertura: 20 segundos. Apresentar o grupo e o posicionamento em uma frase.
A plateia é mista (jurídico + banco + Enter) — evitar jargão ML aqui.
-->

---
layout: center
transition: fade-out
---

<div class="eyebrow mb-6">O problema</div>

<h1 class="text-6xl leading-tight max-w-5xl">
  A cada mês, <span class="accent">5.000 processos</span> chegam ao Banco UFMG alegando
  <span class="underline decoration-amber-500 decoration-4 underline-offset-8">não reconhecimento</span>
  de um empréstimo.
</h1>

<div class="mt-12 text-xl text-gray-600 max-w-3xl">
  Para cada um, um advogado externo precisa decidir:
  <strong class="text-black">defender ou propor acordo?</strong>
</div>

<!--
45s. Estabelecer a escala. Próximo slide quantifica.
-->

---

<div class="eyebrow mb-2">Magnitude</div>
<h1 class="mb-12">Três números que redefinem o problema</h1>

<div class="grid grid-cols-3 gap-12 mt-16">
  <div class="flex flex-col items-center gap-3">
    <StatNumber :value="5000" label="processos por mês" />
    <div class="text-sm text-gray-500 text-center max-w-[200px]">Volume recorrente de casos de não reconhecimento</div>
  </div>
  <div class="flex flex-col items-center gap-3">
    <StatNumber :value="60000" label="sentenças históricas na base" />
    <div class="text-sm text-gray-500 text-center max-w-[200px]">Combustível para os modelos preditivos</div>
  </div>
  <div class="flex flex-col items-center gap-3">
    <StatNumber :value="300" prefix="R$ " suffix=" M" label="em exposição anual estimada" />
    <div class="text-sm text-gray-500 text-center max-w-[200px]">60k casos × ticket médio de condenação</div>
  </div>
</div>

<div class="brand-footer">Banco UFMG × Enter AI · Grupo Estrangeiros</div>

<!--
1 minuto. Cada número aparece animado. Tom: "isto não é um experimento acadêmico — é dinheiro real".
-->

---

<div class="eyebrow mb-2">Política de acordos</div>
<h1>Três princípios. Zero jargão técnico.</h1>

<div class="mt-12 grid grid-cols-1 gap-6 max-w-4xl">

<v-clicks>

<div class="card-accent">
  <div class="eyebrow accent mb-2">01 — Seletividade</div>
  <div class="text-xl">
    <strong>Só se propõe acordo quando o banco tem mais a perder indo até o final.</strong>
    Se a documentação sustenta a defesa, defendemos.
  </div>
</div>

<div class="card-accent">
  <div class="eyebrow accent mb-2">02 — Valor ancorado em risco</div>
  <div class="text-xl">
    O valor do acordo nunca é arbitrário. É derivado da <strong>condenação esperada</strong> do caso,
    corrigida pela <strong>probabilidade real de perda</strong>.
  </div>
</div>

<div class="card-accent">
  <div class="eyebrow accent mb-2">03 — Consistência auditável</div>
  <div class="text-xl">
    Mesma política para todos os advogados externos. Cada decisão é <strong>justificada</strong>,
    <strong>rastreada</strong> e comparada com o que foi efetivamente feito.
  </div>
</div>

</v-clicks>

</div>

<!--
2 minutos. Este é o slide mais importante para a plateia jurídica.
Cada princípio reveal on click. Não ler literalmente — comentar com exemplos.
-->

---
layout: center
---

<div class="eyebrow mb-6">A fronteira de decisão</div>

<h1 class="mb-12">Uma regra simples, tecnicamente ancorada</h1>

<div class="flex items-center justify-center gap-16 mt-8">

<div class="text-center">
  <div class="text-6xl font-extrabold text-gray-300">P(perder)</div>
  <div class="mt-4 text-sm text-gray-500 uppercase tracking-widest">probabilidade estimada pelo modelo</div>
</div>

<div class="text-7xl text-amber-600 font-bold">&gt;</div>

<div class="text-center">
  <div class="text-6xl font-extrabold accent">60 %</div>
  <div class="mt-4 text-sm text-gray-500 uppercase tracking-widest">fronteira de ação</div>
</div>

</div>

<div class="mt-16 grid grid-cols-2 gap-6 max-w-4xl mx-auto">
  <div class="card" v-click>
    <div class="eyebrow mb-2">abaixo do limiar</div>
    <div class="text-2xl font-bold">Defender</div>
    <div class="text-sm text-gray-600 mt-2">O banco tem subsídios suficientes. Custo esperado de ir até o final é menor.</div>
  </div>
  <div class="card-accent" v-click>
    <div class="eyebrow accent mb-2">acima do limiar</div>
    <div class="text-2xl font-bold">Propor acordo</div>
    <div class="text-sm text-gray-600 mt-2">Exposição é alta. Negociar limita o prejuízo esperado.</div>
  </div>
</div>

<!--
1 minuto. A fronteira 0.60 é explicável e defensável. Mencione que é configurável.
-->

---

<div class="eyebrow mb-2">Valor do acordo</div>
<h1>Risk-adjusted, não arbitrário</h1>

<div class="mt-16 flex flex-col items-center gap-10">

<div class="text-4xl font-mono bg-gray-50 border border-gray-200 rounded-xl px-10 py-8">
  <span class="text-gray-500">valor_acordo</span>
  <span class="mx-3 text-amber-600">=</span>
  <span class="accent">α</span>
  <span class="mx-3 text-gray-500">×</span>
  <span>E[condenação]</span>
</div>

<div class="grid grid-cols-3 gap-8 max-w-5xl w-full mt-6">
  <div class="card">
    <div class="eyebrow accent mb-2">α = 0,60</div>
    <div class="text-base">Fator de negociação calibrado. Abaixo disso, o autor rejeita; acima, o banco desperdiça exposição.</div>
  </div>
  <div class="card">
    <div class="eyebrow accent mb-2">E[condenação]</div>
    <div class="text-base">Predição de um modelo de regressão treinado em 60k sentenças, com transformação log para lidar com cauda pesada.</div>
  </div>
  <div class="card">
    <div class="eyebrow accent mb-2">Resultado</div>
    <div class="text-base">Valor sugerido que minimiza prejuízo esperado — caso a caso, não por tabela fixa.</div>
  </div>
</div>

</div>

<!--
1 minuto. Explicar que α é hiperparâmetro — pode ser calibrado pelo banco ao longo do tempo.
-->

---

<div class="eyebrow mb-2">Potencial financeiro</div>
<h1>O que uma política consistente vale</h1>

<div class="mt-12 grid grid-cols-3 gap-12">
  <div class="flex flex-col items-center gap-4">
    <StatNumber :value="60" prefix="R$ " suffix=" M" label="economia anual estimada" :duration="2" />
    <div class="text-xs text-gray-500 text-center max-w-[220px]">
      Decisões mais acuradas × valores de acordo corrigidos pelo risco
    </div>
  </div>

  <div class="flex flex-col items-center gap-4">
    <StatNumber :value="40" suffix=" %" label="menos tempo de triagem" :duration="2" />
    <div class="text-xs text-gray-500 text-center max-w-[220px]">
      Advogado externo chega ao caso com a recomendação pronta
    </div>
  </div>

  <div class="flex flex-col items-center gap-4">
    <StatNumber :value="4" suffix="x" label="mais consistência" :duration="2" />
    <div class="text-xs text-gray-500 text-center max-w-[220px]">
      Mesma política aplicada entre todos os escritórios externos
    </div>
  </div>
</div>

<div class="mt-16 text-[11px] text-gray-400 max-w-4xl leading-relaxed border-t border-gray-100 pt-4">
  <strong class="text-gray-600">Metodologia:</strong> base de 60k sentenças históricas (2024-2025) ·
  ticket médio de exposição calculado por percentil 50 para evitar viés de cauda ·
  economia = (∆ custo esperado entre política atual e política recomendada) × volume anual.
  Valores conservadores; cenário otimista chega a R$ 75 M.
</div>

<div class="brand-footer">Banco UFMG × Enter AI · Grupo Estrangeiros</div>

<!--
2 minutos. SLIDE DECISIVO para a plateia do banco.
Leia o rodapé em voz alta para reforçar credibilidade metodológica.
-->

---

<div class="eyebrow mb-2">Experiência do advogado</div>
<h1>Da triagem à ação, em 3 passos</h1>

<div class="mt-10 grid grid-cols-3 gap-6">

<div class="flex flex-col gap-3" v-click>
  <div class="aspect-video bg-gray-100 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
    <img src="/screenshots/cases-list.png" alt="Lista de processos" class="w-full h-full object-cover" />
  </div>
  <div class="eyebrow accent">01 · Triagem</div>
  <div class="text-sm text-gray-700">O advogado abre a lista de processos. Busca unificada por número, UF, valor ou situação da recomendação.</div>
</div>

<div class="flex flex-col gap-3" v-click>
  <div class="aspect-video bg-gray-100 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
    <img src="/screenshots/case-detail.png" alt="Detalhe do caso com recomendação" class="w-full h-full object-cover" />
  </div>
  <div class="eyebrow accent">02 · Recomendação</div>
  <div class="text-sm text-gray-700">Abre o caso e vê: probabilidade de perda, condenação esperada, ação sugerida e valor de acordo — com justificativa.</div>
</div>

<div class="flex flex-col gap-3" v-click>
  <div class="aspect-video bg-gray-100 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
    <img src="/screenshots/case-action.png" alt="Captura da ação do advogado" class="w-full h-full object-cover" />
  </div>
  <div class="eyebrow accent">03 · Ação</div>
  <div class="text-sm text-gray-700">Aceita a sugestão ou diverge — em ambos casos, o banco captura o dado e alimenta o monitoramento.</div>
</div>

</div>

<div class="mt-8 text-sm text-gray-500 italic max-w-4xl">
  Interface servidor-renderizada, sem curva de aprendizado — o advogado já sabe usar.
</div>

<!--
2 minutos. Narrar o fluxo. Se o vídeo de 2min já foi gravado, mencionar.
-->

---

<div class="eyebrow mb-2">Arquitetura</div>
<h1>Pipeline em camadas, cada uma testável</h1>

<div class="mt-6">
<ArchitectureFlow
  :nodes="[
    { id: 'pdf', label: 'PDFs do processo', x: 20, y: 170, w: 140, h: 64 },
    { id: 'feat', label: 'Feature engineering', x: 200, y: 170, w: 160, h: 64 },
    { id: 'risk', label: 'Modelo de risco', x: 400, y: 80, w: 140, h: 64 },
    { id: 'cost', label: 'Modelo de custo', x: 400, y: 260, w: 140, h: 64 },
    { id: 'policy', label: 'Policy layer', x: 580, y: 170, w: 120, h: 64 },
    { id: 'db', label: 'Recomendação', x: 740, y: 170, w: 120, h: 64 }
  ]"
  :edges="[
    { from: 'pdf', to: 'feat', label: 'extração' },
    { from: 'feat', to: 'risk', label: 'P(perder)' },
    { from: 'feat', to: 'cost', label: 'E[condenação]' },
    { from: 'risk', to: 'policy' },
    { from: 'cost', to: 'policy' },
    { from: 'policy', to: 'db', label: 'persiste' }
  ]"
  :width="880"
  :height="360"
/>
</div>

<div class="mt-6 grid grid-cols-4 gap-4 text-xs text-gray-600">
  <div><strong class="text-black">Ingestão:</strong> pypdf + regex mapeia subsídios por nome de arquivo.</div>
  <div><strong class="text-black">Features:</strong> 22 variáveis incluindo score ponderado de documentos.</div>
  <div><strong class="text-black">Modelos:</strong> 2 checkpoints scikit-learn (risk: classif., cost: reg. log-transformada).</div>
  <div><strong class="text-black">Persistência:</strong> <code>CaseRecommendation</code> 1-para-1 com o processo.</div>
</div>

<!--
2 minutos. Cada nó é um click. Ao revelar o Policy, enfatize que é a camada onde as regras de negócio vivem — explicável e ajustável sem retreinar modelo.
-->

---

<script setup>
const coreCode = `def gerar_recomendacao_caso(case, settlement_factor=0.60):
    prob_perder = risk_model.predict_proba(features)[:, 1][0]
    valor_estimado = np.expm1(cost_model.predict(features))[0]
    expected_loss = prob_perder * valor_estimado

    if prob_perder > settlement_factor:
        return 'PROPOR_ACORDO', settlement_factor * valor_estimado
    return 'DEFENDER', None`

const coreSteps = [
  { lines: [1], note: 'Entry point. Recebe um LegalCase e o fator de negociação (α=0,60). Tudo configurável sem tocar no modelo.' },
  { lines: [2], note: 'Modelo de risco prevê a probabilidade de perda do caso. Treinado em 60k sentenças históricas.' },
  { lines: [3], note: 'Modelo de custo prevê a condenação esperada. Usa transformação log (expm1) para lidar com cauda pesada.' },
  { lines: [4], note: 'Expected loss = probabilidade × magnitude. Esta é a grandeza que a política tenta minimizar.' },
  { lines: [6, 7], note: 'A fronteira de decisão. Acima de α, o ganho esperado com acordo supera o risco de manter o caso em defesa.' },
  { lines: [8], note: 'Caso contrário, defender. Sem valor de acordo. Decisão explicável em uma frase para o advogado.' }
]
</script>

<div class="eyebrow mb-2">O núcleo do código</div>
<h1>6 linhas decidem tudo</h1>

<div class="mt-6">
<CodeReveal lang="python" :code="coreCode" :steps="coreSteps" />
</div>

<!--
1 minuto. Mostrar que toda a inteligência do sistema cabe em uma função — código auditável e de baixa manutenção.
Referência no repo: src/estrangeirosplatform/legalapp/views.py:297-355
-->

---

<div class="eyebrow mb-2">Monitoramento</div>
<h1>Aderência e efetividade, em tempo real</h1>

<div class="mt-8 grid grid-cols-2 gap-6">

<div class="card">
  <div class="eyebrow accent mb-3">Aderência</div>
  <div class="aspect-[16/10] bg-gray-100 border border-gray-200 rounded-md mb-4 overflow-hidden flex items-center justify-center">
    <img src="/screenshots/monitoramento-aderencia.png" alt="Dashboard de aderência" class="w-full h-full object-cover" />
  </div>
  <ul class="text-sm space-y-1 text-gray-700">
    <li>· <strong>% casos em que o advogado seguiu a recomendação</strong></li>
    <li>· % acordos fechados dentro da faixa ±20%</li>
    <li>· Desvio médio absoluto do valor</li>
  </ul>
</div>

<div class="card">
  <div class="eyebrow accent mb-3">Efetividade</div>
  <div class="aspect-[16/10] bg-gray-100 border border-gray-200 rounded-md mb-4 overflow-hidden flex items-center justify-center">
    <img src="/screenshots/monitoramento-efetividade.png" alt="Dashboard de efetividade" class="w-full h-full object-cover" />
  </div>
  <ul class="text-sm space-y-1 text-gray-700">
    <li>· <strong>Taxa de êxito das defesas realizadas</strong></li>
    <li>· Taxa de efetividade global da política</li>
    <li>· Custo total e custo médio por caso</li>
  </ul>
</div>

</div>

<div class="mt-6 text-sm text-gray-500 italic">
  Aderência responde "a política está sendo seguida?". Efetividade responde "ela está gerando resultado?". São perguntas diferentes — medimos as duas.
</div>

<!--
2 minutos. Insistir na distinção aderência vs. efetividade — é o ponto alto para o banco.
-->

---

<div class="eyebrow mb-2">Limitações conhecidas</div>
<h1>Transparência sobre o que ainda não resolvemos</h1>

<div class="mt-10 max-w-4xl">

<v-clicks>

<div class="flex gap-4 mb-5">
  <div class="text-amber-600 font-mono text-sm mt-1">01</div>
  <div>
    <strong>Features limitadas aos subsídios estruturados.</strong>
    <span class="text-gray-600">O modelo não lê os autos em linguagem natural — ainda. Fica cego a nuances argumentativas da petição inicial.</span>
  </div>
</div>

<div class="flex gap-4 mb-5">
  <div class="text-amber-600 font-mono text-sm mt-1">02</div>
  <div>
    <strong>Fronteira α = 0,60 é global.</strong>
    <span class="text-gray-600">Uma UF ou perfil de autor pode ter dinâmica diferente. Calibração por segmento é próximo passo.</span>
  </div>
</div>

<div class="flex gap-4 mb-5">
  <div class="text-amber-600 font-mono text-sm mt-1">03</div>
  <div>
    <strong>Viés histórico na base.</strong>
    <span class="text-gray-600">Modelo aprendeu com decisões passadas — se a política atual já era subótima, parte do viés está embutido. Mitigamos com aprendizado contínuo.</span>
  </div>
</div>

<div class="flex gap-4">
  <div class="text-amber-600 font-mono text-sm mt-1">04</div>
  <div>
    <strong>Sem LLM no loop de decisão.</strong>
    <span class="text-gray-600">Decisão atual é determinística e auditável. Ganhamos explicabilidade, perdemos nuance textual — troca consciente.</span>
  </div>
</div>

</v-clicks>

</div>

<!--
1 minuto. Plateia técnica respeita honestidade. Não enfeitar.
-->

---

<div class="eyebrow mb-2">Próximos passos</div>
<h1>O que construímos em 1 mês adicional</h1>

<div class="mt-10 grid grid-cols-2 gap-6 max-w-5xl">

<v-clicks>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 1</span>
    <h3 class="text-lg m-0">LLM para leitura de autos</h3>
  </div>
  <div class="text-sm text-gray-600">Extrair sinais semânticos da petição inicial (fraude, coação, fatos específicos) como feature adicional.</div>
</div>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 2</span>
    <h3 class="text-lg m-0">Calibração por segmento</h3>
  </div>
  <div class="text-sm text-gray-600">α específico por UF, sub-assunto e perfil de autor. Modelo de custo por segmento.</div>
</div>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 3</span>
    <h3 class="text-lg m-0">Aprendizado contínuo</h3>
  </div>
  <div class="text-sm text-gray-600">Pipeline de retreino mensal com as novas ações capturadas no <code>LawyerAction</code>. Shadow testing de novos limiares antes de produção.</div>
</div>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 4</span>
    <h3 class="text-lg m-0">Feedback loop do advogado</h3>
  </div>
  <div class="text-sm text-gray-600">Quando o advogado diverge da recomendação, capturar o motivo em forma estruturada — direto para o dataset de treino.</div>
</div>

</v-clicks>

</div>

<!--
1 minuto. Enfatizar que o sistema já tem a infraestrutura de captura de ação (LawyerAction) — faltam só as camadas analíticas.
-->

---
layout: center
class: text-center
---

<div class="eyebrow mb-10">Grupo Estrangeiros · Hackathon UFMG 2026</div>

<QuoteReveal
  text="Êxito e eficiência. Mesma política, aplicada em 5.000 processos por mês, sem perder a explicabilidade."
  author="Banco UFMG × Enter AI"
  :auto-play="true"
/>

<div class="mt-16 text-sm text-gray-500 uppercase tracking-widest">
  Obrigado · Perguntas?
</div>

<div class="brand-footer">Hackathon UFMG 2026 · Enter AI Challenge</div>

<!--
30 segundos. Slide de fecho. Deixe a QuoteReveal completar, sorria, abra perguntas.
-->
