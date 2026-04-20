from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List
from app.database import get_db
from app.models import (
    Kid, User, SessionEvent, SessionLog, SessionRsvp,
    MlPrediction, FundDrive, WishlistItem, UserRole,
    RsvpStatus, WishlistStatus, RiskLevel
)
from app.schemas import (
    DashboardResponse, DashboardStats, DashboardAlert, KidOut, SessionEventOut
)
from app.auth import require_coordinator

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """
    The coordinator's full view — stats, alerts, at-risk kids, recent sessions.
    This is what opens on Monday morning.
    """
    # Scope to chapter if provided
    chapter_filter = chapter_id or current_user.chapter_id

    # ── STATS ────────────────────────────────────────
    kid_query = db.query(Kid).filter(Kid.is_active == True)
    if chapter_filter:
        kid_query = kid_query.filter(Kid.chapter_id == chapter_filter)
    total_kids = kid_query.count()

    vol_query = db.query(User).filter(
        User.role == UserRole.volunteer,
        User.is_active == True
    )
    if chapter_filter:
        vol_query = vol_query.filter(User.chapter_id == chapter_filter)
    total_volunteers = vol_query.count()

    # Sessions this week
    week_start = date.today() - timedelta(days=date.today().weekday())
    session_query = db.query(SessionEvent).filter(
        SessionEvent.session_date >= week_start
    )
    if chapter_filter:
        session_query = session_query.filter(SessionEvent.chapter_id == chapter_filter)
    sessions_this_week = session_query.count()

    # At-risk kids count
    at_risk_query = db.query(MlPrediction).filter(MlPrediction.at_risk == True)
    if chapter_filter:
        at_risk_kids_ids = [k.id for k in kid_query.all()]
        at_risk_query = at_risk_query.filter(MlPrediction.kid_id.in_(at_risk_kids_ids))
    at_risk_count = at_risk_query.count()

    # Fund drive progress
    drive = db.query(FundDrive).filter(FundDrive.is_active == True)
    if chapter_filter:
        drive = drive.filter(FundDrive.chapter_id == chapter_filter)
    drive = drive.first()
    fund_pct = None
    if drive and drive.goal_amount > 0:
        fund_pct = round((drive.raised_amount / drive.goal_amount) * 100, 1)

    # Unfunded wishlist
    wish_query = db.query(WishlistItem).filter(WishlistItem.status == WishlistStatus.open)
    unfunded_count = wish_query.count()

    stats = DashboardStats(
        total_kids=total_kids,
        total_volunteers=total_volunteers,
        sessions_this_week=sessions_this_week,
        at_risk_kids=at_risk_count,
        fund_drive_pct=fund_pct,
        unfunded_wishlist_count=unfunded_count
    )

    # ── ALERTS ───────────────────────────────────────
    alerts = []

    # At-risk kids
    at_risk_kids = db.query(MlPrediction).filter(
        MlPrediction.at_risk == True,
        MlPrediction.risk_level == RiskLevel.high
    ).limit(5).all()
    for p in at_risk_kids:
        kid = db.query(Kid).filter_by(id=p.kid_id).first()
        if kid:
            alerts.append(DashboardAlert(
                type="at_risk_kid",
                message=f"{kid.name} is high risk — {p.risk_reason or 'declining session pattern'}",
                severity="high",
                ref_id=kid.id
            ))

    # Inactive volunteers — haven't logged in 14+ days
    two_weeks_ago = date.today() - timedelta(days=14)
    all_vols = vol_query.all()
    for vol in all_vols:
        last_log = db.query(SessionLog).filter_by(volunteer_id=vol.id)\
            .order_by(SessionLog.logged_at.desc()).first()
        if last_log is None or last_log.logged_at.date() < two_weeks_ago:
            alerts.append(DashboardAlert(
                type="inactive_volunteer",
                message=f"{vol.full_name} hasn't logged a session in 14+ days",
                severity="medium",
                ref_id=vol.id
            ))

    # Unfunded wishlist items
    if unfunded_count > 0:
        alerts.append(DashboardAlert(
            type="unfunded_wishlist",
            message=f"{unfunded_count} wishlist items still need funding",
            severity="low"
        ))

    # ── AT-RISK KIDS LIST ─────────────────────────────
    at_risk_kid_ids = [
        p.kid_id for p in db.query(MlPrediction)
        .filter(MlPrediction.at_risk == True).all()
    ]
    at_risk_kids_list = db.query(Kid).filter(Kid.id.in_(at_risk_kid_ids)).limit(10).all()

    # ── RECENT SESSIONS ───────────────────────────────
    recent = db.query(SessionEvent)
    if chapter_filter:
        recent = recent.filter(SessionEvent.chapter_id == chapter_filter)
    recent = recent.order_by(SessionEvent.session_date.desc()).limit(5).all()

    return DashboardResponse(
        stats=stats,
        alerts=alerts[:10],
        at_risk_kids=at_risk_kids_list,
        recent_sessions=recent
    )


@router.get("/chapters", tags=["dashboard"])
def get_all_chapters_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """HQ view — summary stats for every chapter."""
    from app.models import Chapter
    chapters = db.query(Chapter).filter(Chapter.is_active == True).all()
    result = []
    for ch in chapters:
        kids = db.query(Kid).filter_by(chapter_id=ch.id, is_active=True).count()
        vols = db.query(User).filter_by(chapter_id=ch.id, role=UserRole.volunteer, is_active=True).count()
        at_risk = db.query(MlPrediction).join(Kid).filter(
            Kid.chapter_id == ch.id,
            MlPrediction.at_risk == True
        ).count()
        result.append({
            "chapter_id": ch.id,
            "chapter_name": ch.name,
            "city": ch.city,
            "total_kids": kids,
            "total_volunteers": vols,
            "at_risk_kids": at_risk,
        })
    return result
