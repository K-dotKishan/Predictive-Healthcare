# Predictive Healthcare Triage & Patient Readmission Risk Visualizer

> **TechNova 2026 · LPU** &nbsp;|&nbsp; Demo only — trained on synthetic data — **NOT for clinical use**

An interactive clinical dashboard that predicts 30-day hospital readmission probability using a Gradient Boosting model and visualises the results in real-time with D3.js.

---

## Stack

| Layer     | Tech                                      |
|-----------|-------------------------------------------|
| Frontend  | Vue 3 (Composition API) + Vite            |
| Charts    | D3.js v7                                  |
| Backend   | FastAPI + Uvicorn                         |
| ML Model  | scikit-learn GradientBoostingClassifier   |
| Data      | 6 000 synthetic patients (NumPy RNG)      |

---

## Features

- **8 interactive sliders** — Age, Prior Admissions, Length of Stay, Comorbidity Index, HbA1c, Systolic BP, Medications, ER Visits
- **Animated D3 gauge** — semi-circular risk meter with Low / Medium / High colour zones
- **Contributing factors chart** — diverging bar chart showing per-feature impact vs cohort mean (leave-one-out perturbation)
- **Cohort scatter map** — Age vs Risk scatter plot with 120 synthetic patients; your patient highlighted with an animated "You" marker
- **Live cohort stats** — cohort size, average risk, high-risk count/percentage
- **Dark UI** — polished slate-blue theme with hover tooltips and loading skeletons
- **Fully responsive** — single-column layout on mobile

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`.

---

## API Reference

| Method | Path           | Description                                           |
|--------|----------------|-------------------------------------------------------|
| GET    | /api/features  | Feature metadata (label, min, max, default)           |
| POST   | /api/predict   | Predict risk + contributions for a patient payload    |
| GET    | /api/cohort    | Random synthetic cohort (`?n=120`, max 300)           |
| GET    | /health        | Health check                                          |

### POST /api/predict — request body

```json
{
  "age": 72,
  "prior_admissions": 3,
  "length_of_stay": 7,
  "comorbidity_index": 5,
  "hba1c": 8.2,
  "systolic_bp": 148,
  "num_medications": 10,
  "er_visits": 2
}
```

### POST /api/predict — response

```json
{
  "probability": 0.631,
  "tier": "High",
  "contributions": [
    { "key": "prior_admissions", "label": "Prior admissions (12 m)", "impact": 0.218 },
    ...
  ]
}
```

---

## Project structure

```
readmission-visualizer/
├── backend/
│   ├── main.py            FastAPI app + ML model
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue          Layout, sliders, stat chips
        ├── style.css        Dark theme design system
        └── components/
            ├── RiskGauge.vue    Animated semi-circular gauge
            ├── ContribBars.vue  Diverging impact bar chart
            └── CohortMap.vue    Age vs Risk scatter map
```
