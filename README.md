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

## Why I built this

I volunteer with U&I, India's largest volunteer-driven education NGO, at the Visakhapatnam chapter. Nobody assigned me this project. I noticed our coordinator was managing 53 volunteers and 106 kids almost entirely through WhatsApp messages and Google Sheets, and spending more time chasing information than actually helping kids. That gap, between how much a coordinator cared and how little the tools around them helped, is what I set out to close.

---

## The problem

Before ImpactBridge, running a single Sunday session at the Visakhapatnam chapter meant:

- The coordinator manually sending 5 or more WhatsApp messages every Friday and Saturday just to confirm who was showing up.
- Session sheets that were only completed about 70% of the time, because logging a single kid's progress took real effort in the middle of a busy session.
- Resource procurement that was entirely reactive: books and materials got requested only after someone noticed a shortage, not before.
- No early signal on which kids were falling behind until it was already a visible problem, because nobody had time to review 106 kids' worth of scattered notes every week.

None of this was anyone's fault. It's what happens when a fast-growing volunteer program runs entirely on manual coordination. The problem wasn't the people, it was the absence of a system.

## Ideas I considered

Before settling on a custom build, I weighed a few lighter options:

- **A shared spreadsheet with better structure.** This would have helped organize data, but it still relies on someone manually opening it, updating it, and remembering to check it. It doesn't solve the "coordinator has to go looking for information" problem.
- **A simple WhatsApp bot for reminders.** This solves the RSVP chasing piece, but does nothing for the harder problem: knowing which kids are quietly falling behind before it becomes obvious.
- **An off-the-shelf CRM or volunteer management tool.** Most of these are built for donor management, not for a coordinator who needs predictive, kid-level insight and a session logger volunteers will actually use in under a minute.

I decided the real unlock was combining fast data capture (so volunteers would actually use it) with a prediction layer on top (so the coordinator gets ahead of problems instead of reacting to them), which none of the lighter options could do on their own. That's what pushed this from "automate a reminder" into a full data platform.

## The solution

ImpactBridge is a full-stack intelligence platform built around three personas, each with a different problem to solve:

### 1. Coordinator Dashboard (Decision Support)
A command center with 7 data-integrated sections: Home, Alerts, KPIs, Analysis, Volunteers, Kids, and Funds. Every metric is derived from a live data pipeline, not a manually updated sheet.

### 2. Volunteer App (Mobile-First Logging)
A lightweight session logger that reduces administrative overhead. Volunteers can rate student performance in under 30 seconds, a **97% reduction** in logging time compared to the old process.

### 3. Donor Portal (Transparent Impact)
A public wishlist page featuring ML-predicted resource needs and real-time fund drive progress, giving donors concrete proof of their impact instead of a generic ask.

---

## The automation flow

The system runs on a weekly cycle, so the coordinator never has to remember to check anything, the information comes to them on a schedule.

```mermaid
flowchart TD
    A[Sunday session happens] --> B[Volunteer logs session\nin under 30 seconds]
    B --> C[(PostgreSQL)]
    C --> D[dbt: staging models]
    D --> E[dbt: intermediate model\nint_kid_features]
    E --> F[dbt: marts\nat-risk kids + resource demand]

    F --> G[Sunday 11pm\nML pipeline runs]
    G --> G1[Risk model\nRandom Forest + SMOTE]
    G --> G2[Progress model\nRidge Regression]
    G --> G3[Demand forecast\npopulates wishlist]

    G1 --> H[Monday 7am\nAt-risk digest emailed\nto coordinators]
    G3 --> I[Donor Portal\nwishlist updated]

    J[Thursday 8pm\nRSVP reminders sent\nto volunteers] --> K{Volunteer\nconfirms?}
    K -- No response by Friday --> L[Friday 8am\nCoordinator alerted\nto unconfirmed volunteers]
    K -- Confirms --> A

    I --> M[Donor funds an item]
    M --> N[Item used in session]
    N --> O[Donor gets automatic\nimpact card]

    X[GitHub Actions cron\nUTC schedule] -. X-Automation-Key .-> Y[/automation/trigger/*]
    Y --> J
    Y --> L
    Y --> G
    Y --> H
    G & H & J & L --> Z[(automation_runs +\nautomation_logs)]
    Z --> W[Dashboard → Automation tab\nhealth · adoption · audit log]
```

Four scheduled jobs run this cycle without anyone touching a spreadsheet: RSVP reminders (Thursday), unconfirmed volunteer alerts (Friday), the full ML pipeline (Sunday night), and the at-risk digest (Monday morning). A fifth, the donor impact card, fires on demand the moment a funded item is actually used in a session, closing the loop between a donation and its real-world effect.

Every job is fired two ways on purpose: by the in-process APScheduler while the API is awake, and by a GitHub Actions cron that calls the same trigger endpoints with a shared key, so a sleeping free-tier dyno can't silently skip Thursday's reminders. Each run writes a row to `automation_runs`, and each email writes a row to `automation_logs`, which is what the dashboard's Automation tab reads.

### Making the automation observable

The **Automation** tab in the coordinator dashboard answers the three questions an operations reviewer actually asks:

| Question | Where it's answered | Source |
|----------|---------------------|--------|
| Did each job run, and did it succeed? | Job health table: last run, outcome, one-line summary, 30-day success rate, "Run now" | `automation_runs` via `GET /automation/health` |
| Is anyone using it, and did it help? | Adoption cards: session-log completion vs the 70% baseline, RSVP response rate, estimated volunteer hours saved, coordinator messages avoided | `GET /dashboard/adoption` |
| What exactly went out, to whom? | Audit log of every automated email with status | `automation_logs` via `GET /automation/logs` |

### One-tap RSVP (the loop that was missing)

The Thursday email links to `/rsvp/{session}/{volunteer}?token=…`. The token is an HMAC bound to that exact session and volunteer, so a forwarded link can't confirm on someone else's behalf, and no login is needed. Tapping *Confirm* or *Can't make it* hits `POST /sessions/{id}/rsvp/{volunteer}/respond`, which verifies the token, rejects past sessions, and is idempotent.

### Plain-English Monday digest (optional LLM)

If `ANTHROPIC_API_KEY` is set, the at-risk digest opens with a 4–7 sentence briefing that groups kids by shared reason ("three kids missed two sessions in a row") and says who to check on first. The model only rephrases facts the ML pipeline already produced; the prompt forbids advice, diagnoses, and speculation. If the key is missing, the call fails, or the output drops a kid's name, the email falls back to the plain list. The email always goes out.

---

## Technical deep-dive

### Data engineering stack
| Category | Tools |
|----------|-------|
| **Backend** | Python, FastAPI, SQLAlchemy, PostgreSQL |
| **Data Engineering** | dbt (5 models, 16 tests), SQL (CTEs, Window Functions) |
| **Machine Learning** | scikit-learn (Random Forest, Ridge Regression), SMOTE, joblib |
| **Automation** | APScheduler (in-process) + GitHub Actions cron (external), SendGrid, HMAC-signed one-tap links |
| **Observability** | `automation_runs` / `automation_logs` tables, Automation tab (health, adoption, audit log) |
| **LLM (optional)** | Anthropic Claude Haiku for the Monday briefing, deterministic fallback |
| **Tests** | pytest (token signing, adoption metrics, digest guardrails), dbt tests |
| **Frontend** | React, React Router, Recharts |

### Machine learning pipeline
Two core models drive proactive decision-making:
- **At-Risk Classifier (Random Forest + SMOTE)**: Predicts "struggling" kids 2 weeks before traditional methods would catch it. **AUC-ROC: 0.97.**
- **Progression Predictor (Ridge Regression)**: Projects literacy level growth 4 weeks into the future, automatically populating the donor wishlist so procurement becomes predictive instead of reactive.

### KPI framework
| KPI | Target | Source |
|-----|--------|--------|
| **Student Progress Score** | ↑ Over Time | Session logs → dbt → ML |
| **Attendance Rate** | 80% (U&I Benchmark) | Session logs |
| **Volunteer Reliability** | ≥70% Threshold | RSVP + Session Logs |
| **Funding Sufficiency** | ≥85% | Fund drive data |

---

## What changed along the way

This wasn't built in one pass. A few real decisions and course corrections shaped the final system:

- **Schema first, features second.** I started by designing the PostgreSQL schema and seeding realistic data (Phase 1) before writing a single line of ML code, because a prediction layer built on a shaky data model isn't worth trusting.
- **Deployment forced a real fix, not a workaround.** After the initial release, moving to Railway's managed PostgreSQL broke the app's database connection handling. Rather than patch around it, I went back and fixed the `DATABASE_URL` configuration properly so the app would reconnect reliably in production, not just in local development.
- **dbt as the trust layer, not an afterthought.** Early on, features for the ML models were closer to raw SQL queries scattered across the codebase. I consolidated that logic into a proper dbt layer, staging models, an intermediate feature model, and marts, with 16 tests, specifically so a wrong number could be caught before it reached a coordinator's dashboard.
- **The audit log wasn't actually logging.** `email_service.py` and `/automation/logs` were written against an `AutomationLog` table that was never defined, and the write was wrapped in a bare `except: pass`, so every email "logged" silently went nowhere. I defined the model, added `AutomationRun` for job-level tracking, and built the Automation tab on top so the gap can't hide again.
- **The RSVP link went to a page that didn't exist.** Emails linked to `/rsvp/...` with a "Phase 5" comment. I built the page, the signed-token endpoint behind it, and tests for the token so the most visible step of the automation actually closes.
- **Scheduler reliability on free tiers.** An in-process scheduler only fires while the dyno is awake. Rather than pay for an always-on host, I added a GitHub Actions cron that wakes the API and calls the same trigger endpoints with a shared key, and recorded `triggered_by` on every run so the dashboard shows which path fired.
- **Frontend was unbuildable from the repo.** `package.json` was never committed, `Public/` was capitalised (fine on macOS, fatal on Linux build servers), and API calls were relative paths that 404 in production. Fixed all three, and the build now passes under `CI=true`, which is what Vercel uses.
- **Measure adoption, not just uptime.** Added `/dashboard/adoption` so the platform reports session-log completion against the pre-ImpactBridge 70% baseline and RSVP response rates, with estimates clearly labelled as estimates.

---

## Problems solved and results

- **Session Logging**: Time reduced from 15 minutes to under 30 seconds, a **97% reduction**.
- **Volunteer Management**: Replaced reactive WhatsApp chasing with automated Thursday RSVP reminders and Friday "unconfirmed" alerts.
- **Resource Procurement**: ML projects needs 4 weeks in advance, auto-generating **87 wishlist items** for proactive fundraising instead of reactive purchasing.
- **Early Warning**: The Random Forest model flags at-risk kids with plain-English reasons (for example, "2 consecutive struggling sessions"), not just a raw score.

---

## Getting started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL

### Setup
1. **Clone & Install**:
```bash
   git clone https://github.com/saatvika-chokkapu/ImpactBridge.git
   cd ImpactBridge
   pip install -r requirements.txt
   cd ImpactBridge_Frontend && npm install
```
2. **Environment**:
   Rename `.env.example` to `.env` and fill in your database credentials.
3. **Run**:
```bash
   # Backend (http://localhost:8000, docs at /docs)
   uvicorn app.main:app --reload
   # Frontend (http://localhost:3000, proxies API calls to :8000)
   cd ImpactBridge_Frontend && npm start
```
4. **Tests** (no database needed):
```bash
   pytest -q tests
```

### Deploying

| Piece | Where | What to set |
|-------|-------|-------------|
| Backend | Railway / Render (Procfile included, Python 3.11) | `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL`, `AUTOMATION_API_KEY`, optional `SENDGRID_API_KEY`, optional `ANTHROPIC_API_KEY` |
| Frontend | Vercel, root directory `ImpactBridge_Frontend` | `REACT_APP_API_URL` = backend URL (no trailing slash) |
| Scheduler | GitHub Actions (already in `.github/workflows/automation.yml`) | repo secrets `BACKEND_URL`, `AUTOMATION_API_KEY` |

`FRONTEND_URL` on the backend and the Vercel project URL must match, since every email link is built from it and CORS is scoped to it.

---

## Credits & acknowledgments
Built for **U&I (You and I)**, India's largest volunteer-driven education NGO, based on their real 2024-25 operations.
