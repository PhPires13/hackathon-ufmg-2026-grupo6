<script setup lang="ts">
import { computed } from 'vue'
import { useSlideContext, useNav } from '@slidev/client'

interface Node {
  id: string
  label: string
  x: number
  y: number
  w?: number
  h?: number
}
interface Edge {
  from: string
  to: string
  label?: string
}

const props = withDefaults(defineProps<{
  nodes: Node[]
  edges: Edge[]
  width?: number
  height?: number
}>(), {
  width: 800,
  height: 400
})

const { $clicks } = useSlideContext()
const { isPrintMode } = useNav()
const revealed = computed(() =>
  isPrintMode.value ? props.nodes.length + props.edges.length + 1 : $clicks.value
)

const nodeMap = computed(() =>
  Object.fromEntries(props.nodes.map(n => [n.id, n]))
)

function nodeBox(id: string) {
  const n = nodeMap.value[id]
  const w = n.w ?? 120
  const h = n.h ?? 60
  return { x: n.x, y: n.y, w, h, cx: n.x + w / 2, cy: n.y + h / 2 }
}

function edgeGeom(edge: Edge) {
  const a = nodeBox(edge.from)
  const b = nodeBox(edge.to)
  return {
    x1: a.cx, y1: a.cy, x2: b.cx, y2: b.cy,
    mx: (a.cx + b.cx) / 2,
    my: (a.cy + b.cy) / 2
  }
}

const isNodeVisible = (idx: number) => revealed.value > idx
const isEdgeVisible = (idx: number) => revealed.value > props.nodes.length + idx
</script>

<template>
  <svg
    :viewBox="`0 0 ${width} ${height}`"
    class="arch-flow"
    :class="{ 'print-static': isPrintMode }"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <marker
        id="arrow-head"
        viewBox="0 0 10 10"
        refX="9" refY="5"
        markerWidth="7" markerHeight="7"
        orient="auto-start-reverse"
      >
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#F5A623" />
      </marker>
      <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#F5A623" flood-opacity="0.12" />
      </filter>
    </defs>

    <g>
      <g
        v-for="(edge, i) in edges"
        :key="`e-${i}`"
        class="edge"
        :class="{ visible: isEdgeVisible(i) }"
      >
        <line
          :x1="edgeGeom(edge).x1"
          :y1="edgeGeom(edge).y1"
          :x2="edgeGeom(edge).x2"
          :y2="edgeGeom(edge).y2"
          stroke="#F5A623"
          stroke-width="2"
          stroke-dasharray="5 5"
          marker-end="url(#arrow-head)"
        />
        <text
          v-if="edge.label"
          :x="edgeGeom(edge).mx"
          :y="edgeGeom(edge).my - 10"
          text-anchor="middle"
          fill="#6B7280"
          font-size="12"
          font-weight="500"
          font-family="Inter, sans-serif"
        >{{ edge.label }}</text>
      </g>
    </g>

    <g>
      <g
        v-for="(node, i) in nodes"
        :key="node.id"
        class="node"
        :class="{ visible: isNodeVisible(i) }"
      >
        <rect
          :x="node.x"
          :y="node.y"
          :width="node.w ?? 120"
          :height="node.h ?? 60"
          rx="8"
          fill="#141414"
          stroke="#F5A623"
          stroke-width="1.5"
          filter="url(#node-shadow)"
        />
        <text
          :x="node.x + (node.w ?? 120) / 2"
          :y="node.y + (node.h ?? 60) / 2 + 5"
          text-anchor="middle"
          fill="#F3F4F6"
          font-size="14"
          font-weight="600"
          font-family="Inter, sans-serif"
        >{{ node.label }}</text>
      </g>
    </g>
  </svg>
</template>

<style scoped>
.arch-flow {
  width: 100%;
  height: auto;
  max-height: 70vh;
}
.node, .edge {
  opacity: 0;
  transform-origin: center;
  transition: opacity 450ms ease, transform 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.node { transform: scale(0.85); }
.node.visible { opacity: 1; transform: scale(1); }
.edge.visible { opacity: 1; }
.edge line {
  stroke-dashoffset: 100;
  animation: dash 1s ease forwards;
}
.edge.visible line { animation: dash 800ms ease forwards; }
@keyframes dash { to { stroke-dashoffset: 0; } }

.arch-flow.print-static .node,
.arch-flow.print-static .edge {
  opacity: 1 !important;
  transform: none !important;
  transition: none !important;
}
.arch-flow.print-static .edge line {
  stroke-dashoffset: 0 !important;
  animation: none !important;
}
</style>
