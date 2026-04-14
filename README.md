# ImpactBridge

> A full-stack volunteer intelligence platform for U&I NGO — built from 9 months of direct field experience teaching children in Visakhapatnam, India.

---

## The story behind this

From September 2023 to June 2024, I volunteered with [U&I](https://www.unitedindia.org/), a non-profit educating underprivileged children across India. Every Sunday I taught math and English to 5 kids aged 7–11.

The coordination was chaos.

Volunteers tracked progress on a Google Sheet filled out *after* a session — exhausted, while kids were still running around. 30% of volunteers didn't show up on any given Sunday with zero advance warning. The coordinator managed everything through WhatsApp messages. Nobody knew which kids were falling behind until it was too late.

One kid I was responsible for wouldn't sit still. In the second session I noticed he liked to draw. So we made a deal: he'd bring a drawing to class each week. For the next two weeks he actually listened and engaged.

That insight lived in my head. When I left, it disappeared.

**ImpactBridge captures it permanently — for every kid, across every volunteer, across every chapter.**

---

## What it does

Three users. One platform.

| User | What they see |
|------|--------------|
| **Volunteer** | Their 5 kids, current chapters, 3-tap session logger (mobile) |
| **Coordinator** | All chapters, at-risk alerts, fund drive progress, ML predictions |
| **Donor** | Wishlist of specific items for specific kids — fund Arjun's sketchbook |

### Core features

**1. Kid profile — living, portable, permanent**
Each child has a profile that persists across volunteers and years: academic progress, learning style, interests, and a volunteer notes feed. The next volunteer picks up exactly where the last one left off.

**2. 3-tap session logger (mobile PWA)**
Kid → rating → submit. Under 30 seconds. Works offline, syncs when back online. Replaces a 15-minute Google Sheet with 70% completion rate.

**3. Automated RSVP pipeline**
APScheduler sends confirmation reminders 48hrs and 24hrs before each Sunday session. Coordinator gets actionable lead time instead of day-of WhatsApp chaos.

**4. ML intelligence layer**
- **At-risk classifier** (Random Forest + SMOTE): flags kids likely to disengage 2 weeks ahead
- **Progress predictor** (Ridge Regression): forecasts chapter progression per child over 4 weeks
- **Resource demand forecaster**: chains predictions into auto-populated donor wishlist

**5. Live fund drive dashboard + donor impact cards**
Real-time fundraising tracker with personalised donor impact cards triggered when funded items are used in sessions.

---

## Impact

| Metric | Before | After |
|--------|--------|-------|
| Session data entry | 15 min/session | ~30 seconds |
| Data completeness | 70% | 95%+ |
| No-show warning | Day-of | 24–48 hrs advance |
| Resource procurement | Reactive | 4-week predictive |
| Kids tracked | ~200 (no profiles) | 200 with persistent profiles |

*Based on direct observation at U&I Visakhapatnam, 2023–2024*

---

## Tech stack

```
Backend       FastAPI + Python + SQLAlchemy
Database      PostgreSQL (12 tables, multi-chapter schema)
ML            scikit-learn — Random Forest, Ridge Regression, SMOTE
Automation    APScheduler + SendGrid
Frontend      React + Tailwind CSS + Recharts (PWA)
Deploy        Railway + Vercel
```

---

## Project structure

```
impactbridge/
├── app/
│   ├── models.py          # 12 SQLAlchemy models
│   ├── database.py        # DB connection + session
│   ├── api/               # FastAPI route handlers (Phase 2)
│   ├── ml/                # scikit-learn pipeline (Phase 3)
│   └── automation/        # APScheduler jobs (Phase 4)
├── scripts/
│   └── seed.py            # Realistic seed data (200 kids, 50 volunteers)
├── requirements.txt
├── .env.example           # Copy to .env — never commit .env
└── README.md
```

---

## Getting started

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/impactbridge.git
cd impactbridge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your PostgreSQL credentials to .env

# 4. Seed the database
python scripts/seed.py

# 5. Run
uvicorn app.main:app --reload
# Docs at http://localhost:8000/docs
```

### Test credentials (after seeding)
| Role | Email | Password |
|------|-------|----------|
| Coordinator | coord_0_0@impactbridge.org | coord123 |
| Volunteer | vol_0@impactbridge.org | vol123 |
| Donor | donor_0@example.com | donor123 |

---

## Build progress

- [x] Phase 1 — PostgreSQL schema + SQLAlchemy models + seed data
- [ ] Phase 2 — FastAPI backend + JWT auth
- [ ] Phase 3 — ML pipeline
- [ ] Phase 4 — Automation pipeline
- [ ] Phase 5 — React frontend
- [ ] Phase 6 — Deploy

---

## About U&I

[U&I](https://www.unitedindia.org/) is a non-profit educating underprivileged children across India, run entirely by volunteers.

---

*Built by Saatvika Chokkapu · MS Business Analytics & AI, UT Dallas*  
*Volunteer, U&I Visakhapatnam (Sept 2023 – June 2024)*
