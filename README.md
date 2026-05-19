# 🏥 Health Checker Pro

> **An ML-powered clinical symptom analysis platform** with Explainable AI, automated testing, and production-grade architecture.

[![CI Pipeline](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml/badge.svg)](https://github.com/myfault-rohan/HEALTH-CHECKER/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-HistGradientBoosting-orange)
![SHAP](https://img.shields.io/badge/XAI-SHAP-purple)
![Tests](https://img.shields.io/badge/Tests-111%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-72%25-yellow)

---

## 📌 What This Project Does

Health Checker Pro lets users enter symptoms and receive ranked disease predictions from a machine learning model, with **per-symptom explanations** of why the model made each prediction.

**Key differentiator:** Most symptom checkers are black-box rule engines. This one uses `HistGradientBoostingClassifier` trained on 57,000 symptom-disease records, with **SHAP (SHapley Additive exPlanations)** to make every prediction transparent and auditable.

---

## 🧠 Data Science & ML

### Model
| Attribute | Detail |
|-----------|--------|
| Algorithm | `HistGradientBoostingClassifier` |
| Dataset | 57,000 synthetic records · 105 disease classes · 45 binary symptom features |
| Explainability | SHAP `TreeExplainer` — per-feature attribution per prediction |

### Why HistGradientBoosting?
We evaluated 4 algorithms on a stratified 8k sample using 3-fold cross-validation:

| Model | CV Accuracy | CV F1 (weighted) |
|-------|-------------|------------------|
| Decision Tree (baseline) | lowest | lowest |
| Logistic Regression | moderate | moderate |
| Random Forest | high | high |
| **HistGradientBoosting ✅** | **highest** | **highest** |

**Additional advantages:** native missing-value handling, `class_weight='balanced'` for skewed classes, histogram-based splits for fast training.

> 📊 Full analysis with charts, confusion matrix, SHAP global importance, and business insights in [`analysis/model_analysis.ipynb`](analysis/model_analysis.ipynb)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│            Flask Web App                │
│                                         │
│  Blueprints:                            │
│  ├── auth       (login / signup)        │
│  ├── checker    (symptom workflow)      │
│  ├── dashboard  (patient / doctor)      │
│  ├── profile    (history / CSV export)  │
│  ├── reports    (PDF / FHIR export)     │
│  └── pages      (landing / about)       │
│                                         │
│  Services:                              │
│  ├── prediction_service.py              │
│  ├── shap_service.py  ← XAI            │
│  └── chatbot_service.py                 │
└────────────────┬────────────────────────┘
                 │ HTTP
┌────────────────▼────────────────────────┐
│         FastAPI ML Microservice         │
│  POST /predict_disease  (inference)     │
│  POST /explain          (SHAP values)   │
│  POST /extract_symptoms (NLP)           │
└─────────────────────────────────────────┘
```

### Explainable AI (SHAP) — on the Conditions page

After every prediction, the app shows a waterfall chart:
- 🟢 **Green bars** — symptoms that pushed the model *toward* this diagnosis
- 🔴 **Red bars** — symptoms that pushed *away* from it
- `●` dot marks symptoms the patient actually reported

---

## ✅ Testing & CI/CD

```
tests/
├── unit/
│   ├── test_prediction_service.py   # 36 tests — ML engine
│   ├── test_helpers.py              # 34 tests — utilities
│   └── test_shap_service.py        # 13 tests — SHAP format & logic
└── integration/
    └── test_routes.py               # 32 tests — HTTP flows
```

```bash
# Run fast tests
pytest tests/ -m "not slow"

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Lint
ruff check app/ tests/
```

**GitHub Actions** runs on every push to `main`: lint → test → Docker build + container health check.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Docker (optional, for ML microservice)

### 1. Flask App

```bash
git clone https://github.com/myfault-rohan/HEALTH-CHECKER.git
cd HEALTH-CHECKER

python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

python run.py
# → http://localhost:5000
```

### 2. ML Microservice (optional — app works without it)

```bash
cd ml_service
pip install -r requirements.txt

# Train models first (run once)
python ../model/train_model.py
python ../model/train_chatbot.py

uvicorn main:app --port 8000
```

### 3. Docker

```bash
docker build -t health-checker-pro .
docker run -p 10000:10000 health-checker-pro
```

---

## 📁 Project Structure

```
├── app/
│   ├── routes/          # Flask Blueprints (auth, checker, dashboard, ...)
│   ├── services/        # prediction_service, shap_service, chatbot_service
│   └── models/          # user_store (JSON persistence)
├── ml_service/          # FastAPI microservice (Dockerized)
├── model/               # Training scripts (train_model.py, build_dataset.py)
├── analysis/            # 📊 DS analysis notebook (EDA, model comparison, SHAP)
├── tests/               # pytest unit + integration tests
├── templates/           # Jinja2 HTML templates
├── static/              # CSS + JS
├── .github/workflows/   # CI/CD pipeline
├── pyproject.toml       # pytest + ruff config
└── Dockerfile
```

---

## 🔬 Feature Summary

| Feature | Technology |
|---------|-----------|
| ML Prediction | `HistGradientBoostingClassifier` · scikit-learn |
| Explainable AI | SHAP `TreeExplainer` · waterfall visualization |
| NLP Symptom Extraction | TF-IDF pipeline · chatbot interface |
| PDF Reports | ReportLab |
| FHIR Export | HL7 FHIR R4 JSON |
| Rate Limiting | Flask-Limiter |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Testing | pytest · pytest-cov · ruff |

---

## 📊 Data Science Notebook

[`analysis/model_analysis.ipynb`](analysis/model_analysis.ipynb) covers:

1. **EDA** — class distribution, symptom prevalence, correlation heatmap
2. **Model selection** — 4-algorithm comparison with documented reasoning
3. **Production evaluation** — confusion matrix, per-class precision/recall/F1
4. **SHAP global importance** — which symptoms drive predictions across all 105 classes
5. **SHAP waterfall** — single-prediction explanation with colour-coded bars
6. **Clinical insights** — symptom co-occurrence, body-system category analysis

> 📊 **Dataset:** Hybrid — 57k synthetically generated samples (rule-based from clinical symptom maps) enriched with the [Kaggle Disease Symptom Dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) (4,920 real-world-pattern rows, 41 disease classes). Cleaned, normalised, and class-balanced to 6,300 training samples across 21 clinically validated conditions.

---

## 🗺️ Roadmap

- [x] Flask Blueprint architecture (6 modules from 1,295-line monolith)
- [x] ML prediction with HistGradientBoosting
- [x] SHAP Explainability (XAI)
- [x] 111 automated tests + CI/CD pipeline
- [x] Data science analysis notebook
- [ ] RAG-based medical chatbot (LLM + retrieval)
- [ ] Real-time wearable vitals (WebSocket)
- [ ] SMART on FHIR compliance

---

## 📄 License

MIT License
