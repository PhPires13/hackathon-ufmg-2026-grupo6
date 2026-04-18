<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { gsap } from 'gsap'

const props = withDefaults(defineProps<{
  value: number
  prefix?: string
  suffix?: string
  label?: string
  duration?: number
  decimals?: number
}>(), {
  duration: 1.8,
  decimals: 0,
  prefix: '',
  suffix: ''
})

const displayValue = ref(0)
let tween: gsap.core.Tween | null = null

onMounted(() => {
  const state = { n: 0 }
  tween = gsap.to(state, {
    n: props.value,
    duration: props.duration,
    ease: 'power3.out',
    onUpdate: () => {
      displayValue.value = state.n
    }
  })
})

onBeforeUnmount(() => {
  tween?.kill()
})

function formatted(n: number) {
  const parts = n.toFixed(props.decimals).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return parts.join(',')
}
</script>

<template>
  <div class="stat-number">
    <div class="value">
      <span v-if="prefix" class="prefix">{{ prefix }}</span>
      <span class="num">{{ formatted(displayValue) }}</span>
      <span v-if="suffix" class="suffix">{{ suffix }}</span>
    </div>
    <div v-if="label" class="label">{{ label }}</div>
  </div>
</template>

<style scoped>
.stat-number {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.value {
  font-size: clamp(3rem, 7.5vw, 5.75rem);
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: #FFFFFF;
  letter-spacing: -0.035em;
  font-family: 'Inter', sans-serif;
}
.prefix, .suffix {
  font-size: 0.5em;
  vertical-align: top;
  color: #F5A623;
  font-weight: 700;
  margin: 0 0.12em;
}
.label {
  font-size: 0.78rem;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-weight: 600;
  text-align: center;
  max-width: 220px;
}
</style>
