"""
Scheduled Jobs
===============
All automated tasks that run on a schedule.
Registered with APScheduler in scheduler.py.

Weekly automation cycle:
- Thursday 8pm  → send RSVP reminders to all volunteers
- Friday  8am   → alert coordinator about unconfirmed volunteers
- Sunday  11pm  → run ML pipeline, update predictions, populate wishlist
- Monday  7am   → send at-risk digest to coordinators
- On demand     → donor impact card when funded item used in session

This is the pipeline that replaces:
- 5+ manual WhatsApp messages every Friday/Saturday (observed at U&I Vizag)
- Manual session sheet chasing (70% completion pre-ImpactBridge)
- Reactive book procurement (replaced by 4-week predictive forecast)
"""

from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    SessionEvent, SessionRsvp, User, Chapter,
    MlPrediction, Kid, WishlistItem, Donation,
    UserRole, RsvpStatus, WishlistStatus
)
from app.automation.email_service import (
    send_rsvp_reminder,
    send_coordinator_alert,
    send_donor_impact_card,
    send_at_risk_digest,
)


def job_send_rsvp_reminders():
    """
    Runs every Thursday at 8pm.
    Sends RSVP confirmation request to every volunteer
    for the upcoming Sunday session.

    Replaces: manual WhatsApp messages sent every Friday/Saturday
    Impact: coordinator gets 48-hour warning instead of day-of surprise
    """
    print(f"\n[SCHEDULER] Running RSVP reminder job — {datetime.now()}")
    db       = SessionLocal()
    sent     = 0
    skipped  = 0

    try:
        # Find next Sunday
        today      = date.today()
        days_ahead = (6 - today.weekday()) % 7 or 7
        next_sunday = today + timedelta(days=days_ahead)

        sessions = db.query(SessionEvent).filter(
            SessionEvent.session_date == next_sunday
        ).all()

        if not sessions:
            print(f"  No sessions found for {next_sunday}")
            return

        for session in sessions:
            chapter = db.query(Chapter).filter_by(id=session.chapter_id).first()
            if not chapter:
                continue

            # Get all volunteers for this chapter
            volunteers = db.query(User).filter_by(
                chapter_id=session.chapter_id,
                role=UserRole.volunteer,
                is_active=True
            ).all()

            for vol in volunteers:
                # Check if RSVP already exists and was responded to
                rsvp = db.query(SessionRsvp).filter_by(
                    session_id=session.id,
                    volunteer_id=vol.id
                ).first()

                if rsvp and rsvp.status != RsvpStatus.pending:
                    skipped += 1
                    continue  # already responded

                # Create RSVP record if not exists
                if not rsvp:
                    rsvp = SessionRsvp(
                        session_id=session.id,
                        volunteer_id=vol.id,
                        status=RsvpStatus.pending,
                    )
                    db.add(rsvp)
                    db.flush()

                # Build confirm URL (frontend will handle this in Phase 5)
                confirm_url = f"https://impactbridge.vercel.app/rsvp/{session.id}/{vol.id}"

                success = send_rsvp_reminder(
                    volunteer_email=vol.email,
                    volunteer_name=vol.full_name,
                    session_date=str(next_sunday),
                    chapter_name=chapter.name,
                    confirm_url=confirm_url,
                    db=db
                )

                if success:
                    rsvp.reminder_sent = True
                    sent += 1

        db.commit()
        print(f"  RSVP reminders sent: {sent} | Already responded: {skipped}")

    except Exception as e:
        db.rollback()
        print(f"  RSVP reminder job failed: {e}")
    finally:
        db.close()


def job_check_unconfirmed_volunteers():
    """
    Runs every Friday at 8am.
    Checks for unconfirmed volunteers and alerts coordinators.

    Gives coordinator 48 hours to arrange coverage before Sunday.
    Replaces the Saturday morning panic.
    """
    print(f"\n[SCHEDULER] Checking unconfirmed volunteers — {datetime.now()}")
    db = SessionLocal()

    try:
        today       = date.today()
        days_ahead  = (6 - today.weekday()) % 7 or 7
        next_sunday = today + timedelta(days=days_ahead)

        sessions = db.query(SessionEvent).filter(
            SessionEvent.session_date == next_sunday
        ).all()

        for session in sessions:
            chapter = db.query(Chapter).filter_by(id=session.chapter_id).first()
            if not chapter:
                continue

            # Find unconfirmed volunteers
            unconfirmed_rsvps = db.query(SessionRsvp).filter_by(
                session_id=session.id,
                status=RsvpStatus.pending
            ).all()

            if not unconfirmed_rsvps:
                print(f"  {chapter.name}: all volunteers confirmed")
                continue

            # Build list with kid counts
            unconfirmed_list = []
            for rsvp in unconfirmed_rsvps:
                vol = db.query(User).filter_by(id=rsvp.volunteer_id).first()
                if not vol:
                    continue
                from app.models import VolunteerKidAssignment
                kid_count = db.query(VolunteerKidAssignment).filter_by(
                    volunteer_id=vol.id, is_active=True
                ).count()
                unconfirmed_list.append({
                    "name":       vol.full_name,
                    "email":      vol.email,
                    "kids_count": kid_count,
                })

            if not unconfirmed_list:
                continue

            # Alert coordinators for this chapter
            coordinators = db.query(User).filter_by(
                chapter_id=session.chapter_id,
                role=UserRole.coordinator,
                is_active=True
            ).all()

            for coord in coordinators:
                send_coordinator_alert(
                    coordinator_email=coord.email,
                    coordinator_name=coord.full_name,
                    session_date=str(next_sunday),
                    chapter_name=chapter.name,
                    unconfirmed_volunteers=unconfirmed_list,
                    db=db
                )
                print(f"  Alert sent to {coord.full_name} — {len(unconfirmed_list)} unconfirmed")

    except Exception as e:
        db.rollback()
        print(f"  Unconfirmed check failed: {e}")
    finally:
        db.close()


def job_run_ml_pipeline():
    """
    Runs every Sunday at 11pm.
    Triggers the full ML pipeline — features, predictions, wishlist.

    This is the core intelligence loop:
    Session data → ML → predictions → wishlist → donor funds it
    """
    print(f"\n[SCHEDULER] Running Sunday night ML pipeline — {datetime.now()}")
    try:
        from app.ml.pipeline import run_pipeline
        results = run_pipeline(retrain=False)
        print(f"  ML pipeline complete: {results}")
    except Exception as e:
        print(f"  ML pipeline failed: {e}")


def job_send_at_risk_digest():
    """
    Runs every Monday at 7am.
    Sends coordinators a summary of at-risk kids flagged by last night's ML run.
    """
    print(f"\n[SCHEDULER] Sending at-risk digest — {datetime.now()}")
    db = SessionLocal()

    try:
        chapters = db.query(Chapter).filter_by(is_active=True).all()

        for chapter in chapters:
            kid_ids = [k.id for k in db.query(Kid).filter_by(
                chapter_id=chapter.id, is_active=True
            ).all()]

            if not kid_ids:
                continue

            # Get latest at-risk predictions
            from sqlalchemy import func
            latest = db.query(
                MlPrediction.kid_id,
                func.max(MlPrediction.predicted_at).label("max_dt")
            ).group_by(MlPrediction.kid_id).subquery()

            at_risk_preds = db.query(MlPrediction).join(
                latest,
                (MlPrediction.kid_id == latest.c.kid_id) &
                (MlPrediction.predicted_at == latest.c.max_dt)
            ).filter(
                MlPrediction.kid_id.in_(kid_ids),
                MlPrediction.at_risk == True
            ).all()

            if not at_risk_preds:
                print(f"  {chapter.name}: no at-risk kids this week")
                continue

            # Build kid summaries
            at_risk_kids = []
            for pred in at_risk_preds:
                kid = db.query(Kid).filter_by(id=pred.kid_id).first()
                if not kid:
                    continue
                eng_level  = kid.english_level.value if hasattr(kid.english_level, 'value') else str(kid.english_level)
                math_level = kid.math_level.value if hasattr(kid.math_level, 'value') else str(kid.math_level)
                at_risk_kids.append({
                    "name":          kid.name,
                    "english_level": eng_level,
                    "math_level":    math_level,
                    "risk_reason":   pred.risk_reason or "pattern flagged",
                })

            # Send to all coordinators for this chapter
            coordinators = db.query(User).filter_by(
                chapter_id=chapter.id,
                role=UserRole.coordinator,
                is_active=True
            ).all()

            for coord in coordinators:
                send_at_risk_digest(
                    coordinator_email=coord.email,
                    coordinator_name=coord.full_name,
                    chapter_name=chapter.name,
                    at_risk_kids=at_risk_kids,
                    db=db
                )
                print(f"  Digest sent to {coord.full_name} — {len(at_risk_kids)} kids flagged")

    except Exception as e:
        db.rollback()
        print(f"  At-risk digest failed: {e}")
    finally:
        db.close()


def trigger_donor_impact_card(
    wishlist_item_id: int,
    session_event_id: int,
    db: Session
):
    """
    Called immediately when a funded wishlist item is used in a session.
    Not scheduled — triggered by the session log submission.

    This is the loop that makes donors come back:
    Donor funds item → item used in session → donor gets personal update
    """
    try:
        item = db.query(WishlistItem).filter_by(id=wishlist_item_id).first()
        if not item or not item.kid_id:
            return

        # Find the donor
        donation = db.query(Donation).filter_by(
            wishlist_item_id=wishlist_item_id
        ).order_by(Donation.donated_at.desc()).first()

        if not donation or not donation.donor_email:
            return

        if donation.impact_card_sent:
            return  # already sent

        kid     = db.query(Kid).filter_by(id=item.kid_id).first()
        session = db.query(SessionEvent).filter_by(id=session_event_id).first()
        chapter = db.query(Chapter).filter_by(id=kid.chapter_id).first() if kid else None

        if not all([kid, session, chapter]):
            return

        success = send_donor_impact_card(
            donor_email=donation.donor_email,
            donor_name=donation.donor_name or "Friend",
            item_name=item.item_name,
            kid_name=kid.name,
            chapter_name=chapter.name,
            session_date=str(session.session_date),
            db=db
        )

        if success:
            donation.impact_card_sent = True
            item.used_in_session = session_event_id
            item.status = WishlistStatus.used
            db.commit()

    except Exception as e:
        print(f"Donor impact card trigger failed: {e}")
