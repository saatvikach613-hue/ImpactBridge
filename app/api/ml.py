from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserRole, MlPrediction
from app.schemas import MlPredictionOut
from app.ml.pipeline import train_all

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.post("/train", summary="Train ML models and forecast resource demands")
def train_models(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.coordinator:
        raise HTTPException(status_code=403, detail="Coordinator only")
    
    try:
        results = train_all(retrain=True)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions", response_model=List[MlPredictionOut], summary="Get the latest ML predictions for kids")
def get_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.coordinator:
        raise HTTPException(status_code=403, detail="Coordinator only")
        
    predictions = db.query(MlPrediction).all()
    return predictions
