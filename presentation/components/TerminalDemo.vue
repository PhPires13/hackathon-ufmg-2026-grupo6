<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive } from 'vue'

interface Line {
  type: 'cmd' | 'out'
  text: string
  delay?: number
}

const props = withDefaults(defineProps<{
  lines: Line[]
  prompt?: string
  speed?: number
}>(), {
  prompt: '$',
  speed: 30
})

interface VisibleLine {
  type: 'cmd' | 'out'
  text: string
  done: boolean
}

const state = reactive<{ visible: VisibleLine[] }>({ visible: [] })
let cancelled = false
const timers: number[] = []

function wait(ms: number) {
  return new Promise<void>(resolve => {
    const t = window.setTimeout(resolve, ms)
    timers.push(t)
  })
}

async function typeLine(line: Line) {
  if (line.type === 'out') {
    state.visible.push({ type: 'out', text: line.text, done: true })
    return
  }
  const entry: VisibleLine = { type: 'cmd', text: '', done: false }
  state.visible.push(entry)
  for (const ch of line.text) {
    if (cancelled) return
    entry.text += ch
    await wait(props.speed)
  }
  entry.done = true
}

onMounted(async () => {
  for (const line of props.lines) {
    if (cancelled) break
    if (line.delay) await wait(line.delay)
    await typeLine(line)
    await wait(220)
  }
})

onBeforeUnmount(() => {
  cancelled = true
  timers.forEach(t => clearTimeout(t))
})
</script>

<template>
  <div class="terminal">
    <div class="bar">
      <span class="dot r" />
      <span class="dot y" />
      <span class="dot g" />
      <span class="title">~/project</span>
    </div>
    <div class="body">
      <div
        v-for="(line, i) in state.visible"
        :key="i"
        class="line"
        :class="line.type"
      >
        <span v-if="line.type === 'cmd'" class="prompt">{{ prompt }}</span>
        <span class="text">{{ line.text }}<span
          v-if="line.type === 'cmd' && !line.done"
          class="caret"
        >▍</span></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.terminal {
  background: #0b1020;
  border-radius: 12px;
  overflow: hidden;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  box-shadow: 0 20px 50px -10px rgba(0,0,0,0.5);
  border: 1px solid #1e293b;
  max-width: 100%;
}
.bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  position: relative;
}
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.r { background: #ef4444; }
.dot.y { background: #eab308; }
.dot.g { background: #22c55e; }
.title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.8rem;
  color: #64748b;
}
.body {
  padding: 1.1rem 1.25rem;
  color: #e2e8f0;
  min-height: 180px;
  font-size: 0.95rem;
  line-height: 1.75;
}
.line { display: flex; gap: 0.7rem; white-space: pre-wrap; }
.line.cmd .prompt { color: #5eead4; font-weight: 600; user-select: none; }
.line.out { color: #94a3b8; padding-left: 1.35rem; }
.caret {
  display: inline-block;
  animation: blink 0.9s steps(1) infinite;
  color: #5eead4;
  margin-left: 2px;
}
@keyframes blink { 50% { opacity: 0; } }
</style>
