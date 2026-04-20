from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import require_coordinator
from app.automation.scheduler import get_job_status

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/status")
def get_automation_status(
    current_user: User = Depends(require_coordinator)
):
    """
    Shows all scheduled jobs and their next run times.
    Coordinator can see when the next ML pipeline, RSVP reminder etc. will fire.
    """
    return {
        "scheduler_running": True,
        "jobs": get_job_status(),
    }


@router.post("/trigger/rsvp-reminders")
def trigger_rsvp_reminders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_coordinator)
):
    """
    Manually trigger RSVP reminders outside of Thursday schedule.
    Useful for testing or if coordinator wants to send early.
    """
    from app.automation.jobs import job_send_rsvp_reminders
    background_tasks.add_task(job_send_rsvp_reminders)
    return {"message": "RSVP reminder job triggered in background"}


@router.post("/trigger/unconfirmed-check")
def trigger_unconfirmed_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_coordinator)
):
    """Manually check for unconfirmed volunteers."""
    from app.automation.jobs import job_check_unconfirmed_volunteers
    background_tasks.add_task(job_check_unconfirmed_volunteers)
    return {"message": "Unconfirmed volunteer check triggered"}


@router.post("/trigger/at-risk-digest")
def trigger_at_risk_digest(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_coordinator)
):
    """Manually send at-risk digest to all coordinators."""
    from app.automation.jobs import job_send_at_risk_digest
    background_tasks.add_task(job_send_at_risk_digest)
    return {"message": "At-risk digest triggered in background"}


@router.get("/logs")
def get_automation_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """
    View recent automation log entries.
    Shows every email sent, to whom, and whether it succeeded.
    """
    try:
        from app.models import AutomationLog
        logs = db.query(AutomationLog)\
            .order_by(AutomationLog.created_at.desc())\
            .limit(limit).all()
        return [
            {
                "id":           log.id,
                "type":         log.log_type,
                "recipient":    log.recipient,
                "subject":      log.subject,
                "status":       log.status,
                "created_at":   str(log.created_at),
            }
            for log in logs
        ]
    except Exception:
        return {"message": "Automation logs table not yet created — run seed.py first"}
