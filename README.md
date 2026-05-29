# 🏥 Health Checker Pro

> A **production-grade, enterprise AI clinical diagnostic platform** — built to demonstrate end-to-end Data Science, ML Engineering, and full-stack health-tech capabilities.

[![CI Pipeline](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml/badge.svg)](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Render-Live%20Demo-E007B5?logo=render&logoColor=white)](https://health-checker-4sxc.onrender.com)
![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![scikit-learn](https://img.shields.io/badge/scikit--learn-HistGradientBoosting-orange?logo=scikitlearn)
![SHAP](https://img.shields.io/badge/XAI-SHAP-purple)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue?logo=google)
![FastAPI](https://img.shields.io/badge/ML%20Service-FastAPI-teal?logo=fastapi)
![Tests](https://img.shields.io/badge/Tests-137%20passed-brightgreen)
![FHIR](https://img.shields.io/badge/Interop-FHIR%20R4-red)
![HIPAA](https://img.shields.io/badge/Compliance-HIPAA%20Audit-green)

🚀 **Live Demo:** [health-checker-4sxc.onrender.com](https://health-checker-4sxc.onrender.com)

---

## 🎯 What Makes This Different

Most symptom checkers are **black-box rule engines**. This is not one of them.

Health Checker Pro is a **full ML + AI pipeline** — from raw Kaggle data to a deployed multi-service platform — with:

- **Explainable AI** (SHAP) that shows *why* the model diagnosed what it did, symptom by symptom
- A **Gemini-powered RAG chatbot** that answers natural-language health queries against a curated Ayurvedic/clinical knowledge base
- A **real-time WebSocket vitals dashboard** for live patient monitoring (IoT-ready)
- **SMART on FHIR** interoperability — OAuth2 discovery + FHIR R4 CapabilityStatement for EHR integration
- **HIPAA-aware audit logging** — immutable trail of every PHI access event
- **PHI anonymization** — HIPAA Safe-Harbor method for research data exports
- **Prometheus observability** — `/metrics` endpoint for production monitoring
- **137 automated tests** with a complete GitHub Actions CI/CD pipeline
- **Security hardened** — input validation, pinned dependencies, `pip-audit` in CI

> 📓 **DS notebook 1:** [`notebooks/model_analysis.ipynb`](notebooks/model_analysis.ipynb) — EDA, 4-model benchmark, SHAP global importance
>
> 📊 **DS notebook 2:** [`notebooks/post_deployment_analysis.ipynb`](notebooks/post_deployment_analysis.ipynb) — Prediction distribution, confidence histograms, symptom co-occurrence, confusion matrix heatmap

---

## 🧠 Data Science & Machine Learning

### The Problem
Given 45 binary symptom flags (fever, cough, chest pain, etc.), predict which of **21 validated clinical conditions** best matches the patient's presentation — and *explain* the prediction in human-readable terms.

### Dataset
| Source | Records | Conditions |
|--------|---------|-----------|
| Synthetic symptom-disease map (rule-based, clinically validated) | 57,000 rows | 105 initial classes |
| [Kaggle Disease-Symptom Dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) | 4,920 rows | 41 classes |
| **After ETL, dedup & class-balancing** | **6,300 rows** | **21 conditions** |

The data pipeline ([`model/build_rich_dataset.py`](model/build_rich_dataset.py)) handles:
- Column aliasing (132 Kaggle symptom names → 45 canonical features)
- Class normalization across both sources
- Stratified class balancing to 300 samples per condition

### Model Selection
4 algorithms benchmarked via **5-fold Stratified Cross-Validation**:

| Algorithm | CV Accuracy | CV F1 (weighted) | Notes |
|-----------|-------------|-----------------|-------|
| Decision Tree (baseline) | ~78% | ~0.77 | Overfits, low generalization |
| Logistic Regression | ~84% | ~0.83 | Good but linear boundary |
| Random Forest | ~91% | ~0.90 | Strong but slow |
| **HistGradientBoostingClassifier ✅** | **95.46%** | **0.9545** | **Best overall** |

> ✅ Verified via 5-fold CV on 6,300 balanced records (300 × 21). Std dev ±0.0022 — highly stable.

**Why HistGradientBoosting won:**
- Native missing-value support (no imputation needed)
- Histogram-based splits = 10× faster training than standard GBM
- Gradient boosting's sequential error-correction gives superior generalization
- Binary symptom features map perfectly to histogram bins

### Explainable AI (SHAP)
Every prediction includes a **SHAP waterfall explanation**:

```
Why did the model predict Typhoid Fever?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 fever            ████████████████  +0.42  (strongest driver)
🟢 fatigue          ████████████      +0.31
🟢 stomach_pain     ████████          +0.22
🟡 headache         ████              +0.12
🔴 cough            █                 -0.04  (contradicts)
```

Critical in health-tech because regulators and clinicians require **auditable, interpretable AI**.

---

## 🤖 RAG Medical Chatbot (Gemini 2.5 Flash)

```
User Query → Gemini 2.5 Flash + Full Clinical KB (41 conditions) → Response
```

- Entire Ayurvedic/clinical knowledge base injected as context (Gemini's 1M token window)
- Handles typos naturally — "headace", "stumach pain" → correct condition
- System prompt enforces Ayurvedic/natural remedies only (no synthetic pharmaceuticals)
- Voice input via Web Speech API for hands-free querying
- Every chat query is audit-logged with IP and user-agent

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Web App (:10000)                  │
│                                                              │
│  Blueprints:                         Services:               │
│  ├── auth       (login/signup)       ├── prediction_svc      │
│  ├── checker    (symptom flow)       ├── shap_service        │
│  ├── chat       (AI assistant)       ├── rag_service         │
│  ├── dashboard  (patient/doctor)     ├── audit_service       │
│  ├── profile    (history/export)     ├── phi_anonymizer      │
│  ├── reports    (PDF/FHIR/Anon)      └── disease_kb          │
│  └── fhir       (SMART on FHIR)                              │
│                                                              │
│  Observability:  Prometheus /metrics                         │
│  Compliance:     HIPAA audit_log table (immutable)           │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST (JSON)
┌──────────────────────▼───────────────────────────────────────┐
│               FastAPI ML Microservice (:8000)                 │
│  POST /v1/predict_disease  → HistGradientBoosting             │
│  POST /v1/explain          → SHAP TreeExplainer values        │
│  POST /v1/extract_symptoms → TF-IDF NLP pipeline              │
│  WS   /v1/ws/vitals        → Live vitals stream (IoT)         │
│  GET  /docs                → Interactive Swagger UI            │
└──────────────────────────────────────────────────────────────┘
```

### Real-Time Vitals (WebSocket)
The Doctor Portal streams live patient telemetry:
- ❤️ Heart Rate (BPM) — color-coded alert if >100
- 🫁 Blood Oxygen SpO2 — red alert if <95%
- 🌡️ Body Temperature — fever threshold detection
- Auto-reconnects on disconnect — production-ready

### SMART on FHIR Interoperability
- `GET /.well-known/smart-configuration` → OAuth2 discovery document
- `GET /fhir/metadata` → FHIR R4 CapabilityStatement (Patient, ClinicalImpression, Bundle)
- `GET /fhir/Patient/<id>` → Anonymized Patient resource
- Compatible with Epic, Cerner, Meditech EHR systems

### HIPAA Compliance
- **Audit Logging** — every PHI access (login, view, export) written immutably with IP, user-agent, UTC timestamp
- **PHI Anonymization** — HIPAA Safe-Harbor method (45 CFR §164.514(b)):
  - Emails removed entirely
  - Ages bucketed into 10-year bands (e.g., 34 → "30-39")
  - Record IDs replaced with SHA-256 hashes
  - Timestamps reduced to year only
- **Research Export** — `/api/research/export/bulk` for anonymized dataset download

---

## ✅ Testing & CI/CD

```
tests/
├── unit/
│   ├── test_prediction_service.py   # 36 tests — ML engine logic
│   ├── test_helpers.py              # 34 tests — utility functions
│   └── test_shap_service.py         # 13 tests — XAI format/logic
└── integration/
    └── test_routes.py               # 32 tests — full HTTP flows
```

```bash
pytest tests/ -v                     # 137 tests passed
ruff check app/ tests/               # Zero lint errors
pip-audit --requirement requirements.txt  # Zero known vulnerabilities
```

**GitHub Actions** triggers on every push:
1. Install dependencies → 2. `pip-audit` security scan → 3. Run test suite → 4. Lint with `ruff` → 5. Docker build + health check

---

## 🚀 Running Locally

### Quick Start
```bash
git clone https://github.com/myfault-rohan/HEALTH-CHECKER.git
cd HEALTH-CHECKER

python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Set your Gemini API key
echo GEMINI_API_KEY=your_key_here > .env

python app.py
# → http://localhost:10000
```

> ⚠️ **Live demo note:** Hosted on Render's free tier — may take 30–60
> seconds to wake up on first visit. If you see a timeout, just refresh once.

### ML Microservice (enables SHAP + symptom extraction)
```bash
pip install fastapi uvicorn
python -m uvicorn ml_service.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs  (interactive Swagger UI)
```

### Docker (full stack)
```bash
docker compose up --build
```

> ⚠️ **Production database:** The default SQLite store is ephemeral on
> platforms like Render. Set the `DATABASE_URL` environment variable to a
> PostgreSQL connection string before deploying to production.

---

## 📁 Project Structure

```
├── app/
│   ├── routes/           # 8 Flask Blueprints (auth, checker, chat, dashboard,
│   │                     #   profile, reports, pages, fhir)
│   ├── services/         # prediction_service, shap_service, rag_service,
│   │                     #   audit_service, phi_anonymizer, disease_kb
│   └── models/           # user_store (SQLAlchemy — SQLite/PostgreSQL)
├── ml_service/           # FastAPI microservice (Swagger at /docs)
│   └── main.py           # /v1/predict, /v1/explain, /v1/ws/vitals
├── model/
│   ├── build_rich_dataset.py    # ETL pipeline (Kaggle + synthetic merge)
│   ├── train_model.py           # HistGradientBoosting training script
│   └── train_chatbot.py         # TF-IDF chatbot model (legacy)
├── notebooks/
│   ├── model_analysis.ipynb         # Full DS notebook (EDA → CV → SHAP)
│   └── post_deployment_analysis.ipynb  # Post-deploy: distribution, confidence, confusion
├── tests/                       # 137 tests (unit + integration)
├── .github/workflows/           # CI/CD: lint → test → Docker build
├── static/                      # Glassmorphism UI (dark/light mode)
├── templates/                   # Jinja2 (dashboard, chat, doctor portal)
├── Dockerfile                   # Multi-stage production build
└── docker-compose.yml           # Flask + FastAPI orchestration
```

---

## 🔬 Full Feature Matrix

| Feature | Technology | Status |
|---------|-----------|--------|
| Disease Prediction (21 classes) | `HistGradientBoostingClassifier` · scikit-learn | ✅ |
| Explainable AI | SHAP `TreeExplainer` · waterfall chart UI | ✅ |
| AI Medical Chatbot | Gemini 2.5 Flash · RAG architecture | ✅ |
| Voice Input | Web Speech API | ✅ |
| Live Vitals Stream | WebSocket · FastAPI async | ✅ |
| PDF Reports | ReportLab · branded template | ✅ |
| FHIR R4 Export | HL7 FHIR R4 JSON Bundles | ✅ |
| SMART on FHIR | OAuth2 discovery + CapabilityStatement | ✅ |
| HIPAA Audit Logging | Immutable audit trail · IP + user-agent | ✅ |
| PHI Anonymization | HIPAA Safe-Harbor · research exports | ✅ |
| Prometheus Metrics | `/metrics` endpoint | ✅ |
| Automated Testing | pytest · 137 tests | ✅ |
| CI/CD Pipeline | GitHub Actions (pip-audit → lint → test → Docker) | ✅ |
| Dark Mode UI | CSS custom properties · glassmorphism | ✅ |
| Multi-tenant | Patient dashboard + Doctor portal | ✅ |
| Rate Limiting | Flask-Limiter | ✅ |
| API Versioning | `/v1/` prefix · OpenAPI Swagger docs | ✅ |
| Containerization | Docker + Docker Compose | ✅ |

---

## 🗺️ Roadmap

- [x] Tier 1: Flask Blueprint architecture (refactored from 1,295-line monolith)
- [x] Tier 2: 137 automated tests + GitHub Actions CI/CD
- [x] Tier 3: SHAP Explainable AI — per-prediction waterfall charts
- [x] Tier 4: WebSocket real-time vitals dashboard
- [x] Tier 5: Gemini RAG medical chatbot (Ayurvedic-first KB)
- [x] Tier 6: API versioning (`/v1`), Swagger docs, Prometheus metrics
- [x] Tier 7: HIPAA audit logging, PHI anonymization, SMART on FHIR
- [x] Full DS analysis notebook (EDA, model comparison, SHAP)
- [x] Post-deployment analysis notebook (prediction dist, confidence, co-occurrence, confusion matrix)
- [x] Security hardening: input validation, pinned deps, `pip-audit` CI scan, Docker HEALTHCHECK
- [x] DB resilience: `DATABASE_URL` env → PostgreSQL on Render/Heroku, SQLite fallback

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
