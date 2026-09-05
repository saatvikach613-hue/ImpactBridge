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


@router.get("/adoption", tags=["dashboard"])
def get_adoption_metrics(
    weeks: int = 8,
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """
    Is the automation actually being used, and did it help?

    - Session log completion vs the ~70% pre-ImpactBridge baseline
    - RSVP response / confirmation rates from the one-tap email links
    - Estimated volunteer minutes saved and coordinator messages avoided
    - Automated emails actually sent (from the audit log)

    Window: past `weeks` weeks of sessions that have already happened.
    """
    from app.models import VolunteerKidAssignment, Chapter, AutomationLog
    from app.metrics import compute_adoption

    weeks = max(1, min(weeks, 52))
    today = date.today()
    since = today - timedelta(weeks=weeks)

    # Chapters in scope
    if chapter_id:
        chapter_ids = [chapter_id]
    else:
        chapter_ids = [c.id for c in db.query(Chapter).filter_by(is_active=True).all()]

    # Sessions that already happened in the window
    sessions = db.query(SessionEvent).filter(
        SessionEvent.chapter_id.in_(chapter_ids),
        SessionEvent.session_date >= since,
        SessionEvent.session_date < today,
    ).all()
    session_ids = [s.id for s in sessions]

    # "Session sheet completion", measured the same way the 70% baseline was:
    #   expected = volunteer-sessions where the volunteer confirmed attendance
    #   actual   = of those, how many submitted at least one session log
    # (Counting per enrolled kid would penalise absences, which isn't adoption.)
    expected_logs = actual_logs = 0
    if session_ids:
        expected_logs = db.query(SessionRsvp).filter(
            SessionRsvp.session_id.in_(session_ids),
            SessionRsvp.status == RsvpStatus.confirmed,
        ).count()
        actual_logs = (
            db.query(SessionLog.session_id, SessionLog.volunteer_id)
            .join(SessionRsvp, (SessionRsvp.session_id == SessionLog.session_id)
                               & (SessionRsvp.volunteer_id == SessionLog.volunteer_id))
            .filter(SessionLog.session_id.in_(session_ids),
                    SessionRsvp.status == RsvpStatus.confirmed)
            .distinct()
            .count()
        )

    # RSVP adoption
    rsvps_total = rsvps_responded = rsvps_confirmed = 0
    if session_ids:
        rsvps_total = db.query(SessionRsvp).filter(SessionRsvp.session_id.in_(session_ids)).count()
        rsvps_responded = db.query(SessionRsvp).filter(
            SessionRsvp.session_id.in_(session_ids),
            SessionRsvp.status != RsvpStatus.pending,
        ).count()
        rsvps_confirmed = db.query(SessionRsvp).filter(
            SessionRsvp.session_id.in_(session_ids),
            SessionRsvp.status == RsvpStatus.confirmed,
        ).count()

    # Emails actually sent by the automation in the window
    automated_emails_sent = db.query(AutomationLog).filter(
        AutomationLog.created_at >= since,
        AutomationLog.status.like("sent%"),
    ).count()

    snapshot = compute_adoption(
        window_weeks=weeks,
        sessions_in_window=len(sessions),
        expected_logs=expected_logs,
        actual_logs=actual_logs,
        rsvps_total=rsvps_total,
        rsvps_responded=rsvps_responded,
        rsvps_confirmed=rsvps_confirmed,
        automated_emails_sent=automated_emails_sent,
    )
    return snapshot.to_dict()


@router.get("/analytics", tags=["dashboard"])
def get_analytics(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """
    Everything the dashboard charts need, computed from the database.
    (These used to be hardcoded sample arrays in the frontend.)

    - volunteers:       reliability per volunteer from RSVP history
    - attendance_trend: last 8 past sessions, kid + volunteer attendance %
    - retention:        monthly active kids (enrolled and still active)
    - fund_trend:       cumulative donations by month (falls back to the drive's raised total)
    - progress_trend:   average level index taught per month, from session logs
    - hygiene:          null — not instrumented yet; the UI labels it as sample data
    """
    from collections import defaultdict
    from app.models import Chapter, VolunteerKidAssignment, Donation, FundDrive
    from datetime import datetime

    today = date.today()
    if chapter_id:
        chapter_ids = [chapter_id]
    else:
        chapter_ids = [c.id for c in db.query(Chapter).filter_by(is_active=True).all()]
    chapter_names = dict(db.query(Chapter.id, Chapter.name).all())

    past_sessions = (
        db.query(SessionEvent)
        .filter(SessionEvent.chapter_id.in_(chapter_ids), SessionEvent.session_date < today)
        .order_by(SessionEvent.session_date)
        .all()
    )
    past_ids = [s.id for s in past_sessions]
    session_by_id = {s.id: s for s in past_sessions}

    # ── Volunteers: reliability = confirmed / all RSVPs on past sessions ─────
    volunteers_out = []
    vols = db.query(User).filter(
        User.chapter_id.in_(chapter_ids), User.role == UserRole.volunteer, User.is_active == True
    ).all()
    if past_ids:
        rsvp_rows = (
            db.query(SessionRsvp.volunteer_id, SessionRsvp.status, func.count(SessionRsvp.id))
            .filter(SessionRsvp.session_id.in_(past_ids))
            .group_by(SessionRsvp.volunteer_id, SessionRsvp.status)
            .all()
        )
    else:
        rsvp_rows = []
    per_vol = defaultdict(lambda: {"confirmed": 0, "total": 0})
    for vid, st, n in rsvp_rows:
        per_vol[vid]["total"] += n
        if st == RsvpStatus.confirmed:
            per_vol[vid]["confirmed"] += n
    kids_per_vol = dict(
        db.query(VolunteerKidAssignment.volunteer_id, func.count(VolunteerKidAssignment.id))
        .filter(VolunteerKidAssignment.is_active == True)
        .group_by(VolunteerKidAssignment.volunteer_id).all()
    )
    for v in vols:
        stats = per_vol.get(v.id, {"confirmed": 0, "total": 0})
        total = stats["total"]
        reliability = round(100 * stats["confirmed"] / total) if total else None
        parts = (v.full_name or "").split()
        short = f"{parts[0]} {parts[1][0]}." if len(parts) > 1 else (v.full_name or "Volunteer")
        volunteers_out.append({
            "id": v.id,
            "name": short,
            "reliability": reliability,
            "sessions": total,
            "missed": total - stats["confirmed"],
            "kids": kids_per_vol.get(v.id, 0),
            "chapter": (chapter_names.get(v.chapter_id) or "").split(" - ")[-1],
        })
    volunteers_out.sort(key=lambda x: (x["reliability"] is None, -(x["reliability"] or 0)))

    # ── Attendance trend: last 8 past session dates ──────────────────────────
    active_kids_per_chapter = dict(
        db.query(Kid.chapter_id, func.count(Kid.id))
        .filter(Kid.chapter_id.in_(chapter_ids), Kid.is_active == True)
        .group_by(Kid.chapter_id).all()
    )
    dates = sorted({s.session_date for s in past_sessions})[-8:]
    attendance_trend = []
    for i, d in enumerate(dates):
        sids = [s.id for s in past_sessions if s.session_date == d]
        enrolled = sum(active_kids_per_chapter.get(session_by_id[sid].chapter_id, 0) for sid in sids)
        kids_logged = (
            db.query(SessionLog.session_id, SessionLog.kid_id)
            .filter(SessionLog.session_id.in_(sids)).distinct().count()
        ) if sids else 0
        rs_total = db.query(SessionRsvp).filter(SessionRsvp.session_id.in_(sids)).count() if sids else 0
        rs_conf = db.query(SessionRsvp).filter(
            SessionRsvp.session_id.in_(sids), SessionRsvp.status == RsvpStatus.confirmed
        ).count() if sids else 0
        attendance_trend.append({
            "week": f"W{i + 1}",
            "date": str(d),
            "kids": round(100 * kids_logged / enrolled) if enrolled else 0,
            "volunteers": round(100 * rs_conf / rs_total) if rs_total else 0,
        })

    # ── Retention: kids enrolled by month-end and still active ───────────────
    all_kids = db.query(Kid).filter(Kid.chapter_id.in_(chapter_ids)).all()
    total_kids = len(all_kids)
    retention = []
    for k in range(5, -1, -1):
        y, m = today.year, today.month - k
        while m <= 0:
            m += 12; y -= 1
        month_end = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
        enrolled = [x for x in all_kids if (x.enrolled_date or date.min) <= month_end]
        active = sum(1 for x in enrolled if x.is_active)
        retention.append({
            "month": month_end.strftime("%b"),
            "active": active,
            "churned": len(enrolled) - active,
            "enrolled": len(enrolled),
        })

    # ── Fund trend ───────────────────────────────────────────────────────────
    drives = db.query(FundDrive).filter(FundDrive.chapter_id.in_(chapter_ids), FundDrive.is_active == True).all()
    goal = sum(d.goal_amount for d in drives)
    raised = sum(d.raised_amount or 0 for d in drives)
    donations = (
        db.query(Donation).filter(Donation.fund_drive_id.in_([d.id for d in drives]))
        .order_by(Donation.donated_at).all()
    ) if drives else []
    fund_trend = []
    if donations:
        cum = 0.0
        by_month = defaultdict(float)
        for dn in donations:
            by_month[dn.donated_at.strftime("%Y-%m")] += dn.amount
        for ym in sorted(by_month):
            cum += by_month[ym]
            fund_trend.append({"month": datetime.strptime(ym, "%Y-%m").strftime("%b"), "raised": round(cum), "needed": round(goal)})
        fund_source = "donations"
    else:
        start = min((d.start_date for d in drives), default=today)
        fund_trend = [
            {"month": start.strftime("%b"), "raised": 0, "needed": round(goal)},
            {"month": today.strftime("%b"), "raised": round(raised), "needed": round(goal)},
        ]
        fund_source = "drive_totals"

    # ── Progress trend: avg level index taught per month ─────────────────────
    ENGLISH = ["letter", "word", "sentence", "story", "advanced"]
    MATH = ["pre_number", "number_recognition", "basic_operations", "advanced_operations", "syllabus_aligned"]
    progress = []
    if past_ids:
        rows = (
            db.query(SessionEvent.session_date, SessionLog.subject, SessionLog.level_covered)
            .join(SessionEvent, SessionEvent.id == SessionLog.session_id)
            .filter(SessionLog.session_id.in_(past_ids), SessionLog.level_covered.isnot(None))
            .all()
        )
        acc = defaultdict(list)
        for d, subj, lvl in rows:
            lvl_s = lvl.value if hasattr(lvl, "value") else str(lvl)
            scale = ENGLISH if subj == "english" else MATH
            if lvl_s in scale:
                acc[d.strftime("%Y-%m")].append(scale.index(lvl_s))
        for ym in sorted(acc)[-8:]:
            vals = acc[ym]
            progress.append({"month": datetime.strptime(ym, "%Y-%m").strftime("%b"), "avgLevel": round(sum(vals) / len(vals), 2)})

    return {
        "totals": {"kids": total_kids, "volunteers": len(vols), "fund_goal": round(goal), "fund_raised": round(raised)},
        "volunteers": volunteers_out,
        "attendance_trend": attendance_trend,
        "retention": retention,
        "fund_trend": fund_trend,
        "fund_source": fund_source,
        "progress_trend": progress,
        "hygiene": None,  # not instrumented — UI shows sample data with a label
    }
