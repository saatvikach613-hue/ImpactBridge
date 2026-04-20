"""
Email Service
==============
Handles all automated emails sent by ImpactBridge.

Four email types:
1. RSVP reminder      — sent to volunteers Thursday night
2. Coordinator alert  — sent Friday if volunteers unconfirmed
3. Donor impact card  — sent when funded item used in session
4. At-risk alert      — sent to coordinator when ML flags a kid

Uses SendGrid in production.
Falls back to console logging in development (no API key needed).

All emails are logged — you can see every email sent in the
automation_logs table (added in this phase).
"""

import os
import json
from datetime import datetime
from sqlalchemy.orm import Session


def _is_dev_mode() -> bool:
    """Return True if running locally without SendGrid key."""
    key = os.getenv("SENDGRID_API_KEY", "")
    return not key or key == "your-sendgrid-key"


def _log_email(db: Session, email_type: str, recipient: str, subject: str, status: str, body_preview: str = ""):
    """Log every email attempt to the database."""
    try:
        from app.models import AutomationLog
        log = AutomationLog(
            log_type=email_type,
            recipient=recipient,
            subject=subject,
            status=status,
            body_preview=body_preview[:200],
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    except Exception:
        pass  # Don't crash if logging fails


def send_rsvp_reminder(
    volunteer_email: str,
    volunteer_name: str,
    session_date: str,
    chapter_name: str,
    confirm_url: str,
    db: Session = None
) -> bool:
    """
    Sent every Thursday night to all volunteers.
    One tap to confirm or decline.
    Replaces the manual Friday/Saturday WhatsApp messages.
    """
    subject = f"U&I session this Sunday {session_date} — please confirm"
    body = f"""
Hi {volunteer_name},

This is a reminder for your U&I Teach session this Sunday ({session_date}) at {chapter_name}.

Please confirm your attendance by Friday evening:

✓ Confirm:  {confirm_url}?response=confirmed
✗ Decline:  {confirm_url}?response=declined

Your 2 students are counting on you. If you can't make it, please let us know early so we can arrange coverage.

Thank you for being part of the movement.
U&I {chapter_name} Team
    """.strip()

    if _is_dev_mode():
        print(f"\n[EMAIL - RSVP REMINDER]")
        print(f"  To:      {volunteer_email}")
        print(f"  Subject: {subject}")
        print(f"  Body preview: Hi {volunteer_name}, session on {session_date}...")
        if db:
            _log_email(db, "rsvp_reminder", volunteer_email, subject, "sent_dev", body[:200])
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg      = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@impactbridge.org"),
            to_emails=volunteer_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        success  = response.status_code in [200, 202]
        if db:
            _log_email(db, "rsvp_reminder", volunteer_email, subject,
                      "sent" if success else "failed", body[:200])
        return success
    except Exception as e:
        print(f"Email failed for {volunteer_email}: {e}")
        if db:
            _log_email(db, "rsvp_reminder", volunteer_email, subject, f"error: {str(e)[:100]}", "")
        return False


def send_coordinator_alert(
    coordinator_email: str,
    coordinator_name: str,
    session_date: str,
    chapter_name: str,
    unconfirmed_volunteers: list,
    db: Session = None
) -> bool:
    """
    Sent Friday morning if volunteers haven't confirmed.
    Gives coordinator 48 hours to arrange coverage.
    Replaces the manual Saturday scramble.
    """
    names_list = "\n".join([f"  - {v['name']} ({v['kids_count']} kids)" for v in unconfirmed_volunteers])
    subject    = f"[Action needed] {len(unconfirmed_volunteers)} volunteers unconfirmed for Sunday {session_date}"
    body = f"""
Hi {coordinator_name},

The following volunteers have not confirmed for Sunday's session ({session_date}) at {chapter_name}:

{names_list}

Total students at risk of no coverage: {sum(v['kids_count'] for v in unconfirmed_volunteers)}

Please follow up with them today so you have time to arrange coverage if needed.

This alert was sent automatically by ImpactBridge.
    """.strip()

    if _is_dev_mode():
        print(f"\n[EMAIL - COORDINATOR ALERT]")
        print(f"  To:      {coordinator_email}")
        print(f"  Subject: {subject}")
        print(f"  Unconfirmed: {[v['name'] for v in unconfirmed_volunteers]}")
        if db:
            _log_email(db, "coordinator_alert", coordinator_email, subject, "sent_dev", body[:200])
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg      = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@impactbridge.org"),
            to_emails=coordinator_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        success  = response.status_code in [200, 202]
        if db:
            _log_email(db, "coordinator_alert", coordinator_email, subject,
                      "sent" if success else "failed", body[:200])
        return success
    except Exception as e:
        print(f"Coordinator alert failed: {e}")
        return False


def send_donor_impact_card(
    donor_email: str,
    donor_name: str,
    item_name: str,
    kid_name: str,
    chapter_name: str,
    session_date: str,
    db: Session = None
) -> bool:
    """
    Sent when a funded item is used in a session.
    This is the loop that turns one-time donors into repeat donors.
    'Your ₹180 sketchbook was used by Arjun in his session today.'
    """
    subject = f"Your donation reached {kid_name} today"
    body = f"""
Hi {donor_name},

Something wonderful happened today.

The {item_name} you funded was used by {kid_name} in their U&I session at {chapter_name} on {session_date}.

Your contribution is directly helping a child learn and grow. Thank you for being part of this.

If you'd like to fund another resource for a child at {chapter_name}, visit our wishlist:
https://impactbridge.vercel.app/wishlist?chapter={chapter_name}

With gratitude,
The U&I {chapter_name} Team
    """.strip()

    if _is_dev_mode():
        print(f"\n[EMAIL - DONOR IMPACT CARD]")
        print(f"  To:      {donor_email}")
        print(f"  Subject: {subject}")
        print(f"  Item:    {item_name} → {kid_name}")
        if db:
            _log_email(db, "donor_impact", donor_email, subject, "sent_dev", body[:200])
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg      = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@impactbridge.org"),
            to_emails=donor_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        success  = response.status_code in [200, 202]
        if db:
            _log_email(db, "donor_impact", donor_email, subject,
                      "sent" if success else "failed", body[:200])
        return success
    except Exception as e:
        print(f"Donor impact card failed: {e}")
        return False


def send_at_risk_digest(
    coordinator_email: str,
    coordinator_name: str,
    chapter_name: str,
    at_risk_kids: list,
    db: Session = None
) -> bool:
    """
    Sent Monday morning after Sunday night ML pipeline runs.
    Shows coordinator which kids were flagged and why.
    """
    if not at_risk_kids:
        return True

    kids_list = "\n".join([
        f"  - {k['name']} | English: {k['english_level']} | Math: {k['math_level']} | Reason: {k['risk_reason']}"
        for k in at_risk_kids
    ])
    subject = f"[U&I {chapter_name}] {len(at_risk_kids)} kids flagged as at-risk this week"
    body = f"""
Hi {coordinator_name},

The ImpactBridge ML model ran last night and flagged the following kids as at-risk at {chapter_name}:

{kids_list}

These kids may need extra attention or a different learning approach this Sunday.
Consider reaching out to their volunteers before the session.

This digest was generated automatically every Sunday night.
View full dashboard: https://impactbridge.vercel.app/dashboard

U&I ImpactBridge
    """.strip()

    if _is_dev_mode():
        print(f"\n[EMAIL - AT-RISK DIGEST]")
        print(f"  To:      {coordinator_email}")
        print(f"  Subject: {subject}")
        print(f"  Kids:    {[k['name'] for k in at_risk_kids]}")
        if db:
            _log_email(db, "at_risk_digest", coordinator_email, subject, "sent_dev", body[:200])
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg      = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@impactbridge.org"),
            to_emails=coordinator_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        success  = response.status_code in [200, 202]
        if db:
            _log_email(db, "at_risk_digest", coordinator_email, subject,
                      "sent" if success else "failed", body[:200])
        return success
    except Exception as e:
        print(f"At-risk digest failed: {e}")
        return False
