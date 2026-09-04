"""
RSVP link signing
=================
Volunteers confirm attendance with ONE tap from the Thursday email,
without logging in. To stop anyone from confirming/declining on
someone else's behalf, every link carries an HMAC token bound to
(session_id, volunteer_id).

Pure functions, no DB, so they are trivially unit-testable.
"""

import hmac
import hashlib
from app.config import RSVP_SIGNING_KEY, FRONTEND_URL


def sign_rsvp(session_id: int, volunteer_id: int) -> str:
    """Return a short, URL-safe HMAC token for this session/volunteer pair."""
    msg = f"{session_id}:{volunteer_id}".encode()
    return hmac.new(RSVP_SIGNING_KEY.encode(), msg, hashlib.sha256).hexdigest()[:32]


def verify_rsvp(session_id: int, volunteer_id: int, token: str) -> bool:
    """Constant-time comparison so the token can't be brute-forced by timing."""
    if not token:
        return False
    expected = sign_rsvp(session_id, volunteer_id)
    return hmac.compare_digest(expected, token)


def build_rsvp_url(session_id: int, volunteer_id: int) -> str:
    """Base URL the email uses; the email appends &response=confirmed|declined."""
    token = sign_rsvp(session_id, volunteer_id)
    return f"{FRONTEND_URL}/rsvp/{session_id}/{volunteer_id}?token={token}"
