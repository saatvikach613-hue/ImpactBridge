from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    coordinator = "coordinator"
    volunteer   = "volunteer"
    donor       = "donor"

class SessionRating(str, enum.Enum):
    struggling = "struggling"   # 😕
    okay       = "okay"         # 🙂
    nailed_it  = "nailed_it"    # ⭐

class WishlistStatus(str, enum.Enum):
    open    = "open"
    funded  = "funded"
    used    = "used"

class RsvpStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    declined  = "declined"

class RiskLevel(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


# ─────────────────────────────────────────────
# CHAPTER — U&I branch (Vizag-1, Vizag-2, etc.)
# ─────────────────────────────────────────────

class Chapter(Base):
    __tablename__ = "chapters"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)          # e.g. "Visakhapatnam - Sector 7"
    city       = Column(String(100), nullable=False)          # e.g. "Visakhapatnam"
    state      = Column(String(100), default="Andhra Pradesh")
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    users      = relationship("User", back_populates="chapter")
    kids       = relationship("Kid", back_populates="chapter")
    events     = relationship("SessionEvent", back_populates="chapter")
    fund_drives= relationship("FundDrive", back_populates="chapter")


# ─────────────────────────────────────────────
# USER — coordinator / volunteer / donor
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(150), nullable=False)
    email         = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False)
    chapter_id    = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    is_active     = Column(Boolean, default=True)
    phone         = Column(String(20), nullable=True)
    joined_date   = Column(Date, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    chapter       = relationship("Chapter", back_populates="users")
    assignments   = relationship("VolunteerKidAssignment", back_populates="volunteer")
    rsvps         = relationship("SessionRsvp", back_populates="volunteer")
    session_logs  = relationship("SessionLog", back_populates="volunteer")
    donations     = relationship("Donation", back_populates="donor")


# ─────────────────────────────────────────────
# KID — the heart of the platform
# ─────────────────────────────────────────────

class Kid(Base):
    __tablename__ = "kids"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    age             = Column(Integer, nullable=False)
    chapter_id      = Column(Integer, ForeignKey("chapters.id"), nullable=False)

    # academic progress — chapter numbers per subject
    math_chapter    = Column(Integer, default=1)
    english_chapter = Column(Integer, default=1)

    # what unlocks this kid — the insight Saatvika discovered about drawing
    learning_style  = Column(String(100), nullable=True)   # e.g. "visual", "hands-on"
    interests       = Column(String(255), nullable=True)   # e.g. "drawing, cricket"
    unlock_note     = Column(Text, nullable=True)          # e.g. "Bring drawing activity"

    is_active       = Column(Boolean, default=True)
    enrolled_date   = Column(Date, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    chapter         = relationship("Chapter", back_populates="kids")
    assignments     = relationship("VolunteerKidAssignment", back_populates="kid")
    session_logs    = relationship("SessionLog", back_populates="kid")
    progress_logs   = relationship("ProgressLog", back_populates="kid")
    ml_predictions  = relationship("MlPrediction", back_populates="kid")
    wishlist_items  = relationship("WishlistItem", back_populates="kid")


# ─────────────────────────────────────────────
# VOLUNTEER ↔ KID ASSIGNMENT
# Each volunteer is responsible for 4-5 kids
# ─────────────────────────────────────────────

class VolunteerKidAssignment(Base):
    __tablename__ = "volunteer_kid_assignments"

    id           = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kid_id       = Column(Integer, ForeignKey("kids.id"), nullable=False)
    assigned_date= Column(Date, nullable=True)
    is_active    = Column(Boolean, default=True)

    # relationships
    volunteer    = relationship("User", back_populates="assignments")
    kid          = relationship("Kid", back_populates="assignments")


# ─────────────────────────────────────────────
# SESSION EVENT — each Sunday session
# ─────────────────────────────────────────────

class SessionEvent(Base):
    __tablename__ = "session_events"

    id           = Column(Integer, primary_key=True, index=True)
    chapter_id   = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    start_time   = Column(String(10), default="09:00")
    end_time     = Column(String(10), default="11:00")
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    chapter      = relationship("Chapter", back_populates="events")
    rsvps        = relationship("SessionRsvp", back_populates="session")
    logs         = relationship("SessionLog", back_populates="session")


# ─────────────────────────────────────────────
# SESSION RSVP — the automation trigger
# Volunteers confirm 48hrs before, coordinator
# gets alerted if unconfirmed by Friday
# ─────────────────────────────────────────────

class SessionRsvp(Base):
    __tablename__ = "session_rsvps"

    id           = Column(Integer, primary_key=True, index=True)
    session_id   = Column(Integer, ForeignKey("session_events.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status       = Column(Enum(RsvpStatus), default=RsvpStatus.pending)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent= Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    session      = relationship("SessionEvent", back_populates="rsvps")
    volunteer    = relationship("User", back_populates="rsvps")


# ─────────────────────────────────────────────
# SESSION LOG — the 3-tap logger output
# One row per kid per session
# ─────────────────────────────────────────────

class SessionLog(Base):
    __tablename__ = "session_logs"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(Integer, ForeignKey("session_events.id"), nullable=False)
    volunteer_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    kid_id          = Column(Integer, ForeignKey("kids.id"), nullable=False)

    # the 3-tap input
    rating          = Column(Enum(SessionRating), nullable=False)

    # subject taught this session
    subject         = Column(String(50), nullable=False)   # "math" or "english"
    chapter_covered = Column(Integer, nullable=False)

    # optional volunteer note — feeds NLP later
    notes           = Column(Text, nullable=True)

    # auto-populated from note via NLP (Phase 3)
    detected_interest = Column(String(255), nullable=True)
    mood_flag         = Column(String(50), nullable=True)

    logged_at       = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    session         = relationship("SessionEvent", back_populates="logs")
    volunteer       = relationship("User", back_populates="session_logs")
    kid             = relationship("Kid", back_populates="session_logs")


# ─────────────────────────────────────────────
# PROGRESS LOG — weekly snapshot per kid
# Aggregated from session logs each Sunday night
# by the automation pipeline
# ─────────────────────────────────────────────

class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id                  = Column(Integer, primary_key=True, index=True)
    kid_id              = Column(Integer, ForeignKey("kids.id"), nullable=False)
    week_start          = Column(Date, nullable=False)

    math_chapter        = Column(Integer, nullable=True)
    english_chapter     = Column(Integer, nullable=True)
    avg_rating_math     = Column(Float, nullable=True)     # 1.0–3.0
    avg_rating_english  = Column(Float, nullable=True)
    sessions_attended   = Column(Integer, default=0)
    sessions_total      = Column(Integer, default=0)

    created_at          = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    kid                 = relationship("Kid", back_populates="progress_logs")


# ─────────────────────────────────────────────
# ML PREDICTION — output of the ML pipeline
# Runs every Sunday night via APScheduler
# ─────────────────────────────────────────────

class MlPrediction(Base):
    __tablename__ = "ml_predictions"

    id                      = Column(Integer, primary_key=True, index=True)
    kid_id                  = Column(Integer, ForeignKey("kids.id"), nullable=False)

    # Model 1 — Ridge regression output
    predicted_math_chapter  = Column(Float, nullable=True)   # in 4 weeks
    predicted_eng_chapter   = Column(Float, nullable=True)

    # Model 2 — Random Forest classifier output
    at_risk                 = Column(Boolean, default=False)
    risk_level              = Column(Enum(RiskLevel), default=RiskLevel.low)
    risk_score              = Column(Float, nullable=True)   # 0.0–1.0 probability
    risk_reason             = Column(String(255), nullable=True)  # e.g. "3 declining sessions"

    # metadata
    model_version           = Column(String(20), default="1.0")
    predicted_at            = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    kid                     = relationship("Kid", back_populates="ml_predictions")


# ─────────────────────────────────────────────
# FUND DRIVE — chapter-level fundraiser
# ─────────────────────────────────────────────

class FundDrive(Base):
    __tablename__ = "fund_drives"

    id            = Column(Integer, primary_key=True, index=True)
    chapter_id    = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    title         = Column(String(200), nullable=False)
    goal_amount   = Column(Float, nullable=False)
    raised_amount = Column(Float, default=0.0)
    start_date    = Column(Date, nullable=False)
    end_date      = Column(Date, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    chapter       = relationship("Chapter", back_populates="fund_drives")
    donations     = relationship("Donation", back_populates="fund_drive")
    wishlist_items= relationship("WishlistItem", back_populates="fund_drive")


# ─────────────────────────────────────────────
# WISHLIST ITEM — specific resource for a kid
# Populated by coordinator OR auto by ML pipeline
# ─────────────────────────────────────────────

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id              = Column(Integer, primary_key=True, index=True)
    kid_id          = Column(Integer, ForeignKey("kids.id"), nullable=True)   # null = chapter-level
    fund_drive_id   = Column(Integer, ForeignKey("fund_drives.id"), nullable=True)

    item_name       = Column(String(200), nullable=False)    # e.g. "Sketchbook + colour pencils"
    description     = Column(Text, nullable=True)
    amount_needed   = Column(Float, nullable=False)          # in ₹
    status          = Column(Enum(WishlistStatus), default=WishlistStatus.open)

    # auto-generated by ML pipeline?
    ml_generated    = Column(Boolean, default=False)
    predicted_need_date = Column(Date, nullable=True)        # when kid will need it

    funded_at       = Column(DateTime(timezone=True), nullable=True)
    used_in_session = Column(Integer, ForeignKey("session_events.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    kid             = relationship("Kid", back_populates="wishlist_items")
    fund_drive      = relationship("FundDrive", back_populates="wishlist_items")
    donations       = relationship("Donation", back_populates="wishlist_item")


# ─────────────────────────────────────────────
# DONATION — donor funds a wishlist item
# ─────────────────────────────────────────────

class Donation(Base):
    __tablename__ = "donations"

    id              = Column(Integer, primary_key=True, index=True)
    donor_id        = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = anonymous
    wishlist_item_id= Column(Integer, ForeignKey("wishlist_items.id"), nullable=True)
    fund_drive_id   = Column(Integer, ForeignKey("fund_drives.id"), nullable=True)

    amount          = Column(Float, nullable=False)
    donor_name      = Column(String(150), nullable=True)     # for anonymous donors
    donor_email     = Column(String(200), nullable=True)     # for impact card emails
    payment_ref     = Column(String(100), nullable=True)
    impact_card_sent= Column(Boolean, default=False)
    donated_at      = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    donor           = relationship("User", back_populates="donations")
    wishlist_item   = relationship("WishlistItem", back_populates="donations")
    fund_drive      = relationship("FundDrive", back_populates="donations")
