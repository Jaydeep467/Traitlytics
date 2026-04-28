No worries bro! Here's the README — create README.md in the root of the traitlytics folder:
markdown# 🧠 Traitlytics — Personality Analytics Platform

> Big Five (OCEAN) personality analytics platform with ML-powered trait scoring, population percentile rankings, longitudinal drift detection, and exportable PDF reports.

![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React_18-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)

---

## Architecture
50-item IPIP Big Five Questionnaire
↓
Response Validation (IsolationForest)
↓
Reverse Scoring Pipeline
↓
StandardScaler Normalization (0-100)
↓
Population Percentile (scipy CDF vs IPIP norms)
↓
Trait Drift Detection (longitudinal)
↓
PostgreSQL Storage (compound indexes)
↓
Flask REST API + JWT Auth
↓
React Dashboard (Radar, Line, Doughnut charts)

PDF Report Export (ReportLab)


---

## Key Features

| Feature | Implementation |
|---|---|
| Big Five OCEAN scoring | 50-item IPIP questionnaire, reverse scoring |
| ML pipeline | StandardScaler normalization, IsolationForest validation |
| Population percentiles | scipy.stats.norm.cdf vs Goldberg et al. norms |
| Trait drift detection | Longitudinal tracking across multiple assessments |
| Role-based access | Individual vs Manager cohort views |
| PDF export | Professional ReportLab report |
| 210 demo profiles | Realistic Indian user profiles, 9 personality archetypes |
| 32 tests | Pipeline, validation, reverse scoring, percentiles, API |

---

## Quickstart

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Create DB
psql -U postgres
CREATE USER tl_user WITH PASSWORD 'tl_pass';
CREATE DATABASE traitlytics OWNER tl_user;
GRANT ALL PRIVILEGES ON DATABASE traitlytics TO tl_user;

# Seed demo data
python seed_demo.py

# Run backend
python -m app.main

# Frontend
cd frontend
npm install
npm run dev
```

---

## API Reference
POST /api/v1/auth/register          Register user
POST /api/v1/auth/login             Login
GET  /api/v1/assessment/questions   Get 50 questions
POST /api/v1/assessment/submit      Submit responses → ML scoring
GET  /api/v1/profile                Get latest trait profile
GET  /api/v1/profile/history        Trait history + drift detection
GET  /api/v1/profile/export/pdf     Download PDF report
GET  /api/v1/analytics/population   Population distribution
GET  /api/v1/analytics/dominant-traits  Dominant trait breakdown
GET  /api/v1/analytics/cohort       Cohort comparison (manager only)
POST /api/v1/demo/seed              Seed historical data

---

## ML Pipeline Details

```python
# 1. Response validation
IsolationForest(contamination=0.05)  # flags gaming/random responses

# 2. Reverse scoring
score = 6 - score  # for negatively-keyed items

# 3. Normalization
StandardScaler → 0-100 scale

# 4. Population percentile
from scipy import stats
z   = (score - population_mean) / population_std
pct = stats.norm.cdf(z) * 100  # vs Goldberg et al. IPIP norms

# 5. Drift detection
delta = last_score - first_score
if delta > 10: drift = "increasing"
```

## Scrrenshots

<img width="1920" height="1080" alt="Screenshot 2026-04-28 112938" src="https://github.com/user-attachments/assets/d900ab31-2f35-4393-9230-e7e117b1414b" />

---

## Running Tests

```bash
cd backend
pytest tests/ -v
# 32 passed ✅
```

---

## Tech Stack

`Python` · `Flask` · `Scikit-learn` · `scipy` · `PostgreSQL` · `SQLAlchemy` · `React 18` · `Chart.js` · `ReportLab` · `JWT` · `bcrypt` · `Docker`
