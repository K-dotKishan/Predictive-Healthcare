<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ data: Array })
const el = ref()

const W = 380, ROW_H = 38, PAD = { l: 10, r: 12, t: 8, b: 28 }
const CENTER_X = 175   // where the zero-line sits
const BAR_MAX  = 160   // max bar extends this many px from center

function draw() {
  if (!el.value || !props.data?.length) return

  const data   = props.data.slice(0, 6)
  const H      = data.length * ROW_H + PAD.t + PAD.b
  const maxAbs = Math.max(0.001, d3.max(data, d => Math.abs(d.impact)))
  const scale  = d3.scaleLinear([-maxAbs, maxAbs], [-BAR_MAX, BAR_MAX])

  const svg = d3.select(el.value)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .attr('width', '100%')

  svg.selectAll('*').remove()

  // ── background rows (zebra)
  svg.selectAll('rect.row')
    .data(data).join('rect').attr('class', 'row')
    .attr('x', 0).attr('y', (_, i) => PAD.t + i * ROW_H)
    .attr('width', W).attr('height', ROW_H)
    .attr('fill', (_, i) => i % 2 === 0 ? 'rgba(255,255,255,.02)' : 'transparent')

  // ── center line
  svg.append('line')
    .attr('x1', CENTER_X).attr('x2', CENTER_X)
    .attr('y1', PAD.t).attr('y2', H - PAD.b)
    .attr('stroke', '#2e4060').attr('stroke-width', 1)

  // ── axis ticks at bottom
  const xAxis = d3.scaleLinear([-maxAbs, maxAbs], [CENTER_X - BAR_MAX, CENTER_X + BAR_MAX])
  const tickVals = [-maxAbs, -maxAbs / 2, 0, maxAbs / 2, maxAbs]
  tickVals.forEach(v => {
    const x = xAxis(v)
    svg.append('line')
      .attr('x1', x).attr('x2', x)
      .attr('y1', H - PAD.b).attr('y2', H - PAD.b + 4)
      .attr('stroke', '#475569')
    svg.append('text')
      .attr('x', x).attr('y', H - PAD.b + 14)
      .attr('text-anchor', 'middle')
      .style('font-size', '9px').attr('fill', '#64748b')
      .text(v === 0 ? '0' : (v > 0 ? '+' : '') + (v * 100).toFixed(0) + 'pp')
  })

  // ── axis label
  svg.append('text')
    .attr('x', W / 2).attr('y', H - 2)
    .attr('text-anchor', 'middle')
    .style('font-size', '9px').attr('fill', '#475569')
    .text('Risk impact vs cohort mean')

  // ── bars + labels
  const g = svg.selectAll('g.bar-row')
    .data(data).join('g').attr('class', 'bar-row')
    .attr('transform', (_, i) => `translate(0,${PAD.t + i * ROW_H})`)

  const barW = d => Math.max(2, Math.abs(scale(d.impact)))
  const barX = d => d.impact >= 0 ? CENTER_X : CENTER_X + scale(d.impact)

  // bars — initial width 0, then transition in
  g.append('rect')
    .attr('y', 8).attr('height', ROW_H - 16).attr('rx', 4)
    .attr('fill', d => d.impact > 0 ? '#ef4444' : '#22c55e')
    .attr('opacity', .85)
    .attr('x', d => barX(d))
    .attr('width', 0)
    .transition().duration(500).ease(d3.easeCubicOut)
    .attr('width', d => barW(d))

  // label on left
  g.append('text')
    .attr('x', PAD.l).attr('y', ROW_H / 2 + 4)
    .style('font-size', '11px').attr('fill', '#cbd5e1')
    .text(d => d.label)

  // value badge on right
  g.append('text')
    .attr('x', W - PAD.r).attr('y', ROW_H / 2 + 4)
    .attr('text-anchor', 'end')
    .style('font-size', '10px').style('font-weight', 600)
    .style('font-family', "'JetBrains Mono', monospace")
    .attr('fill', d => d.impact > 0 ? '#f87171' : '#4ade80')
    .text(d => (d.impact > 0 ? '▲' : '▼') + ' ' + Math.abs(d.impact * 100).toFixed(1) + 'pp')

  // invisible hover overlay for tooltip
  const tooltip = d3.select('#contrib-tooltip')
  g.append('rect')
    .attr('width', W).attr('height', ROW_H)
    .attr('fill', 'transparent')
    .on('mousemove', (event, d) => {
      tooltip
        .style('opacity', 1)
        .style('left', (event.clientX + 14) + 'px')
        .style('top',  (event.clientY - 30) + 'px')
        .html(`<strong>${d.label}</strong><br/>
               Impact: <span style="color:${d.impact > 0 ? '#f87171' : '#4ade80'}">${d.impact > 0 ? '+' : ''}${(d.impact * 100).toFixed(2)} pp</span><br/>
               <span style="font-size:.7rem;color:#64748b">vs cohort mean</span>`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
}

onMounted(() => { nextTick(draw) })
watch(() => props.data, () => nextTick(draw), { deep: true })
</script>

<template>
  <svg ref="el"></svg>
  <!-- Global tooltip element (rendered once, moved by JS) -->
  <teleport to="body">
    <div id="contrib-tooltip" class="tooltip" style="opacity:0;"></div>
  </teleport>
</template>
