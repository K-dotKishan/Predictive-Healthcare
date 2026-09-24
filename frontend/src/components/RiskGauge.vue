<script setup>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ p: Number, tier: String })
const el = ref()

const W = 300, H = 170
const CX = W / 2, CY = 135
const R_OUT = 100, R_IN = 72

const COLORS = { Low: '#22c55e', Medium: '#f59e0b', High: '#ef4444' }
const ZONES = [
  { from: 0,    to: 0.25, color: 'rgba(34,197,94,.18)',   label: 'Low'    },
  { from: 0.25, to: 0.50, color: 'rgba(245,158,11,.18)',  label: 'Med'    },
  { from: 0.50, to: 1.00, color: 'rgba(239,68,68,.18)',   label: 'High'   },
]

function pToAngle(p) { return -Math.PI / 2 + Math.PI * p }

const arc = d3.arc().innerRadius(R_IN).outerRadius(R_OUT)

let needleSel, percentSel, initialized = false

function render() {
  if (!initialized || !el.value) return
  const svg = d3.select(el.value)
  const endAngle = pToAngle(props.p)
  const tierColor = COLORS[props.tier] ?? '#38bdf8'

  // animate needle arc
  needleSel.transition().duration(350).ease(d3.easeCubicOut)
    .attrTween('d', function () {
      const prev = this._end ?? -Math.PI / 2
      const interp = d3.interpolate(prev, endAngle)
      this._end = endAngle
      return t => arc.startAngle(-Math.PI / 2).endAngle(interp(t))()
    })
    .attr('fill', tierColor)

  // percent label
  percentSel.transition().duration(350)
    .tween('text', function () {
      const prev = parseFloat(this.textContent) || 0
      const interp = d3.interpolate(prev, props.p * 100)
      return t => { this.textContent = interp(t).toFixed(1) + '%' }
    })
    .attr('fill', tierColor)

  // tier label
  svg.select('.tier-label')
    .text(props.tier + ' Risk')
    .attr('fill', tierColor)
}

onMounted(() => {
  const svg = d3.select(el.value)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .attr('width', '100%')

  const g = svg.append('g').attr('transform', `translate(${CX},${CY})`)

  // Background track
  g.append('path')
    .attr('d', arc.startAngle(-Math.PI / 2).endAngle(Math.PI / 2)())
    .attr('fill', '#1e293b')

  // Colored zone segments
  ZONES.forEach(z => {
    g.append('path')
      .attr('d', arc.startAngle(pToAngle(z.from)).endAngle(pToAngle(z.to))())
      .attr('fill', z.color)
  })

  // Zone boundary ticks
  ;[0, 0.25, 0.5, 0.75, 1].forEach(v => {
    const a = pToAngle(v)
    const x1 = Math.cos(a) * R_IN, y1 = Math.sin(a) * R_IN
    const x2 = Math.cos(a) * R_OUT, y2 = Math.sin(a) * R_OUT
    g.append('line').attr('x1', x1).attr('y1', y1).attr('x2', x2).attr('y2', y2)
      .attr('stroke', '#0a0f1e').attr('stroke-width', 2)
  })

  // Needle arc (animated)
  needleSel = g.append('path')
    .attr('d', arc.startAngle(-Math.PI / 2).endAngle(-Math.PI / 2)())
    .attr('fill', '#38bdf8')

  // Center circle
  g.append('circle').attr('r', 6).attr('fill', '#1e293b').attr('stroke', '#475569').attr('stroke-width', 2)

  // Percentage label
  percentSel = g.append('text')
    .attr('y', -20).attr('text-anchor', 'middle')
    .style('font-size', '28px').style('font-weight', 700)
    .style('font-family', "'JetBrains Mono', monospace")
    .text('0.0%')

  // Tier label
  g.append('text').attr('class', 'tier-label')
    .attr('y', 2).attr('text-anchor', 'middle')
    .style('font-size', '13px').style('font-weight', 600)

  // Scale labels: 0%, 25%, 50%, 75%, 100%
  ;[0, 0.25, 0.5, 0.75, 1].forEach(v => {
    const a = pToAngle(v)
    const r = R_OUT + 16
    g.append('text')
      .attr('x', Math.cos(a) * r).attr('y', Math.sin(a) * r + 4)
      .attr('text-anchor', 'middle').style('font-size', '10px').attr('fill', '#64748b')
      .text(`${(v * 100).toFixed(0)}%`)
  })

  initialized = true
  render()
})

watch(() => [props.p, props.tier], render)
</script>

<template>
  <svg ref="el"></svg>
</template>
