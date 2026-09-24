<script setup>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ cohort: Array, age: Number, risk: Number })
const el = ref()

const W  = 640, H  = 300
const M  = { l: 52, r: 20, t: 14, b: 44 }
const iW = W - M.l - M.r
const iH = H - M.t - M.b

const COL = { Low: '#22c55e', Medium: '#f59e0b', High: '#ef4444' }

const x = d3.scaleLinear([18, 95], [0, iW])
const y = d3.scaleLinear([0, 1],   [iH, 0])

let svg, gMain, meDot, xAxisG, yAxisG

function buildSvg() {
  if (!el.value) return

  svg = d3.select(el.value)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .attr('width', '100%')

  svg.selectAll('*').remove()

  gMain = svg.append('g').attr('transform', `translate(${M.l},${M.t})`)

  // ── Grid lines
  const yTicks = [0, 0.25, 0.5, 0.75, 1]
  yTicks.forEach(v => {
    gMain.append('line')
      .attr('x1', 0).attr('x2', iW)
      .attr('y1', y(v)).attr('y2', y(v))
      .attr('stroke', '#1e2d45').attr('stroke-dasharray', '4 3')
  })
  const xTicks = [20, 30, 40, 50, 60, 70, 80, 90]
  xTicks.forEach(v => {
    gMain.append('line')
      .attr('x1', x(v)).attr('x2', x(v))
      .attr('y1', 0).attr('y2', iH)
      .attr('stroke', '#1e2d45').attr('stroke-dasharray', '4 3')
  })

  // ── Risk zone bands
  const zones = [
    { y0: 0,    y1: 0.25, color: 'rgba(34,197,94,.04)'   },
    { y0: 0.25, y1: 0.50, color: 'rgba(245,158,11,.05)'  },
    { y0: 0.50, y1: 1.00, color: 'rgba(239,68,68,.06)'   },
  ]
  zones.forEach(z => {
    gMain.append('rect')
      .attr('x', 0).attr('width', iW)
      .attr('y', y(z.y1)).attr('height', y(z.y0) - y(z.y1))
      .attr('fill', z.color)
  })

  // ── Axes
  xAxisG = gMain.append('g').attr('transform', `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(8).tickSize(-iH).tickPadding(8))
  xAxisG.select('.domain').remove()
  xAxisG.selectAll('.tick line').attr('stroke', 'none')
  xAxisG.selectAll('text').attr('fill', '#64748b').style('font-size', '11px')

  yAxisG = gMain.append('g')
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('.0%')).tickSize(-iW).tickPadding(8))
  yAxisG.select('.domain').remove()
  yAxisG.selectAll('.tick line').attr('stroke', 'none')
  yAxisG.selectAll('text').attr('fill', '#64748b').style('font-size', '11px')

  // Axis labels
  svg.append('text')
    .attr('x', M.l + iW / 2).attr('y', H - 4)
    .attr('text-anchor', 'middle').style('font-size', '11px').attr('fill', '#475569')
    .text('Patient Age')

  svg.append('text')
    .attr('transform', `rotate(-90)`)
    .attr('x', -(M.t + iH / 2)).attr('y', 14)
    .attr('text-anchor', 'middle').style('font-size', '11px').attr('fill', '#475569')
    .text('30-day Readmission Risk')

  // ── Cohort dots
  const tooltip = d3.select('#cohort-tooltip')

  gMain.selectAll('circle.pt')
    .data(props.cohort)
    .join('circle').attr('class', 'pt')
    .attr('cx', d => x(d.age))
    .attr('cy', d => y(d.risk))
    .attr('r', 0)
    .attr('fill', d => COL[d.tier])
    .attr('opacity', .7)
    .attr('stroke', 'none')
    .on('mousemove', (event, d) => {
      tooltip
        .style('opacity', 1)
        .style('left', (event.clientX + 14) + 'px')
        .style('top',  (event.clientY - 36) + 'px')
        .html(`<strong>${d.id}</strong><br/>
               Age: ${d.age.toFixed(0)}<br/>
               Risk: <span style="color:${COL[d.tier]}">${(d.risk * 100).toFixed(1)}%</span><br/>
               Tier: <span style="color:${COL[d.tier]}">${d.tier}</span>`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
    .transition().duration(600).delay((_, i) => i * 4)
    .attr('r', 4.5)

  // Legend
  const legendData = [
    { label: 'Low  (<25%)',    color: COL.Low    },
    { label: 'Medium (25–50%)', color: COL.Medium },
    { label: 'High (>50%)',    color: COL.High   },
  ]
  const leg = svg.append('g').attr('transform', `translate(${M.l + iW - 140},${M.t + 4})`)
  legendData.forEach((d, i) => {
    leg.append('circle').attr('cx', 6).attr('cy', i * 16 + 6).attr('r', 5).attr('fill', d.color).attr('opacity', .8)
    leg.append('text').attr('x', 16).attr('y', i * 16 + 10)
      .style('font-size', '10px').attr('fill', '#94a3b8').text(d.label)
  })

  // ── My patient dot (on top)
  meDot = gMain.append('g')

  // outer ring
  meDot.append('circle').attr('class', 'me-ring').attr('r', 14)
    .attr('fill', 'none').attr('stroke', '#38bdf8').attr('stroke-width', 1.5).attr('opacity', .4)
  // inner ring
  meDot.append('circle').attr('class', 'me-dot').attr('r', 8)
    .attr('fill', 'none').attr('stroke', '#38bdf8').attr('stroke-width', 2.5)
  // center
  meDot.append('circle').attr('r', 4).attr('fill', '#38bdf8')

  // "You" label
  meDot.append('text').attr('class', 'me-label')
    .attr('y', -16).attr('text-anchor', 'middle')
    .style('font-size', '11px').style('font-weight', 700).attr('fill', '#38bdf8')
    .text('You')

  updateMe()
}

function updateMe() {
  if (!meDot) return
  meDot.transition().duration(250).ease(d3.easeCubicOut)
    .attr('transform', `translate(${x(props.age)},${y(props.risk)})`)
}

onMounted(buildSvg)
watch(() => props.cohort, buildSvg)
watch(() => [props.age, props.risk], updateMe)
</script>

<template>
  <svg ref="el"></svg>
  <teleport to="body">
    <div id="cohort-tooltip" class="tooltip" style="opacity:0;"></div>
  </teleport>
</template>
