from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import WishlistItem, Donation, FundDrive, User, WishlistStatus
from app.schemas import (
    WishlistItemOut, WishlistItemCreate,
    DonationCreate, DonationOut, FundDriveOut
)
from app.auth import get_current_user, require_coordinator

router = APIRouter(tags=["wishlist & donations"])


# ── WISHLIST ──────────────────────────────────────────

@router.get("/wishlist", response_model=List[WishlistItemOut])
def get_wishlist(
    chapter_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Public endpoint — no auth required.
    This is what donors see when they land on the page.
    """
    query = db.query(WishlistItem)
    if status:
        query = query.filter(WishlistItem.status == status)
    else:
        query = query.filter(WishlistItem.status == WishlistStatus.open)
    return query.order_by(WishlistItem.created_at.desc()).all()


@router.post("/wishlist", response_model=WishlistItemOut)
def create_wishlist_item(
    item: WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    """Coordinator adds a specific item for a specific kid."""
    new_item = WishlistItem(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.delete("/wishlist/{item_id}")
def delete_wishlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    item = db.query(WishlistItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}


# ── DONATIONS ─────────────────────────────────────────

@router.post("/donate", response_model=DonationOut)
def make_donation(
    donation: DonationCreate,
    db: Session = Depends(get_db)
):
    """
    Public endpoint — no auth required.
    Donor funds a specific wishlist item.
    The impact card email is triggered by the automation pipeline (Phase 4).
    """
    item = db.query(WishlistItem).filter_by(id=donation.wishlist_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    if item.status == WishlistStatus.funded:
        raise HTTPException(status_code=400, detail="This item is already funded")

    new_donation = Donation(
        wishlist_item_id=donation.wishlist_item_id,
        amount=donation.amount,
        donor_name=donation.donor_name,
        donor_email=donation.donor_email,
    )
    db.add(new_donation)

    # Mark item as funded
    item.status = WishlistStatus.funded
    item.funded_at = datetime.utcnow()

    # Update fund drive raised amount
    if item.fund_drive_id:
        drive = db.query(FundDrive).filter_by(id=item.fund_drive_id).first()
        if drive:
            drive.raised_amount += donation.amount

    db.commit()
    db.refresh(new_donation)
    return new_donation


# ── FUND DRIVES ───────────────────────────────────────

@router.get("/fund-drives", response_model=List[FundDriveOut])
def get_fund_drives(
    chapter_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Public — donors and coordinators see live fund drive progress."""
    query = db.query(FundDrive).filter(FundDrive.is_active == True)
    if chapter_id:
        query = query.filter(FundDrive.chapter_id == chapter_id)
    return query.all()


@router.get("/fund-drives/{drive_id}", response_model=FundDriveOut)
def get_fund_drive(drive_id: int, db: Session = Depends(get_db)):
    drive = db.query(FundDrive).filter_by(id=drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Fund drive not found")
    return drive
