"""Adoption metrics: the numbers the dashboard shows must be right and safe on empty data."""

from app.metrics import compute_adoption, safe_rate, BASELINE_LOG_COMPLETION


def test_safe_rate_handles_zero_denominator():
    assert safe_rate(3, 0) is None
    assert safe_rate(0, 0) is None
    assert safe_rate(1, 4) == 0.25


def test_empty_window_produces_no_nans_or_errors():
    snap = compute_adoption(
        window_weeks=8, sessions_in_window=0,
        expected_logs=0, actual_logs=0,
        rsvps_total=0, rsvps_responded=0, rsvps_confirmed=0,
        automated_emails_sent=0,
    )
    d = snap.to_dict()
    assert d["log_completion_rate"] is None
    assert d["log_completion_delta_pts"] is None
    assert d["rsvp_response_rate"] is None
    assert d["volunteer_minutes_saved_est"] == 0
    assert d["coordinator_manual_msgs_avoided_est"] == 0


def test_completion_rate_and_delta_vs_baseline():
    # 8 sessions × 100 kids expected = 800; 720 logged → 90%, +20 pts vs 70% baseline
    snap = compute_adoption(
        window_weeks=8, sessions_in_window=8,
        expected_logs=800, actual_logs=720,
        rsvps_total=400, rsvps_responded=340, rsvps_confirmed=300,
        automated_emails_sent=512,
    )
    assert snap.log_completion_rate == 0.9
    assert snap.log_completion_baseline == BASELINE_LOG_COMPLETION
    assert snap.log_completion_delta_pts == 20.0
    assert snap.rsvp_response_rate == 0.85
    assert snap.rsvp_confirmed_rate == 0.75


def test_time_saved_uses_15min_to_30s_delta():
    snap = compute_adoption(
        window_weeks=1, sessions_in_window=1,
        expected_logs=10, actual_logs=10,
        rsvps_total=0, rsvps_responded=0, rsvps_confirmed=0,
        automated_emails_sent=0,
    )
    # 10 logs × (15 − 0.5) min = 145 min
    assert snap.volunteer_minutes_saved_est == 145.0
    assert snap.coordinator_manual_msgs_avoided_est == 5


def test_completion_can_be_below_baseline():
    snap = compute_adoption(
        window_weeks=2, sessions_in_window=2,
        expected_logs=100, actual_logs=50,
        rsvps_total=0, rsvps_responded=0, rsvps_confirmed=0,
        automated_emails_sent=0,
    )
    assert snap.log_completion_rate == 0.5
    assert snap.log_completion_delta_pts == -20.0
