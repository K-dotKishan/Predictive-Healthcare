<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import RiskGauge from './components/RiskGauge.vue'
import ContribBars from './components/ContribBars.vue'
import CohortMap from './components/CohortMap.vue'

const features  = ref([])
const form      = reactive({})
const result    = ref(null)
const cohort    = ref([])
const loading   = ref(true)
const predicting = ref(false)
const error     = ref(null)

let timer = null

// ── Cohort stats derived from cohort data
const cohortStats = computed(() => {
  if (!cohort.value.length) return null
  const risks = cohort.value.map(p => p.risk)
  const high  = cohort.value.filter(p => p.tier === 'High').length
  const avg   = risks.reduce((a, b) => a + b, 0) / risks.length
  return {
    n: cohort.value.length,
    avgRisk: (avg * 100).toFixed(1),
    highRisk: high,
    highPct: ((high / cohort.value.length) * 100).toFixed(0)
  }
})

// ── API helpers
async function predict() {
  predicting.value = true
  error.value = null
  try {
    const r = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    if (!r.ok) throw new Error(`Server error ${r.status}`)
    result.value = await r.json()
  } catch (e) {
    error.value = 'Prediction failed — is the backend running?'
  } finally {
    predicting.value = false
  }
}

function reset() {
  features.value.forEach(f => { form[f.key] = f.default })
}

function debounced() {
  clearTimeout(timer)
  timer = setTimeout(predict, 140)
}

onMounted(async () => {
  try {
    features.value = await (await fetch('/api/features')).json()
    reset()
    cohort.value = await (await fetch('/api/cohort?n=120')).json()
    await predict()
  } catch (e) {
    error.value = 'Could not connect to backend. Start it with: uvicorn main:app --reload'
  } finally {
    loading.value = false
  }
  watch(form, debounced)
})
</script>

<template>
  <!-- ── Header ───────────────────────────────────────────── -->
  <header>
    <div class="header-left">
      <div class="header-icon">🏥</div>
      <div class="header-title">
        <h1>Predictive Healthcare Triage &amp; Readmission Risk Visualizer</h1>
        <p>Adjust risk factors to see 30-day readmission probability update in real-time · Demo model · Synthetic data only</p>
      </div>
    </div>
    <span class="badge">⚠ Demo — Not for clinical use</span>
  </header>

  <!-- ── Error banner ──────────────────────────────────────── -->
  <Transition name="fade">
    <div v-if="error" style="background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);
         color:#fca5a5;padding:12px 28px;font-size:.85rem;display:flex;align-items:center;gap:8px;">
      ⚠ {{ error }}
    </div>
  </Transition>

  <!-- ── Main layout ───────────────────────────────────────── -->
  <main>
    <!-- Sidebar: sliders -->
    <aside class="card sidebar">
      <div class="controls-header">
        <h2><span class="icon">🎛</span> Risk Factors</h2>
        <button class="btn btn-ghost" @click="reset(); predict()">↺ Reset</button>
      </div>

      <!-- Loading skeleton -->
      <template v-if="loading">
        <div v-for="i in 8" :key="i" class="skeleton" style="height:58px;border-radius:10px;margin-bottom:10px;" />
      </template>

      <!-- Sliders -->
      <div v-else class="slider-group">
        <div class="slider-item" v-for="f in features" :key="f.key">
          <div class="slider-label">
            <span>{{ f.label }}</span>
            <span class="slider-value">{{ form[f.key] }}</span>
          </div>
          <input
            type="range"
            :min="f.min"
            :max="f.max"
            :step="f.key === 'hba1c' ? 0.1 : 1"
            v-model.number="form[f.key]"
          />
        </div>
      </div>
    </aside>

    <!-- Dashboard right side -->
    <div class="dashboard">
      <!-- Cohort quick stats -->
      <div v-if="cohortStats && !loading" class="stats-row">
        <div class="stat-chip">
          <div class="sv">{{ cohortStats.n }}</div>
          <div class="sl">Cohort size</div>
        </div>
        <div class="stat-chip">
          <div class="sv">{{ cohortStats.avgRisk }}%</div>
          <div class="sl">Avg risk</div>
        </div>
        <div class="stat-chip">
          <div class="sv" style="color:var(--hi)">{{ cohortStats.highRisk }}</div>
          <div class="sl">High risk</div>
        </div>
        <div class="stat-chip">
          <div class="sv" style="color:var(--hi)">{{ cohortStats.highPct }}%</div>
          <div class="sl">High risk %</div>
        </div>
      </div>

      <!-- Gauge + Contrib bars row -->
      <div class="top-row">
        <!-- Risk gauge -->
        <div class="card">
          <h2>
            <span class="icon">📊</span> 30-day Readmission Risk
            <Transition name="fade">
              <span v-if="predicting" style="margin-left:auto;font-size:.7rem;color:var(--acc);animation:pulse 1s infinite">updating…</span>
            </Transition>
          </h2>
          <div v-if="loading" class="skeleton skeleton-gauge" />
          <template v-else-if="result">
            <RiskGauge :p="result.probability" :tier="result.tier" />
            <div style="text-align:center;margin-top:-8px;padding-bottom:6px;">
              <span class="tier-pill" :class="`tier-${result.tier}`">
                {{ result.tier === 'High' ? '🔴' : result.tier === 'Medium' ? '🟡' : '🟢' }}
                {{ result.tier }} Risk
              </span>
            </div>
          </template>
        </div>

        <!-- Contributing factors -->
        <div class="card">
          <h2><span class="icon">📈</span> Top Contributing Factors</h2>
          <div v-if="loading" class="skeleton skeleton-bars" />
          <ContribBars v-else-if="result" :data="result.contributions" />
          <p v-else style="color:var(--tx-mute);font-size:.85rem">No data yet</p>
        </div>
      </div>

      <!-- Cohort scatter map -->
      <div class="card bottom-row">
        <h2><span class="icon">🗺</span> Cohort Map — Age vs Readmission Risk</h2>
        <p style="font-size:.78rem;color:var(--tx-mute);margin-bottom:10px;">
          Each dot is a synthetic patient. Your patient is highlighted in blue.
        </p>
        <div v-if="loading" class="skeleton skeleton-map" />
        <CohortMap
          v-else-if="cohort.length"
          :cohort="cohort"
          :age="form.age"
          :risk="result ? result.probability : 0"
        />
      </div>
    </div>
  </main>

  <!-- ── Footer ────────────────────────────────────────────── -->
  <footer style="text-align:center;padding:18px;font-size:.75rem;color:var(--tx-dim);border-top:1px solid var(--border);">
    TechNova 2026 · LPU &nbsp;|&nbsp; Stack: Vue 3 · FastAPI · scikit-learn · D3.js &nbsp;|&nbsp;
    Model trained on 6 000 synthetic patients — <strong style="color:var(--hi)">not for clinical use</strong>
  </footer>
</template>

<style scoped>
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
</style>
