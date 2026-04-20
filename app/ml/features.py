"""
Feature Engineering Pipeline
==============================
Reads from dbt-transformed tables in the analytics schema.
Specifically reads from analytics.int_kid_features which was
built by dbt from raw session logs.

All features are engineered per kid based on their session history.
Levels are U&I's real tracking system — not chapter numbers.

English levels: letter → word → sentence → story → advanced
Math levels:    pre_number → number_recognition → basic_operations
                → advanced_operations → syllabus_aligned

8 features engineered:
1. attendance_rate         — sessions attended / sessions possible (last 4 weeks)
2. avg_rating              — mean score (struggling=1, okay=2, nailed_it=3)
3. rating_trend            — slope of ratings over last 4 sessions
4. consecutive_struggles   — streak of struggling sessions
5. chapters_per_month      — level advancement velocity
6. days_since_last_session — recency signal
7. volunteer_consistency   — how consistently their volunteer shows up
8. stuck_flag              — same level for 3+ consecutive sessions
"""

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import date
from app.models import SessionLog, SessionRsvp, VolunteerKidAssignment, Kid, RsvpStatus

# ── U&I official level systems ─────────────────────────────────────────────────
ENGLISH_LEVELS = ["letter", "word", "sentence", "story", "advanced"]
MATH_LEVELS    = ["pre_number", "number_recognition", "basic_operations",
                  "advanced_operations", "syllabus_aligned"]

# Progression rates from U&I Annual Report 2024-25
# Used to calibrate ML model expectations
ENGLISH_PROGRESSION_RATES = {
    "letter":   0.68,   # 68% of letter-level kids progressed
    "word":     0.28,
    "sentence": 0.25,
    "story":    0.28,
    "advanced": 0.00,
}
MATH_PROGRESSION_RATE = 0.43  # 43% progressed to higher math level


def level_to_num(level: str, level_list: list) -> int:
    """Convert level string to numeric index for ML models."""
    try:
        return level_list.index(level)
    except ValueError:
        return 0


def num_to_level(num: int, level_list: list) -> str:
    """Convert numeric index back to level string."""
    idx = int(round(max(0, min(num, len(level_list) - 1))))
    return level_list[idx]


FEATURE_COLUMNS = [
    "attendance_rate",
    "avg_rating",
    "rating_trend",
    "consecutive_struggles",
    "levels_per_month",
    "days_since_last_session",
    "volunteer_consistency",
    "stuck_flag",
]


def build_features(db: Session, chapter_id: int = None) -> pd.DataFrame:
    """
    Main feature engineering function.
    Reads session logs from PostgreSQL and engineers features per kid.
    Returns one row per kid with all 8 features + level info.
    """
    log_query = db.query(SessionLog)
    if chapter_id:
        kid_ids = [k.id for k in db.query(Kid).filter_by(chapter_id=chapter_id).all()]
        if not kid_ids:
            return pd.DataFrame()
        log_query = log_query.filter(SessionLog.kid_id.in_(kid_ids))

    logs = log_query.all()
    if not logs:
        return pd.DataFrame()

    # Build DataFrame from logs
    rows = []
    for log in logs:
        rows.append({
            "kid_id":        log.kid_id,
            "volunteer_id":  log.volunteer_id,
            "session_id":    log.session_id,
            "subject":       log.subject,
            "level_covered": log.level_covered or "",
            "rating":        log.rating.value,
            "logged_at":     log.logged_at,
        })
    df = pd.DataFrame(rows)
    rating_map = {"struggling": 1, "okay": 2, "nailed_it": 3}
    df["rating_num"] = df["rating"].map(rating_map)
    df["logged_at"]  = pd.to_datetime(df["logged_at"], utc=True).dt.tz_localize(None)
    df = df.sort_values(["kid_id", "logged_at"])

    # Get all kids
    kids_query = db.query(Kid).filter(Kid.is_active == True)
    if chapter_id:
        kids_query = kids_query.filter(Kid.chapter_id == chapter_id)
    kids = kids_query.all()

    feature_rows = []
    # Use UTC aware cutoff to match common practice, but ensure compatibility
    cutoff = pd.Timestamp.now(tz='UTC').tz_localize(None) - pd.Timedelta(weeks=4)

    for kid in kids:
        kid_logs    = df[df["kid_id"] == kid.id].copy()
        recent_logs = kid_logs[kid_logs["logged_at"] >= cutoff]

        # ── Feature 1: Attendance rate ─────────────────────────────────────
        sessions_attended = recent_logs["session_id"].nunique()
        sessions_possible = max(sessions_attended, 1)
        attendance_rate   = min(sessions_attended / sessions_possible, 1.0)

        # ── Feature 2: Average rating ──────────────────────────────────────
        avg_rating = recent_logs["rating_num"].mean() if len(recent_logs) > 0 else 2.0

        # ── Feature 3: Rating trend (slope) ───────────────────────────────
        if len(recent_logs) >= 3:
            ratings      = recent_logs["rating_num"].values
            x            = np.arange(len(ratings))
            rating_trend = float(np.polyfit(x, ratings, 1)[0])
        else:
            rating_trend = 0.0

        # ── Feature 4: Consecutive struggles ──────────────────────────────
        all_ratings = kid_logs["rating_num"].values
        streak = 0
        for r in reversed(all_ratings):
            if r == 1:
                streak += 1
            else:
                break
        consecutive_struggles = streak

        # ── Feature 5: Level advancement velocity ─────────────────────────
        # How many levels has this kid advanced per month?
        eng_logs  = kid_logs[kid_logs["subject"] == "english"]
        math_logs = kid_logs[kid_logs["subject"] == "math"]

        def calc_velocity(subject_logs, level_list):
            if len(subject_logs) < 2:
                return 0.3
            levels  = subject_logs["level_covered"].apply(
                lambda l: level_to_num(l, level_list)
            ).values
            dates   = subject_logs["logged_at"].values
            months  = max((dates[-1] - dates[0]) / np.timedelta64(30, 'D'), 0.1)
            advancement = max(levels[-1] - levels[0], 0)
            return advancement / months

        eng_velocity  = calc_velocity(eng_logs,  ENGLISH_LEVELS)
        math_velocity = calc_velocity(math_logs, MATH_LEVELS)
        levels_per_month = (eng_velocity + math_velocity) / 2

        # ── Feature 6: Days since last session ────────────────────────────
        if len(kid_logs) > 0:
            last_session  = kid_logs["logged_at"].max()
            now_naive     = pd.Timestamp.now(tz='UTC').tz_localize(None)
            days_since    = (now_naive - last_session).days
        else:
            days_since = 30

        # ── Feature 7: Volunteer consistency ──────────────────────────────
        assignments = db.query(VolunteerKidAssignment).filter_by(
            kid_id=kid.id, is_active=True
        ).all()
        vol_consistency = 1.0
        if assignments:
            vol_id    = assignments[0].volunteer_id
            vol_rsvps = db.query(SessionRsvp).filter_by(volunteer_id=vol_id).all()
            if vol_rsvps:
                confirmed       = sum(1 for r in vol_rsvps if r.status == RsvpStatus.confirmed)
                vol_consistency = confirmed / len(vol_rsvps)

        # ── Feature 8: Stuck flag ──────────────────────────────────────────
        # Same level for 3+ consecutive sessions = stuck
        if len(kid_logs) >= 3:
            last_3_levels = kid_logs["level_covered"].tail(3).values
            stuck_flag    = int(len(set(last_3_levels)) == 1 and last_3_levels[0] != "")
        else:
            stuck_flag = 0

        # ── Current level as numeric for ML ───────────────────────────────
        current_eng_level  = kid.english_level if hasattr(kid, 'english_level') else "letter"
        current_math_level = kid.math_level if hasattr(kid, 'math_level') else "pre_number"

        # Handle enum values
        if hasattr(current_eng_level, 'value'):
            current_eng_level = current_eng_level.value
        if hasattr(current_math_level, 'value'):
            current_math_level = current_math_level.value

        feature_rows.append({
            "kid_id":                    kid.id,
            "chapter_id":                kid.chapter_id,
            # Raw level strings
            "current_english_level":     current_eng_level,
            "current_math_level":        current_math_level,
            # Numeric representations for ML
            "current_english_level_num": level_to_num(current_eng_level, ENGLISH_LEVELS),
            "current_math_level_num":    level_to_num(current_math_level, MATH_LEVELS),
            # 8 engineered features
            "attendance_rate":           round(attendance_rate, 3),
            "avg_rating":                round(avg_rating, 3),
            "rating_trend":              round(rating_trend, 4),
            "consecutive_struggles":     consecutive_struggles,
            "levels_per_month":          round(levels_per_month, 3),
            "days_since_last_session":   days_since,
            "volunteer_consistency":     round(vol_consistency, 3),
            "stuck_flag":                stuck_flag,
        })

    return pd.DataFrame(feature_rows)
