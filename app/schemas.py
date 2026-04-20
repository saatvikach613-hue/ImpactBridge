from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from app.models import UserRole, SessionRating, WishlistStatus, RsvpStatus, RiskLevel


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    chapter_id: Optional[int]


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    chapter_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# CHAPTER
# ─────────────────────────────────────────────

class ChapterOut(BaseModel):
    id: int
    name: str
    city: str
    state: str
    is_active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# KID
# ─────────────────────────────────────────────

class KidOut(BaseModel):
    id: int
    name: str
    age: int
    chapter_id: int
    math_level: str
    english_level: str
    learning_style: Optional[str]
    interests: Optional[str]
    unlock_note: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class KidUpdate(BaseModel):
    learning_style: Optional[str] = None
    interests: Optional[str] = None
    unlock_note: Optional[str] = None
    math_level: Optional[str] = None
    english_level: Optional[str] = None


# ─────────────────────────────────────────────
# SESSION LOG — the 3-tap logger
# ─────────────────────────────────────────────

class SessionLogCreate(BaseModel):
    kid_id: int
    rating: SessionRating
    subject: str
    chapter_covered: int
    notes: Optional[str] = None

class SessionLogOut(BaseModel):
    id: int
    kid_id: int
    session_id: int
    rating: SessionRating
    subject: str
    chapter_covered: int
    notes: Optional[str]
    logged_at: datetime

    class Config:
        from_attributes = True

class BulkSessionLogCreate(BaseModel):
    session_id: int
    logs: List[SessionLogCreate]


# ─────────────────────────────────────────────
# SESSION EVENT
# ─────────────────────────────────────────────

class SessionEventOut(BaseModel):
    id: int
    chapter_id: int
    session_date: date
    start_time: str
    end_time: str

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# RSVP
# ─────────────────────────────────────────────

class RsvpUpdate(BaseModel):
    status: RsvpStatus

class RsvpOut(BaseModel):
    id: int
    session_id: int
    volunteer_id: int
    status: RsvpStatus
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ML PREDICTION
# ─────────────────────────────────────────────

class MlPredictionOut(BaseModel):
    kid_id: int
    at_risk: bool
    risk_level: RiskLevel
    risk_score: Optional[float]
    risk_reason: Optional[str]
    predicted_math_level: Optional[str]
    predicted_eng_level: Optional[str]
    predicted_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────

class WishlistItemOut(BaseModel):
    id: int
    kid_id: Optional[int]
    item_name: str
    description: Optional[str]
    amount_needed: float
    status: WishlistStatus
    ml_generated: bool
    fund_drive_id: Optional[int]

    class Config:
        from_attributes = True

class WishlistItemCreate(BaseModel):
    kid_id: Optional[int] = None
    fund_drive_id: Optional[int] = None
    item_name: str
    description: Optional[str] = None
    amount_needed: float


# ─────────────────────────────────────────────
# DONATION
# ─────────────────────────────────────────────

class DonationCreate(BaseModel):
    wishlist_item_id: int
    amount: float
    donor_name: Optional[str] = None
    donor_email: Optional[str] = None

class DonationOut(BaseModel):
    id: int
    wishlist_item_id: Optional[int]
    amount: float
    donor_name: Optional[str]
    donated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# FUND DRIVE
# ─────────────────────────────────────────────

class FundDriveOut(BaseModel):
    id: int
    chapter_id: int
    title: str
    goal_amount: float
    raised_amount: float
    start_date: date
    end_date: date
    is_active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# COORDINATOR DASHBOARD — all in one response
# ─────────────────────────────────────────────

class DashboardAlert(BaseModel):
    type: str        # "at_risk_kid" | "inactive_volunteer" | "unfunded_wishlist"
    message: str
    severity: str    # "high" | "medium" | "low"
    ref_id: Optional[int] = None

class DashboardStats(BaseModel):
    total_kids: int
    total_volunteers: int
    sessions_this_week: int
    at_risk_kids: int
    fund_drive_pct: Optional[float]
    unfunded_wishlist_count: int

class DashboardResponse(BaseModel):
    stats: DashboardStats
    alerts: List[DashboardAlert]
    at_risk_kids: List[KidOut]
    recent_sessions: List[SessionEventOut]
