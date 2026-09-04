"""
Adoption metrics
================
The question a coordinator (or a hiring manager) actually asks about an
automation is not "does it run" but "is anyone using it, and did it help".

Pure functions here; the DB gathering lives in api/dashboard.py so this
module is unit-testable without a database.

Baselines come from what was observed at U&I Visakhapatnam before ImpactBridge:
- session sheets completed ~70% of the time
- ~5 manual WhatsApp confirmations per volunteer-session week
- ~15 minutes per volunteer to fill the old sheet
"""

from dataclasses import dataclass, asdict

BASELINE_LOG_COMPLETION      = 0.70   # share of expected session logs actually filled, pre-ImpactBridge
BASELINE_MANUAL_MSGS_PER_WEEK = 5     # WhatsApp confirmations the coordinator sent by hand each week
BASELINE_LOG_MINUTES         = 15.0   # old sheet
CURRENT_LOG_MINUTES          = 0.5    # 3-tap logger (~30 seconds)


def safe_rate(numerator: int, denominator: int):
    return round(numerator / denominator, 3) if denominator else None


@dataclass
class AdoptionSnapshot:
    window_weeks: int
    sessions_in_window: int

    # Logging adoption
    expected_logs: int
    actual_logs: int
    log_completion_rate: float | None
    log_completion_baseline: float
    log_completion_delta_pts: float | None      # percentage points vs baseline

    # RSVP adoption
    rsvps_total: int
    rsvps_responded: int
    rsvp_response_rate: float | None
    rsvps_confirmed: int
    rsvp_confirmed_rate: float | None

    # Time & effort saved (estimates, clearly labelled)
    volunteer_minutes_saved_est: float
    coordinator_manual_msgs_avoided_est: int
    automated_emails_sent: int

    def to_dict(self) -> dict:
        return asdict(self)


def compute_adoption(
    *,
    window_weeks: int,
    sessions_in_window: int,
    expected_logs: int,
    actual_logs: int,
    rsvps_total: int,
    rsvps_responded: int,
    rsvps_confirmed: int,
    automated_emails_sent: int,
) -> AdoptionSnapshot:
    completion = safe_rate(actual_logs, expected_logs)
    delta = round((completion - BASELINE_LOG_COMPLETION) * 100, 1) if completion is not None else None

    return AdoptionSnapshot(
        window_weeks=window_weeks,
        sessions_in_window=sessions_in_window,
        expected_logs=expected_logs,
        actual_logs=actual_logs,
        log_completion_rate=completion,
        log_completion_baseline=BASELINE_LOG_COMPLETION,
        log_completion_delta_pts=delta,
        rsvps_total=rsvps_total,
        rsvps_responded=rsvps_responded,
        rsvp_response_rate=safe_rate(rsvps_responded, rsvps_total),
        rsvps_confirmed=rsvps_confirmed,
        rsvp_confirmed_rate=safe_rate(rsvps_confirmed, rsvps_total),
        volunteer_minutes_saved_est=round(actual_logs * (BASELINE_LOG_MINUTES - CURRENT_LOG_MINUTES), 1),
        coordinator_manual_msgs_avoided_est=sessions_in_window * BASELINE_MANUAL_MSGS_PER_WEEK,
        automated_emails_sent=automated_emails_sent,
    )
