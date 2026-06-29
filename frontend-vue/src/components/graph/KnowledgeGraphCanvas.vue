<template>
  <div ref="containerRef" class="w-full h-full relative min-h-[300px] bg-slate-900 rounded-xl overflow-hidden">
    <svg ref="svgRef" class="w-full h-full block"></svg>
    <!-- Tooltip -->
    <div v-if="tooltip.node" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      class="absolute z-50 pointer-events-none bg-black/85 text-white rounded-lg p-3 max-w-[240px] text-xs backdrop-blur border border-white/20 shadow-xl">
      <p class="font-bold text-sm mb-1" :style="{ color: nodeColor(tooltip.node.type) }">{{ tooltip.node.name }}</p>
      <p class="text-gray-300 text-xs leading-snug">{{ tooltip.node.description || '暂无描述' }}</p>
      <p class="text-gray-500 text-[10px] mt-1">{{ typeLabel(tooltip.node.type) }}</p>
    </div>
    <!-- Legend -->
    <div class="absolute bottom-3 left-3 flex gap-3 text-[10px] z-10 bg-black/60 backdrop-blur px-3 py-2 rounded-lg">
      <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-disease"></span>疾病</span>
      <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-symptom"></span>症状</span>
      <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-drug"></span>药品</span>
      <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-dept"></span>科室</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'

interface Node {
  id: string; name: string; type: string; description?: string
  x?: number; y?: number; fx?: number | null; fy?: number | null; index?: number; vx?: number; vy?: number
}
interface Edge {
  id: string; source: string | Node; target: string | Node; relation: string; relation_name?: string
}
interface GraphData { nodes: Node[]; edges: Edge[]; center_node?: string }

const props = defineProps<{ graphData?: GraphData | null }>()
const emit = defineEmits<{ nodeClick: [node: Node] }>()

const containerRef = ref<HTMLDivElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const tooltip = ref<{ node: Node | null; x: number; y: number }>({ node: null, x: 0, y: 0 })
let simulation: d3.Simulation<any, any> | null = null
let resizeObserver: ResizeObserver | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const colors: Record<string, string> = {
  Disease: '#165DFF', Symptom: '#F53F3F', Drug: '#00B42A', Department: '#FF7D00',
}
const defaultColor = '#94a3b8'

function nodeColor(type: string) { return colors[type] || colors[type.charAt(0).toUpperCase() + type.slice(1)] || defaultColor }
function typeLabel(type: string) {
  const m: Record<string,string> = {Disease:'疾病',Symptom:'症状',Drug:'药品',Department:'科室',Check:'检查'}
  return m[type] || type
}
function edgeStyle(relation: string) {
  if (relation === 'contraindication') return { dash: '6,4', color: '#F53F3F', width: 2.5 }
  if (relation === 'complication') return { dash: '8,4', color: '#FF7D00', width: 2 }
  return { dash: '', color: '#475569', width: 1.5 }
}

watch(() => props.graphData, (data) => { if (data) renderGraph(data) })

function renderGraph(data: GraphData | null | undefined) {
  if (!data || !svgRef.value || !data.nodes?.length) return

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const rect = svgRef.value.getBoundingClientRect()
  // 高度塌陷保底
  const width = rect.width || 800
  const height = rect.height || 600
  svg.attr('viewBox', `0 0 ${width} ${height}`)

  const g = svg.append('g')
  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.3, 4])
    .on('zoom', (e) => g.attr('transform', e.transform))
  svg.call(zoom)

  // 🔴 核心防御 1：JSON 深拷贝彻底切断 Vue Proxy，防止 tick 高频坐标写入触发响应式狂抖
  const rawNodes = JSON.parse(JSON.stringify(data.nodes))
  const rawEdges = JSON.parse(JSON.stringify(data.edges))

  // 🔴 核心防御 2：过滤坏死边——source/target ID 找不到对应节点会导致 D3 算出 NaN，图谱崩溃消失
  const nodeIds = new Set(rawNodes.map((n: any) => n.id))
  const validLinks = rawEdges.filter((e: any) => nodeIds.has(e.source) && nodeIds.has(e.target))

  if (simulation) simulation.stop()

  simulation = d3.forceSimulation(rawNodes)
    .force('link', d3.forceLink(validLinks).id((d: any) => d.id).distance(100)) // 稍微拉开边长
    .force('charge', d3.forceManyBody().strength(-150)) // 【降低斥力】从-250降到-150，减少剧烈排斥
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(25).iterations(2)) // 【缩小碰撞半径】减少节点间的物理挤压
    .velocityDecay(0.45) // 【关键：增大阻尼=摩擦力】让节点极速安静下来

  // --- Edges ---
  const linkG = g.append('g').selectAll('g').data(validLinks).join('g')
  linkG.append('line')
    .attr('stroke', (d: any) => edgeStyle(d.relation).color)
    .attr('stroke-width', (d: any) => edgeStyle(d.relation).width)
    .attr('stroke-dasharray', (d: any) => edgeStyle(d.relation).dash)
    .attr('marker-end', (d: any) => d.relation === 'contraindication' ? 'url(#arrow-red)' : d.relation === 'complication' ? 'url(#arrow-orange)' : '')

  // --- Nodes ---
  const nodeG = g.append('g').selectAll('g').data(rawNodes).join('g')
    .attr('cursor', 'pointer')
    .on('click', (_e: any, d: any) => emit('nodeClick', d))
    .on('mouseenter', (e: MouseEvent, d: any) => { tooltip.value = { node: d, x: e.offsetX + 15, y: e.offsetY - 10 } })
    .on('mouseleave', () => tooltip.value = { node: null, x: 0, y: 0 })
    .call(d3.drag<any, any>()
      .on('start', (e: any, d: any) => {
        // 【核心修复】不要用 alphaTarget(0.3) 持续加热！
        // 改用 alpha(0.1) 只给一个瞬间的微小扰动能量，图谱会在拖动时依然保持冷却
        if (!e.active) simulation?.alpha(0.1).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (e: any, d: any) => {
        d.fx = e.x
        d.fy = e.y
      })
      .on('end', (e: any, d: any) => {
        if (!e.active) simulation?.alphaTarget(0)
        // 【体验升级】注释掉 fx/fy 释放！
        // 拖动完松手后节点被"钉"在原地，方便用户手动整理图谱排版
        // d.fx = null; d.fy = null;
      }))

  nodeG.append('circle')
    .attr('r', (d: any) => Math.min(18, 8 + (validLinks.filter((l: any) => (l.source as any)?.id === d.id || (l.target as any)?.id === d.id).length * 2)))
    .attr('fill', (d: any) => d3.color(nodeColor(d.type))?.darker(0.4)?.toString() || defaultColor)
    .attr('stroke', (d: any) => nodeColor(d.type))
    .attr('stroke-width', 2.5)

  nodeG.append('text')
    .text((d: any) => d.name.length > 5 ? d.name.slice(0, 5) + '…' : d.name)
    .attr('text-anchor', 'middle').attr('dy', 4)
    .attr('fill', '#fff').style('font-size', '10px').style('pointer-events', 'none')

  // Arrow markers
  svg.append('defs').html(`
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#F53F3F"/></marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#FF7D00"/></marker>
  `)

  simulation.on('tick', () => {
    linkG.selectAll('line')
      .attr('x1', (d: any) => (d.source as any).x).attr('y1', (d: any) => (d.source as any).y)
      .attr('x2', (d: any) => (d.target as any).x).attr('y2', (d: any) => (d.target as any).y)
    nodeG.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

onMounted(() => {
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = window.setTimeout(() => { if (props.graphData) renderGraph(props.graphData) }, 200)
    })
    resizeObserver.observe(containerRef.value)
  }
  if (props.graphData) nextTick(() => renderGraph(props.graphData))
})

onBeforeUnmount(() => {
  simulation?.stop()
  resizeObserver?.disconnect()
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped>
.bg-disease { background: #165DFF; }
.bg-symptom { background: #F53F3F; }
.bg-drug { background: #00B42A; }
.bg-dept { background: #FF7D00; }
</style>
