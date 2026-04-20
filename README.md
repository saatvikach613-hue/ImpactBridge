# ImpactBridge: Volunteer Intelligence Platform

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-00758F?style=for-the-badge&logo=postgresql&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-E97627?style=for-the-badge&logo=Tableau&logoColor=white)
![ML](https://img.shields.io/badge/Machine_Learning-blue?style=for-the-badge&logo=scikitlearn&logoColor=white)

**Empowering U&I NGO with ML-Driven Operational Excellence**

---

## 🌟 The Impact Story

Before **ImpactBridge**, coordination at U&I Visakhapatnam was a manual mountain. One coordinator, 53 volunteers, and 106 kids were managed through a fragmentated system of WhatsApp messages and Google Sheets. 

**After ImpactBridge**, the coordinator opens a dashboard on Monday morning and sees exactly which 5 kids need attention, which 3 volunteers are likely to miss Sunday, and that the fund drive is 87% complete. The coordinator doesn't chase information anymore—**the information comes to them.**

---

## 🏗️ Project Architecture

ImpactBridge is a full-stack intelligence platform built to modernize NGO operations across three critical personas:

### 1. Coordinator Dashboard (Decision Support)
A command center with 7 data-integrated sections: Home, Alerts, KPIs, Analysis, Volunteers, Kids, and Funds. Every metric is derived from a live data pipeline.

### 2. Volunteer App (Mobile-First Logging)
A lightweight session logger that reduces administrative overhead. Volunteers can rate student performance in under 30 seconds (a **97% reduction** in logging time).

### 3. Donor Portal (Transparent Impact)
A public wishlist page featuring ML-predicted resource needs and real-time fund drive progress, providing donors with definitive proof of their impact.

---

## 📊 Technical Deep-Dive

### Data Engineering Stack
| Category | Tools |
|----------|-------|
| **Backend** | Python, FastAPI, SQLAlchemy, PostgreSQL |
| **Data Engineering** | dbt (5 models, 16 tests), SQL (CTEs, Window Functions) |
| **Machine Learning** | scikit-learn (Random Forest, Ridge Regression), SMOTE, joblib |
| **Automation** | APScheduler, SendGrid |
| **Frontend** | React, React Router, Recharts |

### Machine Learning Pipeline
We implemented two core models to drive proactive decision-making:
- **At-Risk Classifier (Random Forest + SMOTE)**: Predicts "struggling" kids 2 weeks before traditional methods. **AUC-ROC: 0.97.**
- **Progression Predictor (Ridge Regression)**: Projects literacy level growth 4 weeks into the future, automatically populating the donor wishlist.

### KPI Framework
| KPI | Target | Source |
|-----|--------|--------|
| **Student Progress Score** | ↑ Over Time | Session logs → dbt → ML |
| **Attendance Rate** | 80% (U&I Benchmark) | Session logs |
| **Volunteer Reliability** | ≥70% Threshold | RSVP + Session Logs |
| **Funding Sufficiency** | ≥85% | Fund drive data |

---

## ✅ Problems Solved & Results

- **Session Logging**: Time reduced from 15 mins to <30 seconds. **97% time reduction.**
- **Volunteer Management**: Replaced reactive chasing with automated Thursday RSVP reminders and Friday "unconfirmed" alerts.
- **Resource Procurement**: ML projects needs 4 weeks in advance, auto-generating **87 wishlist items** for proactive fundraising.
- **Early Warning**: Random Forest flags at-risk kids with plain-English reasons (e.g., "2 consecutive struggling sessions").

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL

### Setup
1. **Clone & Install**:
   ```bash
   git clone https://github.com/saatvikach613-hue/ImpactBridge.git
   cd ImpactBridge
   pip install -r requirements.txt
   cd ImpactBridge_Frontend && npm install
   ```
2. **Environment**: 
   Rename `.env.example` to `.env` and fill in your database credentials.
3. **Run**:
   ```bash
   # Backend
   uvicorn app.main:app --reload
   # Frontend
   npm run dev
   ```

---

## 🙏 Credits & Acknowledgments
Built for **U&I (You and I)**, India's largest volunteer-driven education NGO, based on their real 2024-25 operations.
