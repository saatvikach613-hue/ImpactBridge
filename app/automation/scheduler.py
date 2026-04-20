"""
Scheduler
==========
APScheduler configuration and job registration.
Starts automatically when the FastAPI server starts.

Schedule:
- Thursday 20:00 → RSVP reminders to all volunteers
- Friday   08:00 → Alert coordinators about unconfirmed volunteers
- Sunday   23:00 → Run full ML pipeline
- Monday   07:00 → Send at-risk digest to coordinators

All times are local server time.
In production (Railway), set your timezone in environment variables.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

# Single scheduler instance — imported by main.py
scheduler = BackgroundScheduler(
    job_defaults={
        "coalesce":       True,   # run once even if missed multiple times
        "max_instances":  1,      # never run same job twice simultaneously
        "misfire_grace_time": 3600,  # allow 1hr late if server was down
    }
)


def start_scheduler():
    """
    Register all jobs and start the scheduler.
    Called once when FastAPI starts up.
    """
    from app.automation.jobs import (
        job_send_rsvp_reminders,
        job_check_unconfirmed_volunteers,
        job_run_ml_pipeline,
        job_send_at_risk_digest,
    )

    # Thursday 8pm — RSVP reminders
    scheduler.add_job(
        job_send_rsvp_reminders,
        CronTrigger(day_of_week="thu", hour=20, minute=0),
        id="rsvp_reminders",
        name="Send RSVP reminders to volunteers",
        replace_existing=True,
    )

    # Friday 8am — Unconfirmed volunteer alert
    scheduler.add_job(
        job_check_unconfirmed_volunteers,
        CronTrigger(day_of_week="fri", hour=8, minute=0),
        id="unconfirmed_alert",
        name="Alert coordinators about unconfirmed volunteers",
        replace_existing=True,
    )

    # Sunday 11pm — Full ML pipeline
    scheduler.add_job(
        job_run_ml_pipeline,
        CronTrigger(day_of_week="sun", hour=23, minute=0),
        id="ml_pipeline",
        name="Run weekly ML pipeline",
        replace_existing=True,
    )

    # Monday 7am — At-risk digest
    scheduler.add_job(
        job_send_at_risk_digest,
        CronTrigger(day_of_week="mon", hour=7, minute=0),
        id="at_risk_digest",
        name="Send at-risk digest to coordinators",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("ImpactBridge scheduler started — 4 jobs registered")
    print("\n[SCHEDULER] Started — 4 jobs registered:")
    print("  Thu 20:00 → RSVP reminders")
    print("  Fri 08:00 → Unconfirmed volunteer alert")
    print("  Sun 23:00 → ML pipeline")
    print("  Mon 07:00 → At-risk digest")


def stop_scheduler():
    """Called when FastAPI shuts down."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_job_status() -> list:
    """Returns current status of all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id":       job.id,
            "name":     job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else "not scheduled",
        })
    return jobs
