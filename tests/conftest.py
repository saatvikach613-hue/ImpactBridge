"""
Test config: make `app` importable and keep tests DB-free.
Pure-logic modules (rsvp_tokens, metrics, digest_writer) don't touch the
database, so no PostgreSQL is needed to run `pytest`.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stable signing key so token tests are deterministic
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RSVP_SIGNING_KEY", "test-signing-key")
os.environ.setdefault("FRONTEND_URL", "https://impactbridge-saatvika.vercel.app")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
