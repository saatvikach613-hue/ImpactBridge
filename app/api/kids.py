from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Kid, VolunteerKidAssignment, MlPrediction, User
from app.schemas import KidOut, KidUpdate, MlPredictionOut
from app.auth import get_current_user, require_coordinator

router = APIRouter(prefix="/kids", tags=["kids"])


@router.get("/", response_model=List[KidOut])
def get_kids(
    chapter_id: Optional[int] = None,
    at_risk: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Coordinator: sees all kids, can filter by chapter or at_risk.
    Volunteer: sees only their assigned kids.
    """
    if current_user.role == "coordinator":
        query = db.query(Kid).filter(Kid.is_active == True)
        if chapter_id:
            query = query.filter(Kid.chapter_id == chapter_id)
        if at_risk is not None:
            at_risk_ids = [
                p.kid_id for p in db.query(MlPrediction)
                .filter(MlPrediction.at_risk == at_risk).all()
            ]
            query = query.filter(Kid.id.in_(at_risk_ids))
        return query.all()
    else:
        # Volunteer sees only their assigned kids
        assigned_ids = [
            a.kid_id for a in db.query(VolunteerKidAssignment)
            .filter_by(volunteer_id=current_user.id, is_active=True).all()
        ]
        return db.query(Kid).filter(
            Kid.id.in_(assigned_ids),
            Kid.is_active == True
        ).all()


@router.get("/{kid_id}", response_model=KidOut)
def get_kid(
    kid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kid = db.query(Kid).filter_by(id=kid_id, is_active=True).first()
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")

    # Volunteers can only see their assigned kids
    if current_user.role == "volunteer":
        assigned = db.query(VolunteerKidAssignment).filter_by(
            volunteer_id=current_user.id, kid_id=kid_id, is_active=True
        ).first()
        if not assigned:
            raise HTTPException(status_code=403, detail="Not your assigned kid")
    return kid


@router.patch("/{kid_id}", response_model=KidOut)
def update_kid(
    kid_id: int,
    updates: KidUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Volunteer updates learning style, interests, unlock note.
    Coordinator can update everything.
    """
    kid = db.query(Kid).filter_by(id=kid_id, is_active=True).first()
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")

    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(kid, field, value)

    db.commit()
    db.refresh(kid)
    return kid


@router.get("/{kid_id}/prediction", response_model=MlPredictionOut)
def get_kid_prediction(
    kid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Latest ML prediction for this kid."""
    prediction = db.query(MlPrediction).filter_by(kid_id=kid_id)\
        .order_by(MlPrediction.predicted_at.desc()).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction yet for this kid")
    return prediction
