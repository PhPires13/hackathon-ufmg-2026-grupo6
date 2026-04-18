<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useSlideContext } from '@slidev/client'

const props = withDefaults(defineProps<{
  text: string
  author?: string
  autoPlay?: boolean
  stagger?: number
}>(), {
  autoPlay: false,
  stagger: 70
})

const { $clicks } = useSlideContext()
const mounted = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})

const words = computed(() => props.text.split(/\s+/).filter(Boolean))
const wordsVisible = computed(() => {
  if (props.autoPlay) return mounted.value ? words.value.length : 0
  return $clicks.value
})

const authorVisible = computed(() => {
  if (props.autoPlay) return mounted.value
  return $clicks.value >= words.value.length
})
</script>

<template>
  <figure class="quote-reveal">
    <div class="mark" aria-hidden="true">"</div>
    <blockquote>
      <span
        v-for="(w, i) in words"
        :key="i"
        class="word"
        :class="{ on: i < wordsVisible }"
        :style="{ transitionDelay: autoPlay ? `${i * stagger}ms` : undefined }"
      >{{ w }}<span>&nbsp;</span></span>
    </blockquote>
    <figcaption
      v-if="author"
      class="author"
      :class="{ on: authorVisible }"
      :style="{ transitionDelay: autoPlay ? `${words.length * stagger + 200}ms` : undefined }"
    >— {{ author }}</figcaption>
  </figure>
</template>

<style scoped>
.quote-reveal {
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
  position: relative;
  padding: 2rem 1rem;
}
.mark {
  font-family: 'Georgia', serif;
  font-size: 8rem;
  line-height: 0.5;
  color: #5eead4;
  opacity: 0.25;
  position: absolute;
  top: 2rem;
  left: 50%;
  transform: translateX(-50%);
}
blockquote {
  position: relative;
  font-size: clamp(1.6rem, 3.8vw, 2.6rem);
  line-height: 1.4;
  font-weight: 500;
  font-style: italic;
  color: #e2e8f0;
  margin: 0;
}
.word {
  display: inline-block;
  opacity: 0;
  transform: translateY(14px);
  filter: blur(6px);
  transition: opacity 700ms cubic-bezier(0.22, 1, 0.36, 1),
              transform 700ms cubic-bezier(0.22, 1, 0.36, 1),
              filter 700ms ease;
}
.word.on {
  opacity: 1;
  transform: none;
  filter: blur(0);
}
.author {
  margin-top: 2rem;
  color: #94a3b8;
  font-size: 1.1rem;
  letter-spacing: 0.08em;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 500ms ease, transform 500ms ease;
}
.author.on { opacity: 1; transform: none; }
</style>
