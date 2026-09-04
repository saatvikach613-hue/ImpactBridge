"""
Automation API
==============
Three audiences:

1. Coordinators (JWT) — see job status/health/logs from the dashboard,
   and manually fire a job early if they need to.
2. An external scheduler (GitHub Actions cron, see .github/workflows/automation.yml)
   — hits /automation/trigger/* with the AUTOMATION_API_KEY header.
   This is the reliability fix: the in-process APScheduler only fires while
   the web dyno is awake, which free-tier hosts don't guarantee.
3. Public /automation/ping — cheap liveness check for uptime monitors.
"""

import hmac
from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User, AutomationLog
from app.auth import get_current_user
from app.config import AUTOMATION_API_KEY
from app.automation.scheduler import get_job_status
from app.automation.tracking import summarize_runs

router = APIRouter(prefix="/automation", tags=["automation"])

JOB_IDS = ["rsvp_reminders", "unconfirmed_alert", "ml_pipeline", "at_risk_digest"]

# Human-readable schedule, kept in sync with scheduler.py
JOB_SCHEDULE = {
    "rsvp_reminders":    {"when": "Thursday 20:00", "replaces": "Manual Fri/Sat WhatsApp confirmations"},
    "unconfirmed_alert": {"when": "Friday 08:00",   "replaces": "Saturday-morning scramble for coverage"},
    "ml_pipeline":       {"when": "Sunday 23:00",   "replaces": "Manual review of 100+ kids' notes"},
    "at_risk_digest":    {"when": "Monday 07:00",   "replaces": "Coordinator hunting for who needs help"},
}


# ── Auth: coordinator JWT *or* automation API key ────────────────────────────

def _bearer_optional(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None


def require_coordinator_or_api_key(
    x_automation_key: Optional[str] = Header(default=None, alias="X-Automation-Key"),
    token: Optional[str] = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> str:
    """
    Returns who triggered the call: "github_actions" for API-key callers,
    "api" for logged-in coordinators. Raises 401/403 otherwise.
    """
    # 1. External scheduler
    if x_automation_key:
        if AUTOMATION_API_KEY and hmac.compare_digest(x_automation_key, AUTOMATION_API_KEY):
            return "github_actions"
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid automation key")

    # 2. Logged-in coordinator
    if token:
        user: User = get_current_user(token, db)  # raises 401 if bad
        if user.role.value != "coordinator":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Coordinator access required")
        return "api"

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")


def _require_coordinator_only(who: str = Depends(require_coordinator_or_api_key)) -> str:
    """Read endpoints stay coordinator-only (API key is for triggering, not browsing)."""
    if who != "api":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Coordinator login required")
    return who


# ── Read endpoints ───────────────────────────────────────────────────────────

@router.get("/ping")
def ping():
    """Unauthenticated liveness check (for uptime monitors / GitHub Actions keep-alive)."""
    return {"ok": True}


@router.get("/status")
def get_automation_status(_: str = Depends(_require_coordinator_only)):
    """All scheduled jobs and their next in-process run times."""
    return {"scheduler_running": True, "jobs": get_job_status()}


@router.get("/health")
def get_automation_health(
    db: Session = Depends(get_db),
    _: str = Depends(_require_coordinator_only),
):
    """
    Per-job health for the dashboard panel:
    last run, outcome, one-line summary, 30-day success rate,
    plus email counts from the audit log.
    """
    runs = summarize_runs(db, JOB_IDS)
    for r in runs:
        r.update(JOB_SCHEDULE.get(r["job_id"], {}))

    # Email totals (last 30 days) by type and status
    from datetime import datetime, timedelta
    from sqlalchemy import func
    since = datetime.utcnow() - timedelta(days=30)
    email_rows = (
        db.query(AutomationLog.log_type, AutomationLog.status, func.count(AutomationLog.id))
        .filter(AutomationLog.created_at >= since)
        .group_by(AutomationLog.log_type, AutomationLog.status)
        .all()
    )
    emails: dict = {}
    for log_type, st, n in email_rows:
        bucket = emails.setdefault(log_type, {"sent": 0, "failed": 0})
        if st.startswith("sent"):
            bucket["sent"] += n
        else:
            bucket["failed"] += n

    overall = "healthy"
    if any(r["last_status"] == "failed" for r in runs):
        overall = "degraded"
    if all(r["last_status"] == "never_run" for r in runs):
        overall = "idle"

    return {"overall": overall, "jobs": runs, "emails_30d": emails}


@router.get("/logs")
def get_automation_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: str = Depends(_require_coordinator_only),
):
    """Every automated email: to whom, what, and whether it succeeded."""
    logs = (
        db.query(AutomationLog)
        .order_by(AutomationLog.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return [
        {
            "id":         log.id,
            "type":       log.log_type,
            "recipient":  log.recipient,
            "subject":    log.subject,
            "status":     log.status,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]


# ── Trigger endpoints (coordinator or external cron) ─────────────────────────

def _trigger(background_tasks: BackgroundTasks, job_fn, job_id: str, who: str):
    background_tasks.add_task(job_fn, triggered_by=who)
    return {"job": job_id, "triggered_by": who, "message": f"{job_id} started in background"}


@router.post("/trigger/rsvp-reminders")
def trigger_rsvp_reminders(background_tasks: BackgroundTasks, who: str = Depends(require_coordinator_or_api_key)):
    from app.automation.jobs import job_send_rsvp_reminders
    return _trigger(background_tasks, job_send_rsvp_reminders, "rsvp_reminders", who)


@router.post("/trigger/unconfirmed-check")
def trigger_unconfirmed_check(background_tasks: BackgroundTasks, who: str = Depends(require_coordinator_or_api_key)):
    from app.automation.jobs import job_check_unconfirmed_volunteers
    return _trigger(background_tasks, job_check_unconfirmed_volunteers, "unconfirmed_alert", who)


@router.post("/trigger/ml-pipeline")
def trigger_ml_pipeline(background_tasks: BackgroundTasks, who: str = Depends(require_coordinator_or_api_key)):
    from app.automation.jobs import job_run_ml_pipeline
    return _trigger(background_tasks, job_run_ml_pipeline, "ml_pipeline", who)


@router.post("/trigger/at-risk-digest")
def trigger_at_risk_digest(background_tasks: BackgroundTasks, who: str = Depends(require_coordinator_or_api_key)):
    from app.automation.jobs import job_send_at_risk_digest
    return _trigger(background_tasks, job_send_at_risk_digest, "at_risk_digest", who)
