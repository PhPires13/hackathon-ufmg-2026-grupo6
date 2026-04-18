<script setup lang="ts">
import { computed } from 'vue'
import { useSlideContext, useNav } from '@slidev/client'

interface Step {
  lines: number[]
  note?: string
}

const props = defineProps<{
  code: string
  lang?: string
  steps: Step[]
}>()

const { $clicks } = useSlideContext()
const { isPrintMode } = useNav()

const stepIdx = computed(() => {
  if (isPrintMode.value) return props.steps.length - 1
  return Math.min(Math.max($clicks.value - 1, 0), props.steps.length - 1)
})
const currentStep = computed(() => props.steps[stepIdx.value])

const lines = computed(() => props.code.split('\n'))
const isHighlighted = (idx: number) =>
  !!currentStep.value?.lines.includes(idx + 1)
</script>

<template>
  <div class="code-reveal">
    <pre class="code-block"><code><span
      v-for="(line, idx) in lines"
      :key="idx"
      class="code-line"
      :class="{ dim: !isHighlighted(idx), hl: isHighlighted(idx) }"
    ><span class="ln">{{ String(idx + 1).padStart(2, ' ') }}</span><span class="txt">{{ line || ' ' }}</span></span></code></pre>
    <transition name="note">
      <aside v-if="currentStep?.note" :key="stepIdx" class="note">
        <div class="note-idx">{{ stepIdx + 1 }} / {{ steps.length }}</div>
        <div class="note-text">{{ currentStep.note }}</div>
      </aside>
    </transition>
  </div>
</template>

<style scoped>
.code-reveal {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 1.5rem;
  align-items: start;
  width: 100%;
}
.code-block {
  background: #0A0F1C;
  color: #E5E7EB;
  padding: 1.25rem 1rem 1.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.65;
  overflow: auto;
  margin: 0;
  border: 1px solid #1F2937;
  box-shadow: 0 8px 30px -8px rgba(0, 0, 0, 0.15);
}
.code-block code { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.code-line {
  display: flex;
  gap: 0.85rem;
  padding: 0 0.5rem;
  border-radius: 4px;
  transition: opacity 350ms ease, background 350ms ease, box-shadow 350ms ease;
}
.code-line.dim { opacity: 0.25; }
.code-line.hl {
  background: rgba(0, 102, 255, 0.12);
  box-shadow: inset 3px 0 0 #F5A623;
}
.ln {
  color: #4B5563;
  user-select: none;
  white-space: pre;
  font-variant-numeric: tabular-nums;
}
.hl .ln { color: #FBBF24; }
.txt { white-space: pre; }
.note {
  position: sticky;
  top: 1rem;
  background: #141414;
  border: 1px solid #27272A;
  border-left: 3px solid #F5A623;
  padding: 1rem 1.1rem;
  border-radius: 8px;
  font-size: 0.92rem;
  line-height: 1.55;
  color: #E5E7EB;
}
.note-idx {
  font-size: 0.7rem;
  color: #F5A623;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  margin-bottom: 0.5rem;
  font-weight: 700;
}
.note-enter-active, .note-leave-active { transition: opacity 250ms, transform 250ms; }
.note-enter-from { opacity: 0; transform: translateY(8px); }
.note-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
