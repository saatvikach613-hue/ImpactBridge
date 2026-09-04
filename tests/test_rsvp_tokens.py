"""One-tap RSVP links must be unforgeable and bound to one (session, volunteer)."""

from app.automation.rsvp_tokens import sign_rsvp, verify_rsvp, build_rsvp_url


def test_roundtrip_valid_token():
    tok = sign_rsvp(12, 34)
    assert verify_rsvp(12, 34, tok)


def test_token_is_bound_to_session_and_volunteer():
    tok = sign_rsvp(12, 34)
    assert not verify_rsvp(13, 34, tok), "different session must not validate"
    assert not verify_rsvp(12, 35, tok), "different volunteer must not validate"


def test_tampered_or_empty_token_rejected():
    tok = sign_rsvp(1, 2)
    assert not verify_rsvp(1, 2, tok[:-1] + ("0" if tok[-1] != "0" else "1"))
    assert not verify_rsvp(1, 2, "")
    assert not verify_rsvp(1, 2, None)


def test_token_is_deterministic_and_url_safe():
    a, b = sign_rsvp(7, 8), sign_rsvp(7, 8)
    assert a == b
    assert len(a) == 32
    assert all(c in "0123456789abcdef" for c in a)


def test_build_url_contains_ids_and_token():
    url = build_rsvp_url(5, 9)
    assert "/rsvp/5/9?token=" in url
    assert url.startswith("http")
    tok = url.split("token=")[1]
    assert verify_rsvp(5, 9, tok)
