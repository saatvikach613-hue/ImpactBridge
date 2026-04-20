from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, datetime
from app.database import get_db
from app.models import (
    SessionEvent, SessionLog, SessionRsvp,
    VolunteerKidAssignment, User, RsvpStatus
)
from app.schemas import (
    SessionEventOut, SessionLogOut, BulkSessionLogCreate,
    RsvpOut, RsvpUpdate
)
from app.auth import get_current_user, require_coordinator

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ── SESSION EVENTS ─────────────────────────────────────

@router.get("/", response_model=List[SessionEventOut])
def get_sessions(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SessionEvent)
    if chapter_id:
        query = query.filter_by(chapter_id=chapter_id)
    elif current_user.role == "volunteer":
        query = query.filter_by(chapter_id=current_user.chapter_id)
    return query.order_by(SessionEvent.session_date.desc()).limit(20).all()


@router.get("/upcoming", response_model=List[SessionEventOut])
def get_upcoming_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Next session for the volunteer's chapter."""
    return db.query(SessionEvent).filter(
        SessionEvent.chapter_id == current_user.chapter_id,
        SessionEvent.session_date >= date.today()
    ).order_by(SessionEvent.session_date).limit(3).all()


# ── 3-TAP SESSION LOGGER ──────────────────────────────

def _run_pipeline_background(chapter_id: int):
    """
    Runs ML pipeline in background after session logs submitted.
    Updates predictions immediately so Analysis tab shows fresh data.
    """
    try:
        from app.ml.pipeline import run_pipeline
        run_pipeline(chapter_id=chapter_id, retrain=False)
        print(f"[PIPELINE] Auto-run complete for chapter {chapter_id}")
    except Exception as e:
        print(f"[PIPELINE] Background run failed: {e}")


@router.post("/log", response_model=List[SessionLogOut])
def submit_session_logs(
    payload: BulkSessionLogCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    The 3-tap logger endpoint.
    Volunteer submits all their kids' ratings in one call.
    After saving — triggers ML pipeline in background so
    Analysis tab shows updated predictions immediately.
    """
    # Verify session exists
    session = db.query(SessionEvent).filter_by(id=payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get volunteer's assigned kids for validation
    assigned_ids = {
        a.kid_id for a in db.query(VolunteerKidAssignment)
        .filter_by(volunteer_id=current_user.id, is_active=True).all()
    }

    created_logs = []
    for log_data in payload.logs:
        if current_user.role == "volunteer" and log_data.kid_id not in assigned_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Kid {log_data.kid_id} is not assigned to you"
            )

        # Check for duplicate log
        existing = db.query(SessionLog).filter_by(
            session_id=payload.session_id,
            volunteer_id=current_user.id,
            kid_id=log_data.kid_id,
            subject=log_data.subject
        ).first()
        if existing:
            continue

        log = SessionLog(
            session_id=payload.session_id,
            volunteer_id=current_user.id,
            kid_id=log_data.kid_id,
            rating=log_data.rating,
            subject=log_data.subject,
            chapter_covered=log_data.chapter_covered,
            notes=log_data.notes,
        )
        db.add(log)
        created_logs.append(log)

    db.commit()
    [db.refresh(l) for l in created_logs]

    # Trigger ML pipeline in background for this chapter
    # This updates predictions so Analysis tab reflects new logs immediately
    if created_logs:
        background_tasks.add_task(
            _run_pipeline_background,
            chapter_id=current_user.chapter_id
        )

    return created_logs


@router.get("/history/{kid_id}")
def get_kid_session_history(
    kid_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns session history for a specific kid.
    Used by the volunteer Analysis tab to show trend charts.
    Returns last N sessions with date, rating, and subject.
    """
    # Verify volunteer is assigned to this kid
    if current_user.role == "volunteer":
        assigned = db.query(VolunteerKidAssignment).filter_by(
            volunteer_id=current_user.id,
            kid_id=kid_id,
            is_active=True
        ).first()
        if not assigned:
            raise HTTPException(status_code=403, detail="Not assigned to this kid")

    logs = db.query(SessionLog).filter_by(
        kid_id=kid_id
    ).order_by(SessionLog.logged_at.desc()).limit(limit).all()

    rating_map = {"struggling": 1, "okay": 2, "nailed_it": 3}

    return [
        {
            "session_id":    log.session_id,
            "logged_at":     str(log.logged_at)[:10],
            "rating":        log.rating.value if hasattr(log.rating, 'value') else log.rating,
            "rating_num":    rating_map.get(
                log.rating.value if hasattr(log.rating, 'value') else log.rating, 2
            ),
            "subject":       log.subject,
            "level_covered": log.level_covered or "",
        }
        for log in reversed(logs)  # oldest first for trend chart
    ]


@router.get("/{session_id}/logs", response_model=List[SessionLogOut])
def get_session_logs(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SessionLog).filter_by(session_id=session_id)
    if current_user.role == "volunteer":
        query = query.filter_by(volunteer_id=current_user.id)
    return query.all()


# ── RSVP ──────────────────────────────────────────────

@router.get("/{session_id}/rsvp", response_model=RsvpOut)
def get_my_rsvp(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rsvp = db.query(SessionRsvp).filter_by(
        session_id=session_id,
        volunteer_id=current_user.id
    ).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="No RSVP found")
    return rsvp


@router.patch("/{session_id}/rsvp", response_model=RsvpOut)
def update_rsvp(
    session_id: int,
    update: RsvpUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Volunteer confirms or declines attendance."""
    rsvp = db.query(SessionRsvp).filter_by(
        session_id=session_id,
        volunteer_id=current_user.id
    ).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="No RSVP found")

    rsvp.status = update.status
    rsvp.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(rsvp)
    return rsvp


@router.get("/{session_id}/rsvps", response_model=List[RsvpOut])
def get_all_rsvps(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """Coordinator sees all RSVPs for a session."""
    return db.query(SessionRsvp).filter_by(session_id=session_id).all()
