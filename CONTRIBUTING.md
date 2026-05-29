# Contributing to Health Checker Pro

Thank you for your interest in contributing! This guide covers everything you need to get started.

---

## 🛠️ Dev Environment Setup

```bash
git clone https://github.com/myfault-rohan/HEALTH-CHECKER.git
cd HEALTH-CHECKER

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install all dependencies (app + dev tools)
pip install -r requirements.txt -r requirements-dev.txt

# Copy the example env file and fill in your keys
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
# Edit .env: set GEMINI_API_KEY and FLASK_SECRET_KEY at minimum
```

---

## 🧪 Running the Test Suite

```bash
pytest tests/ -v
```

All 137 tests should pass. The SHAP tests require a trained `model/model.pkl` — if it's missing locally, generate a stub:

```bash
python - <<'EOF'
import pickle, os, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
os.makedirs("model", exist_ok=True)
X = np.random.randint(0, 2, (210, 45))
y = [f"Disease_{i}" for i in range(105)] * 2
m = HistGradientBoostingClassifier(max_iter=3, random_state=0)
m.fit(X, y)
with open("model/model.pkl", "wb") as f:
    pickle.dump(m, f)
EOF
```

---

## 🔍 Running the Linter

```bash
ruff check app/ tests/ predictor.py
```

Zero errors are required before submitting a PR. To auto-fix safe issues:

```bash
ruff check --fix app/ tests/ predictor.py
```

---

## 🔒 Security Audit

```bash
pip-audit --requirement requirements.txt
```

---

## 📬 PR Guidelines

1. **One feature or fix per PR** — keep PRs focused and reviewable.
2. **Tests are required** — every new behaviour must be covered by at least one test in `tests/`.
3. **Ruff must pass** — run `ruff check app/ tests/` and fix all errors before opening a PR.
4. **Descriptive commit messages** — use the `fix:`, `feat:`, `chore:`, `docs:` prefixes.
5. **No secrets in code** — use environment variables; never commit API keys or passwords.
6. **Update the README** if you're adding a user-visible feature.

---

## 📄 Licence

This project is released under the **MIT Licence** — see [LICENSE](LICENSE) for full terms.
You are free to use, modify, and distribute this software with attribution.
