# Health Checker Pro

Health Checker Pro is a Flask-based symptom analysis platform that helps users log symptoms, review confidence-ranked condition matches, and follow precaution guidance in a modern healthcare-style interface.

## Live Website

- Render deployment: `https://your-render-app.onrender.com`

## Features

- Secure authentication with hashed passwords
- Multi-step symptom checker workflow
- Categorized symptom selection with search and dynamic selected list
- Confidence-based condition prediction cards
- Emergency signal detection and urgency labels
- Treatment guidance with precautions and lifestyle recommendations
- User dashboard with profile snapshot and recent checks
- Profile history view for past analyses
- Responsive Bootstrap 5 UI with medical-themed design
- Loading overlay, success/error flash messages, and animated interactions

## Technology Stack

- Python 3
- Flask
- SQLite
- HTML / Jinja templates
- Bootstrap 5
- Font Awesome
- Vanilla JavaScript
- Gunicorn (production server)

## Project Structure

```text
health-checker/
├── app.py
├── config.py
├── requirements.txt
├── Procfile
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   └── main.py
│   ├── services/
│   │   └── prediction_service.py
│   └── models/
│       └── user_store.py
├── templates/
├── static/
└── health_checker.db
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/myfault-rohan/HEALTH-CHECKER.git
   cd HEALTH-CHECKER
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app locally:
   ```bash
   python app.py
   ```
5. Open:
   - `http://127.0.0.1:10000`

## Deployment (Render)

1. Push this repository to GitHub.
2. Create a new Render Web Service from the repo.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Set environment variables:
   - `FLASK_SECRET_KEY` (strong random value)
   - `SESSION_COOKIE_SECURE=1` (for HTTPS production)

## Screenshots

Add screenshots in this section after deployment:

- Dashboard
- Symptom Selection
- Prediction Results
- Treatment Guidance

