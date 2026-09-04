"""
Config
======
Single place for environment-driven settings used across the backend.
Everything here has a safe local default so `uvicorn app.main:app` works
with just a DATABASE_URL.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _clean_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


# Public URL of the deployed React frontend.
# Used in every email link (RSVP confirm, dashboard, wishlist) and for CORS.
FRONTEND_URL: str = _clean_url(
    os.getenv("FRONTEND_URL", "https://impact-bridge-saatvika.vercel.app")
)

# Extra origins allowed to call the API (comma separated), e.g. Vercel preview URLs.
EXTRA_CORS_ORIGINS: list[str] = [
    _clean_url(o) for o in os.getenv("EXTRA_CORS_ORIGINS", "").split(",") if o.strip()
]

# Shared secret that lets an external scheduler (GitHub Actions cron) hit the
# /automation/trigger/* endpoints without a coordinator login.
# If unset, only logged-in coordinators can trigger jobs.
AUTOMATION_API_KEY: str = os.getenv("AUTOMATION_API_KEY", "")

# Secret used to sign one-tap RSVP links in emails. Falls back to SECRET_KEY.
RSVP_SIGNING_KEY: str = os.getenv("RSVP_SIGNING_KEY") or os.getenv("SECRET_KEY", "dev-secret")

# Optional: Anthropic key for the plain-English at-risk digest.
# If unset, the digest falls back to the plain bullet list.
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
