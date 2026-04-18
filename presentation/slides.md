---
theme: seriph
title: 'Política de Acordos Banco UFMG'
info: |
  Hackathon UFMG 2026 · Enter AI Challenge · Grupo Estrangeiros
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
  <img src="/grupo-logo.svg" alt="Grupo Estrangeiros" class="w-10 h-10" />
  <img src="/enter-logo.svg" alt="Enter AI" class="w-10 h-10" />
  <div class="eyebrow">Enter AI Challenge · Hackathon UFMG 2026 · Grupo Estrangeiros</div>
</div>

<div class="flex-1 flex flex-col justify-center">
  <h1 class="text-7xl font-extrabold leading-none tracking-tight">
    Política de acordos,<br/>
    <span class="accent">automatizada com rigor.</span>
  </h1>

  <div class="mt-10 max-w-2xl text-xl text-gray-700 leading-snug">
    Um triador de processos que decide <strong>defesa × acordo</strong> em segundos,
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
A plateia é mista (jurídico + banco + Enter). Evitar jargão ML aqui.
-->

---
layout: center
transition: fade
---

<div class="eyebrow mb-6">O problema</div>

<h1 class="text-6xl leading-tight max-w-5xl">
  A cada mês, <span class="accent">5.000 processos</span> chegam ao Banco UFMG alegando
  <span class="underline decoration-amber-500 decoration-4 underline-offset-8">não reconhecimento</span>
  de um empréstimo.
</h1>

<div v-click class="mt-12 text-xl text-gray-600 max-w-3xl">
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
    <StatNumber :value="300" prefix="R$ " label="milhões em exposição anual" />
    <div class="text-sm text-gray-500 text-center max-w-[220px]">60 mil casos multiplicados pelo ticket médio de condenação</div>
  </div>
</div>

<div class="brand-footer">Banco UFMG × Enter AI · Grupo Estrangeiros</div>

<!--
1 minuto. Cada número aparece animado. Tom: "isto não é um experimento acadêmico. É dinheiro real".
-->

---

<div class="eyebrow mb-2">Política de acordos</div>
<h1>Três princípios que orientam cada decisão.</h1>

<div class="mt-12 grid grid-cols-1 gap-6 max-w-4xl">

<v-clicks>

<div class="card-accent">
  <div class="eyebrow accent mb-2">01 · Seletividade</div>
  <div class="text-xl">
    <strong>Só se propõe acordo quando o banco tem mais a perder indo até o final.</strong>
    Se a documentação sustenta a defesa, defendemos.
  </div>
</div>

<div class="card-accent">
  <div class="eyebrow accent mb-2">02 · Valor ancorado em risco</div>
  <div class="text-xl">
    O valor do acordo nunca é arbitrário. É derivado da <strong>condenação esperada</strong> do caso,
    corrigida pela <strong>probabilidade real de perda</strong>.
  </div>
</div>

<div class="card-accent">
  <div class="eyebrow accent mb-2">03 · Consistência auditável</div>
  <div class="text-xl">
    Mesma política para todos os advogados externos. Cada decisão é <strong>justificada</strong>,
    <strong>rastreada</strong> e comparada com o que foi efetivamente feito.
  </div>
</div>

</v-clicks>

</div>

<!--
2 minutos. Este é o slide mais importante para a plateia jurídica.
Cada princípio reveal on click. Não ler literalmente, comentar com exemplos.
-->

---
layout: center
---

<div class="eyebrow mb-6">A fronteira de decisão</div>

<h1 class="mb-12">Uma regra simples, tecnicamente ancorada</h1>

<div class="flex items-center justify-center gap-16 mt-8">

<div class="text-center">
  <div class="text-6xl font-extrabold text-gray-300">Chance de perda</div>
  <div class="mt-4 text-sm text-gray-500 uppercase tracking-widest">estimada pelo modelo</div>
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

<div class="equation-box">
  <span class="eq-term">valor de acordo</span>
  <span class="eq-op">=</span>
  <span class="eq-alpha">α</span>
  <span class="eq-op">×</span>
  <span class="eq-term">condenação prevista</span>
</div>

<style scoped>
.equation-box {
  display: inline-flex;
  align-items: baseline;
  gap: 0.9rem;
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 1.25rem 2rem;
  white-space: nowrap;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  letter-spacing: -0.015em;
}
.eq-term {
  font-size: 1.6rem;
  color: #E5E7EB;
}
.eq-op {
  font-size: 1.4rem;
  color: #6B7280;
  font-weight: 400;
}
.eq-alpha {
  font-size: 2rem;
  color: #F5A623;
  font-weight: 700;
}
</style>

<div class="grid grid-cols-3 gap-8 max-w-5xl w-full mt-6">
  <div class="card">
    <div class="eyebrow accent mb-2">α = 0,60</div>
    <div class="text-base">Fator de negociação calibrado. Abaixo desse valor, as chances de rejeição pelo autor aumentam; acima, o banco desperdiça exposição.</div>
  </div>
  <div class="card">
    <div class="eyebrow accent mb-2">Condenação prevista</div>
    <div class="text-base">Estimativa de um modelo de regressão treinado em 60 mil sentenças, com transformação logarítmica para lidar com valores extremos.</div>
  </div>
  <div class="card">
    <div class="eyebrow accent mb-2">Resultado</div>
    <div class="text-base">Valor sugerido que minimiza o prejuízo esperado, caso a caso, e não por tabela fixa.</div>
  </div>
</div>

</div>

<!--
1 minuto. Explicar que α é hiperparâmetro e pode ser calibrado pelo banco ao longo do tempo.
-->

---

<div class="eyebrow mb-2">Potencial financeiro</div>
<h1>O que uma política consistente vale</h1>

<div class="mt-10 grid grid-cols-2 gap-16 max-w-5xl mx-auto">
  <div class="flex flex-col items-center gap-4">
    <StatNumber :value="14.6" prefix="R$ " label="milhões de economia no conjunto de teste" :duration="2" :decimals="1" />
    <div class="grid grid-cols-2 gap-3 mt-2 text-center w-full max-w-[360px]">
      <div class="bg-gray-50 border border-gray-200 rounded-md px-3 py-2">
        <div class="text-[10px] text-gray-500 uppercase tracking-wider">Custo real</div>
        <div class="text-lg font-bold text-gray-800">R$ 38,5 mi</div>
      </div>
      <div class="bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
        <div class="text-[10px] text-amber-700 uppercase tracking-wider">Custo sob a política</div>
        <div class="text-lg font-bold text-amber-700">R$ 23,9 mi</div>
      </div>
    </div>
  </div>

  <div class="flex flex-col items-center gap-4">
    <StatNumber :value="38" suffix=" %" label="redução no custo da política de acordos" :duration="2" />
    <div class="text-xs text-gray-500 text-center max-w-[280px] mt-2">
      Custo sugerido pela política, em percentual do custo real praticado hoje.
    </div>
  </div>
</div>

<div class="mt-12 text-[11px] text-gray-400 max-w-4xl leading-relaxed border-t border-gray-100 pt-4">
  <strong class="text-gray-600">Metodologia:</strong> base de 60 mil sentenças históricas (2024 a 2025), com ticket médio calculado pelo percentil 50 para evitar viés de cauda.
  O modelo foi treinado com split 80/20 (80 % dos dados para treino, 20 % para teste); os números apresentados vêm do conjunto de teste, indicando que os ganhos generalizam para fora da amostra de treino.
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
    <img src="/screenshots/cases-list.png" alt="Lista de processos" class="w-full h-full object-cover object-top" />
  </div>
  <div class="eyebrow accent">01 · Triagem</div>
  <div class="text-sm text-gray-700">O advogado abre a lista de processos. Busca unificada por número, UF, valor ou situação da recomendação.</div>
</div>

<div class="flex flex-col gap-3" v-click>
  <div class="aspect-video bg-gray-100 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
    <img src="/screenshots/case-detail.png" alt="Detalhe do caso com recomendação" class="w-full h-full object-cover object-top" />
  </div>
  <div class="eyebrow accent">02 · Recomendação</div>
  <div class="text-sm text-gray-700">Abre o caso e vê: probabilidade de perda, condenação esperada, ação sugerida e valor de acordo, sempre com justificativa.</div>
</div>

<div class="flex flex-col gap-3" v-click>
  <div class="aspect-video bg-gray-100 border border-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
    <img src="/screenshots/case-action.png" alt="Captura da ação do advogado" class="w-full h-full object-cover object-top" />
  </div>
  <div class="eyebrow accent">03 · Ação</div>
  <div class="text-sm text-gray-700">Registra a ação tomada: valor de acordo ou resultado da defesa. O sistema calcula aderência (±20 %) e desvio percentual automaticamente.</div>
</div>

</div>

<div class="mt-8 text-sm text-gray-500 italic max-w-4xl">
  Interface servidor-renderizada, sem curva de aprendizado. Importação em lote por pasta de subsídios gera recomendação no momento do cadastro.
</div>

<!--
2 minutos. Narrar o fluxo. Se o vídeo de 2min já foi gravado, mencionar.
-->

---

<div class="eyebrow mb-2">Arquitetura</div>
<h1>Pipeline em camadas, cada uma testável</h1>

<div class="pipeline">
  <div class="stage">
    <div class="stage-num">01</div>
    <div class="stage-title">Ingestão</div>
    <div class="stage-desc">PDFs do processo</div>
  </div>
  <div class="arrow">→</div>
  <div class="stage">
    <div class="stage-num">02</div>
    <div class="stage-title">Feature engineering</div>
    <div class="stage-desc">22 variáveis</div>
  </div>
  <div class="arrow">→</div>
  <div class="stage stage-dual">
    <div class="stage-num">03</div>
    <div class="stage-title">Modelos</div>
    <div class="dual-models">
      <div class="model-chip">Risco</div>
      <div class="model-chip">Custo</div>
    </div>
  </div>
  <div class="arrow">→</div>
  <div class="stage stage-highlight">
    <div class="stage-num">04</div>
    <div class="stage-title">Policy layer</div>
    <div class="stage-desc">P &gt; 0,60 → acordo</div>
  </div>
  <div class="arrow">→</div>
  <div class="stage">
    <div class="stage-num">05</div>
    <div class="stage-title">Recomendação</div>
    <div class="stage-desc">persistida 1:1 no caso</div>
  </div>
  <div class="arrow arrow-feedback">↺</div>
  <div class="stage stage-feedback">
    <div class="stage-num">06</div>
    <div class="stage-title">LawyerAction</div>
    <div class="stage-desc">feedback · aderência</div>
  </div>
</div>

<style>
.pipeline {
  display: flex;
  align-items: stretch;
  gap: 0.5rem;
  margin-top: 1.5rem;
  font-family: 'Inter', sans-serif;
  flex-wrap: nowrap;
}
.stage {
  flex: 1 1 0;
  background: #141414;
  border: 1.5px solid #F5A623;
  border-radius: 10px;
  padding: 0.9rem 0.75rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  box-shadow: 0 4px 14px -6px rgba(245, 166, 35, 0.18);
}
.stage-highlight {
  border-width: 2px;
  background: linear-gradient(180deg, #1a1405 0%, #141414 100%);
}
.stage-feedback {
  border-style: dashed;
  background: #0f0f0f;
}
.stage-num {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #F5A623;
  margin-bottom: 0.3rem;
}
.stage-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #F3F4F6;
  line-height: 1.2;
  margin-bottom: 0.35rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
.stage-desc {
  font-size: 0.68rem;
  color: #9CA3AF;
  line-height: 1.35;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
.stage-dual .dual-models {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.2rem;
}
.model-chip {
  font-size: 0.68rem;
  color: #E5E7EB;
  background: rgba(245, 166, 35, 0.08);
  border: 1px solid rgba(245, 166, 35, 0.25);
  border-radius: 5px;
  padding: 0.25rem 0.45rem;
  font-weight: 500;
}
.arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F5A623;
  font-size: 1.4rem;
  font-weight: 300;
  flex: 0 0 auto;
  width: 1.2rem;
}
.arrow-feedback {
  color: #6B7280;
  font-size: 1.2rem;
}
</style>

<div class="mt-6 grid grid-cols-4 gap-4 text-xs text-gray-600">
  <div><strong class="text-black">Ingestão:</strong> leitura dos PDFs dos subsídios e importação em lote por pasta padrão.</div>
  <div><strong class="text-black">Features mais importantes:</strong> quantidade de documentos, comprovantes de crédito e sub-assunto golpe.</div>
  <div><strong class="text-black">Modelos:</strong> dois classificadores treinados em scikit-learn, um para risco e outro para custo da condenação.</div>
  <div><strong class="text-black">Feedback:</strong> a ação registrada pelo advogado alimenta métricas de aderência e o próximo ciclo de treino.</div>
</div>

<!--
2 minutos. Ao falar do Policy, enfatize que é a camada onde as regras de negócio vivem: explicável e ajustável sem retreinar modelo.
-->

---

<div class="eyebrow mb-2">Monitoramento</div>
<h1 class="mb-4">Aderência e efetividade, em tempo real</h1>

<div class="grid grid-cols-2 gap-6">

<div class="card">
  <div class="eyebrow accent mb-2">Aderência</div>
  <div class="aspect-[16/8] bg-gray-100 border border-gray-200 rounded-md mb-3 overflow-hidden flex items-center justify-center">
    <img src="/screenshots/monitoramento-aderencia.png" alt="Dashboard de aderência" class="w-full h-full object-cover object-top" />
  </div>
  <ul class="text-xs space-y-1 text-gray-700 leading-snug">
    <li>· <strong>Aderência de ação:</strong> percentual de casos em que o advogado seguiu a ação recomendada.</li>
    <li>· <strong>Aderência de valor:</strong> percentual de acordos fechados dentro da faixa de ±20 % do valor sugerido.</li>
    <li>· <strong>Desvio médio:</strong> diferença percentual entre o valor praticado e o valor recomendado.</li>
  </ul>
</div>

<div class="card">
  <div class="eyebrow accent mb-2">Efetividade</div>
  <div class="aspect-[16/8] bg-gray-100 border border-gray-200 rounded-md mb-3 overflow-hidden flex items-center justify-center">
    <img src="/screenshots/monitoramento-efetividade.png" alt="Dashboard de efetividade" class="w-full h-full object-cover object-top" />
  </div>
  <ul class="text-xs space-y-1 text-gray-700 leading-snug">
    <li>· <strong>Taxa de efetividade:</strong> casos em que o custo observado ficou dentro da faixa prevista pela recomendação.</li>
    <li>· <strong>Êxito da defesa</strong> e <strong>conversão de acordo</strong>, somados à economia líquida do período.</li>
    <li>· Matriz que compara a ação recomendada com a ação efetivamente tomada pelo advogado.</li>
  </ul>
</div>

</div>

<div class="mt-4 text-xs text-gray-500 italic">
  Aderência responde "a política está sendo seguida?". Efetividade responde "ela está gerando resultado?". São perguntas diferentes, e por isso medimos as duas.
</div>

<!--
2 minutos. Insistir na distinção aderência vs. efetividade. É o ponto alto para o banco.
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
    <span class="text-gray-600">O modelo ainda não lê os autos em linguagem natural e fica cego a nuances argumentativas da petição inicial.</span>
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
    <span class="text-gray-600">O modelo aprendeu com decisões passadas. Se a política atual já era subótima, parte do viés está embutido. Mitigamos com aprendizado contínuo.</span>
  </div>
</div>

<div class="flex gap-4">
  <div class="text-amber-600 font-mono text-sm mt-1">04</div>
  <div>
    <strong>Sem LLM no loop de decisão.</strong>
    <span class="text-gray-600">A decisão atual é determinística e auditável. Ganhamos explicabilidade estatística e perdemos nuance textual. Troca consciente.</span>
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
    <h3 class="text-lg m-0">Integração com APIs dos tribunais</h3>
  </div>
  <div class="text-sm text-gray-600">Carregamento automático dos processos via APIs públicas dos tribunais e melhorias iterativas no modelo preditivo.</div>
</div>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 3</span>
    <h3 class="text-lg m-0">Retreino automático</h3>
  </div>
  <div class="text-sm text-gray-600">O sistema já captura a ação tomada pelo advogado em cada caso. Próximo passo: pipeline de retreino mensal com teste em paralelo de novos limiares α antes de promover ao ambiente produtivo.</div>
</div>

<div class="card">
  <div class="flex items-baseline gap-3 mb-2">
    <span class="text-amber-600 font-mono text-xs">SEMANA 4</span>
    <h3 class="text-lg m-0">Motivo estruturado de divergência</h3>
  </div>
  <div class="text-sm text-gray-600">Quando o advogado diverge da recomendação, capturar o motivo em forma categorizada. Vira feature adicional para o próximo ciclo de treino.</div>
</div>

</v-clicks>

</div>

<!--
1 minuto. Enfatizar que o sistema já tem a infraestrutura de captura de ação (LawyerAction). Faltam só as camadas analíticas.
-->

---
layout: center
class: text-center
---

<div class="eyebrow mb-10">Grupo Estrangeiros · Hackathon UFMG 2026</div>

<QuoteReveal
  text="Tempora mutantur, nos et mutamur in illis."
  author="Ovídio"
  :auto-play="true"
/>

<div class="mt-6 text-lg text-gray-400 italic">
  Os tempos mudam, e nós mudamos com eles.
</div>

<div class="mt-12 text-sm text-gray-500 uppercase tracking-widest">
  Obrigado. Perguntas?
</div>

<div class="brand-footer">Hackathon UFMG 2026 · Enter AI Challenge</div>

<!--
45 segundos. Slide único de fecho. Deixe a QuoteReveal completar, pausa longa, abra perguntas.
A citação de Ovídio captura a essência do sistema: uma política que se adapta ao contexto e aprende com a ação de cada advogado.
-->
