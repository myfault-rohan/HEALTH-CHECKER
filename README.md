# 🏥 Health Checker Pro

> A **production-grade, enterprise AI clinical diagnostic platform** — built to demonstrate end-to-end Data Science, ML Engineering, and full-stack health-tech capabilities.

[![CI Pipeline](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml/badge.svg)](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![scikit-learn](https://img.shields.io/badge/scikit--learn-HistGradientBoosting-orange?logo=scikitlearn)
![SHAP](https://img.shields.io/badge/XAI-SHAP-purple)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue?logo=google)
![FastAPI](https://img.shields.io/badge/ML%20Service-FastAPI-teal?logo=fastapi)
![Tests](https://img.shields.io/badge/Tests-111%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-72%25-yellow)

---

## 🎯 What Makes This Different

Most symptom checkers are **black-box rule engines**. This is not one of them.

Health Checker Pro is a **full ML + AI pipeline** — from raw Kaggle data to a deployed multi-service platform — with:
- **Explainable AI** (SHAP) that shows *why* the model diagnosed what it did, symptom by symptom
- A **Gemini-powered RAG chatbot** that answers natural-language health queries against a curated Ayurvedic/clinical knowledge base  
- A **real-time WebSocket vitals dashboard** for live patient monitoring (IoT-ready)
- A **FHIR R4 export** so predictions can be sent directly into hospital EHR systems (Epic, Cerner)
- **111 automated tests** with a complete GitHub Actions CI/CD pipeline

---

## 🧠 Data Science & Machine Learning

### The Problem
Given 45 binary symptom flags (fever, cough, chest pain, etc.), predict which of **21 validated clinical conditions** best matches the patient's presentation — and *explain* the prediction in human-readable terms.

### Dataset
| Source | Records | Conditions |
|--------|---------|-----------|
| Synthetic symptom-disease map (rule-based, clinically validated) | 57,000 rows | 105 initial classes |
| [Kaggle Disease-Symptom Dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) | 4,920 rows | 41 classes |
| **After ETL, dedup & class-balancing** | **~6,300 rows** | **21 conditions** |

The data pipeline ([`model/build_rich_dataset.py`](model/build_rich_dataset.py)) handles:
- Column aliasing (132 Kaggle symptom names → 45 canonical features)  
- Class normalization across both sources  
- Stratified class balancing to prevent majority-class dominance

### Model Selection
We compared 4 algorithms on a stratified hold-out using 5-fold cross-validation:

| Algorithm | CV Accuracy | CV F1 (weighted) | Notes |
|-----------|-------------|-----------------|-------|
| Decision Tree (baseline) | ~78% | ~0.77 | Overfits, low generalization |
| Logistic Regression | ~84% | ~0.83 | Good but linear boundary |
| Random Forest | ~91% | ~0.90 | Strong but slow |
| **HistGradientBoostingClassifier ✅** | **95.46%** | **0.9545** | **Best overall** |

> ✅ Numbers verified via 5-fold cross-validation on 6,300 balanced records (300 samples × 21 conditions). Std dev ±0.0022 — highly stable.

**Why HistGradientBoosting won:**
- Native missing-value support (no imputation needed)
- Histogram-based splits = 10× faster training than standard GBM
- `class_weight='balanced'` handles rare disease classes cleanly
- Gradient boosting's sequential error-correction gives superior generalization

### Explainable AI (SHAP)
After every prediction, the platform shows a **SHAP waterfall chart**:

```
Why did the model predict Typhoid Fever?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 fever            ████████████████  +0.42  (strongest driver)
🟢 fatigue          ████████████      +0.31
🟢 stomach_pain     ████████          +0.22
🟡 headache         ████              +0.12
🔴 cough            █                 -0.04  (contradicts)
```

This is critical in health-tech because regulators and clinicians require **auditable, interpretable AI** — not black-box outputs.

> 📓 Full analysis in [`analysis/model_analysis.ipynb`](analysis/model_analysis.ipynb) — EDA, confusion matrix, per-class precision/recall, SHAP global importance plots.

---

## 🤖 RAG Medical Chatbot

The AI assistant is built on a **Retrieval-Augmented Generation** architecture:

```
User Query → Gemini 2.5 Flash + Full Clinical KB (41 conditions) → Response
```

**Design decisions:**
- Entire Ayurvedic/clinical knowledge base injected as context (Gemini's 1M token window)  
- Bypasses brittle TF-IDF keyword matching — handles typos like "headace", "stumach pain" naturally  
- System prompt explicitly forbids synthetic pharmaceutical advice — Ayurvedic/natural remedies only  
- Voice input (Web Speech API) allows hands-free symptom querying

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Web App                        │
│                                                         │
│  Blueprints:                        Services:           │
│  ├── auth       (login/signup)      ├── prediction_svc  │
│  ├── checker    (symptom flow)      ├── shap_service    │
│  ├── chat       (AI assistant)      ├── rag_service     │
│  ├── dashboard  (patient/doctor)    └── disease_kb      │
│  ├── profile    (history/export)                        │
│  └── reports    (PDF / FHIR)                            │
└──────────────────────┬──────────────────────────────────┘
                       │ REST
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI ML Microservice (:8000)             │
│  POST /predict_disease  → HistGradientBoosting           │
│  POST /explain          → SHAP TreeExplainer values      │
│  POST /extract_symptoms → TF-IDF NLP pipeline            │
│  WS   /ws/vitals        → Live vitals stream (IoT)       │
└─────────────────────────────────────────────────────────┘
```

### Real-Time Vitals (WebSocket)
The Doctor Portal streams live patient telemetry via WebSocket:
- ❤️ Heart Rate (BPM) — color-coded alert if >100
- 🫁 Blood Oxygen SpO2 — red alert if <95%
- 🌡️ Body Temperature — fever threshold detection
- Auto-reconnects on disconnect — production-ready

### FHIR R4 EHR Export
Predictions export as valid **HL7 FHIR R4 Bundles** containing `Patient` and `ClinicalImpression` resources — compatible with Epic/Cerner integration workflows.

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
pytest tests/ --cov=app --cov-report=term-missing   # 111 tests, 72% coverage
ruff check app/ tests/                               # Zero lint errors
```

**GitHub Actions** triggers on every push to `main`:
1. Install dependencies
2. Run full test suite with coverage report
3. Lint with `ruff`
4. Docker build + container health check

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

### ML Microservice (enables symptom extraction + SHAP)
```bash
pip install fastapi uvicorn
python -m uvicorn ml_service.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs  (interactive Swagger UI)
```

### Docker (full stack)
```bash
docker compose up --build
```

---

## 📁 Project Structure

```
├── app/
│   ├── routes/           # 7 Flask Blueprints (auth, checker, chat, dashboard, profile, reports, pages)
│   ├── services/         # prediction_service, shap_service, rag_service, disease_kb
│   └── models/           # user_store (SQLAlchemy + SQLite/PostgreSQL)
├── ml_service/           # FastAPI microservice with WebSocket vitals endpoint
│   └── main.py           # predict_disease, explain, extract_symptoms, ws/vitals
├── model/
│   ├── build_rich_dataset.py    # ETL pipeline (Kaggle + synthetic merge)
│   ├── train_model.py           # HistGradientBoosting training + evaluation
│   └── dataset_rich.csv         # Merged, cleaned dataset (4,920 Kaggle + synthetic)
├── analysis/
│   └── model_analysis.ipynb    # Full DS notebook (EDA → Model comparison → SHAP)
├── tests/                # 111 tests (unit + integration)
├── .github/workflows/    # CI/CD: lint → test → Docker build
├── static/               # Glassmorphism UI (dark/light mode, animations)
├── templates/            # Jinja2 templates (dashboard, chat, doctor portal)
└── docker-compose.yml    # Flask app + ML microservice orchestration
```

---

## 🔬 Full Feature Matrix

| Feature | Technology | Status |
|---------|-----------|--------|
| Disease Prediction | `HistGradientBoostingClassifier` · scikit-learn | ✅ |
| Explainable AI | SHAP `TreeExplainer` · waterfall chart UI | ✅ |
| AI Medical Chatbot | Gemini 2.5 Flash · RAG architecture | ✅ |
| Voice Input | Web Speech API | ✅ |
| Live Vitals Stream | WebSocket · FastAPI async | ✅ |
| PDF Reports | ReportLab · custom branded template | ✅ |
| FHIR R4 Export | HL7 FHIR R4 JSON Bundles | ✅ |
| Automated Testing | pytest · 111 tests · 72% coverage | ✅ |
| CI/CD Pipeline | GitHub Actions (lint → test → Docker) | ✅ |
| Dark Mode UI | CSS custom properties · glassmorphism | ✅ |
| Multi-tenant | Patient dashboard + Doctor portal | ✅ |
| Rate Limiting | Flask-Limiter | ✅ |
| Containerization | Docker + Docker Compose | ✅ |

---

## 🗺️ Roadmap

- [x] Flask Blueprint architecture (refactored from 1,295-line monolith)
- [x] HistGradientBoosting ML model with SHAP Explainability
- [x] ETL data pipeline (Kaggle + synthetic data merge)
- [x] 111 automated tests + GitHub Actions CI/CD
- [x] Full DS analysis notebook (EDA, model comparison, SHAP)
- [x] Gemini RAG medical chatbot (Ayurvedic-first KB)
- [x] WebSocket real-time wearable vitals dashboard
- [x] FHIR R4 EHR export + branded PDF reports
- [x] Doctor portal with cross-patient monitoring
- [ ] Prometheus metrics + Grafana observability
- [ ] SMART on FHIR OAuth2 scope compliance
- [ ] HIPAA audit logging

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
