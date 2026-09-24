"""
FastAPI + scikit-learn service for 30-day readmission risk.
Demo only — trained on synthetic data. NOT for clinical use.
"""
from __future__ import annotations

import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Feature schema ──────────────────────────────────────────────────────────
#   key: (label, min, max, default)
FEATURES: dict[str, tuple[str, float, float, float]] = {
    "age":               ("Age (years)",              18,   95,  65.0),
    "prior_admissions":  ("Prior admissions (12 m)",   0,   10,   1.0),
    "length_of_stay":    ("Length of stay (days)",      1,   30,   5.0),
    "comorbidity_index": ("Comorbidity index (CCI)",    0,   10,   3.0),
    "hba1c":             ("HbA1c (%)",                 4.0, 14.0,  6.5),
    "systolic_bp":       ("Systolic BP (mmHg)",        80,  200, 130.0),
    "num_medications":   ("Medications count",          0,   25,   6.0),
    "er_visits":         ("ER visits (6 m)",            0,    8,   1.0),
}
KEYS = list(FEATURES.keys())

# ── Synthetic training data ─────────────────────────────────────────────────
rng = np.random.default_rng(42)


def _synth(n: int) -> tuple[np.ndarray, np.ndarray]:
    lo = np.array([FEATURES[k][1] for k in KEYS], dtype=float)
    hi = np.array([FEATURES[k][2] for k in KEYS], dtype=float)
    X = lo + rng.beta(2, 3, (n, len(KEYS))) * (hi - lo)
    # logistic risk score (roughly calibrated for ~25 % base rate)
    z = (
        0.030 * (X[:, 0] - 65)      # age
        + 0.45  * X[:, 1]            # prior admissions
        + 0.10  * X[:, 2]            # LOS
        + 0.35  * X[:, 3]            # comorbidity
        + 0.25  * (X[:, 4] - 6.5)   # HbA1c
        + 0.008 * (X[:, 5] - 130)   # systolic BP
        + 0.05  * X[:, 6]            # medications
        + 0.40  * X[:, 7]            # ER visits
        - 2.2
    )
    y = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    return X, y


from sklearn.ensemble import GradientBoostingClassifier

X_train, y_train = _synth(6_000)
model = GradientBoostingClassifier(
    n_estimators=150, max_depth=3, learning_rate=0.1,
    subsample=0.8, random_state=1
).fit(X_train, y_train)

COHORT_MEAN = X_train.mean(axis=0)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _risk(v: np.ndarray) -> float:
    return float(model.predict_proba(np.atleast_2d(v))[0, 1])


def _tier(p: float) -> str:
    if p >= 0.50:
        return "High"
    if p >= 0.25:
        return "Medium"
    return "Low"


# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Readmission Risk API",
    description="Synthetic-data demo. Not for clinical use.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ─────────────────────────────────────────────────────────
class PatientIn(BaseModel):
    age:               float = Field(65,  ge=18,  le=95)
    prior_admissions:  float = Field(1,   ge=0,   le=10)
    length_of_stay:    float = Field(5,   ge=1,   le=30)
    comorbidity_index: float = Field(3,   ge=0,   le=10)
    hba1c:             float = Field(6.5, ge=4.0, le=14.0)
    systolic_bp:       float = Field(130, ge=80,  le=200)
    num_medications:   float = Field(6,   ge=0,   le=25)
    er_visits:         float = Field(1,   ge=0,   le=8)


class ContribItem(BaseModel):
    key:    str
    label:  str
    impact: float


class PredictOut(BaseModel):
    probability:   float
    tier:          str
    contributions: list[ContribItem]


class FeatureInfo(BaseModel):
    key:     str
    label:   str
    min:     float
    max:     float
    default: float


class CohortPatient(BaseModel):
    id:               str
    age:              float
    prior_admissions: float
    risk:             float
    tier:             str


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/features", response_model=list[FeatureInfo], tags=["meta"])
def get_features() -> list[FeatureInfo]:
    """Return feature metadata (min, max, default) for slider rendering."""
    return [
        FeatureInfo(key=k, label=v[0], min=v[1], max=v[2], default=v[3])
        for k, v in FEATURES.items()
    ]


@app.post("/api/predict", response_model=PredictOut, tags=["inference"])
def predict(patient: PatientIn) -> PredictOut:
    """
    Predict 30-day readmission probability and return the top contributing
    features using a leave-one-out perturbation approach.
    """
    v = np.array([getattr(patient, k) for k in KEYS], dtype=float)
    base = _risk(v)

    contributions: list[ContribItem] = []
    for i, k in enumerate(KEYS):
        w = v.copy()
        w[i] = COHORT_MEAN[i]
        contributions.append(
            ContribItem(key=k, label=FEATURES[k][0], impact=base - _risk(w))
        )
    contributions.sort(key=lambda c: -abs(c.impact))

    return PredictOut(probability=base, tier=_tier(base), contributions=contributions)


@app.get("/api/cohort", response_model=list[CohortPatient], tags=["cohort"])
def get_cohort(n: int = Query(default=80, ge=10, le=300)) -> list[CohortPatient]:
    """
    Return a random synthetic cohort of *n* patients for the scatter map.
    """
    Xc, _ = _synth(n)
    probs = model.predict_proba(Xc)[:, 1]
    return [
        CohortPatient(
            id=f"P-{1000 + i}",
            age=float(row[0]),
            prior_admissions=float(row[1]),
            risk=float(p),
            tier=_tier(float(p)),
        )
        for i, (row, p) in enumerate(zip(Xc, probs))
    ]


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "model": "GradientBoostingClassifier", "train_n": len(X_train)}
