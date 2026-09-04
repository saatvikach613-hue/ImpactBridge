"""
Run tracking
============
Wraps every scheduled job so each execution leaves a row in
`automation_runs` (started, finished, success/failed, one-line summary).

This is what makes the automation *observable*: the coordinator dashboard
and /automation/health read from this table instead of guessing whether
Thursday's reminders actually went out.
"""

import functools
import traceback
from datetime import datetime
from app.database import SessionLocal
from app.models import AutomationRun


def tracked_job(job_id: str):
    """
    Decorator. The wrapped job may return a short summary string
    (e.g. "sent 41, skipped 12"); anything else is stringified.
    Exceptions are recorded as failed runs and re-raised.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, triggered_by: str = "scheduler", **kwargs):
            db = SessionLocal()
            run = AutomationRun(job_id=job_id, triggered_by=triggered_by, status="running")
            try:
                db.add(run)
                db.commit()
                db.refresh(run)
            except Exception:
                db.rollback()
                run = None  # tracking must never block the job itself

            try:
                result = fn(*args, **kwargs)
                if run is not None:
                    run.status      = "success"
                    run.summary     = str(result)[:500] if result is not None else None
                    run.finished_at = datetime.utcnow()
                    db.commit()
                return result
            except Exception as e:
                if run is not None:
                    run.status      = "failed"
                    run.error       = f"{e}\n{traceback.format_exc()}"[:2000]
                    run.finished_at = datetime.utcnow()
                    db.commit()
                raise
            finally:
                db.close()
        return wrapper
    return decorator


def summarize_runs(db, job_ids: list[str]) -> list[dict]:
    """
    For each job: last run + counts over the last 30 days.
    Pure query helper used by /automation/health.
    """
    from datetime import timedelta
    from sqlalchemy import func

    since = datetime.utcnow() - timedelta(days=30)
    out = []
    for job_id in job_ids:
        last = (
            db.query(AutomationRun)
            .filter(AutomationRun.job_id == job_id)
            .order_by(AutomationRun.started_at.desc())
            .first()
        )
        counts = dict(
            db.query(AutomationRun.status, func.count(AutomationRun.id))
            .filter(AutomationRun.job_id == job_id, AutomationRun.started_at >= since)
            .group_by(AutomationRun.status)
            .all()
        )
        total  = sum(counts.values())
        ok     = counts.get("success", 0)
        out.append({
            "job_id":        job_id,
            "last_status":   last.status if last else "never_run",
            "last_run_at":   str(last.started_at) if last else None,
            "last_summary":  last.summary if last else None,
            "last_error":    (last.error or "")[:300] if last and last.status == "failed" else None,
            "triggered_by":  last.triggered_by if last else None,
            "runs_30d":      total,
            "success_rate_30d": round(ok / total, 3) if total else None,
        })
    return out
