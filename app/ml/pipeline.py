"""
ML Pipeline Runner
===================
Orchestrates all three models in sequence.
Called by APScheduler every Sunday night.
Can also be triggered manually via POST /ml/train or /ml/run-pipeline.

Order:
1. Build features from session logs
2. Train or load progress model → predict levels in 4 weeks
3. Train or load risk model → classify at-risk kids
4. Forecast resource demand → populate wishlist
5. Write all predictions to ml_predictions table
"""

import os
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models import MlPrediction, Kid, RiskLevel, Chapter
from app.ml.features import build_features
from app.ml.progress_model import train_progress_model, predict_progress
from app.ml.risk_model import train_risk_model, predict_risk
from app.ml.demand_forecast import forecast_resources, populate_wishlist


def run_pipeline(chapter_id: int = None, retrain: bool = False) -> dict:
    """
    Full ML pipeline. Runs for one chapter or all chapters.
    Called by APScheduler every Sunday night at 23:00.
    """
    db      = SessionLocal()
    results = {}

    try:
        chapters = db.query(Chapter).filter_by(is_active=True).all()
        if chapter_id:
            chapters = [c for c in chapters if c.id == chapter_id]

        model_exists = os.path.exists("app/ml/saved/risk_model.joblib")

        for chapter in chapters:
            print(f"\nRunning ML pipeline: {chapter.name}")
            chapter_results = {}

            # ── Step 1: Feature engineering ───────────────────
            print("  Building features...")
            features_df = build_features(db, chapter_id=chapter.id)

            if features_df.empty:
                print(f"  No session data for {chapter.name} — skipping")
                continue

            print(f"  Features built for {len(features_df)} kids")

            # ── Step 2: Train models if needed ────────────────
            if retrain or not model_exists:
                print("  Training progress model (Ridge Regression)...")
                prog_results = train_progress_model(features_df)
                print(f"  English RMSE: {prog_results.get('english', {}).get('rmse', 'N/A')}")
                print(f"  Math RMSE:    {prog_results.get('math', {}).get('rmse', 'N/A')}")

                print("  Training risk model (Random Forest + SMOTE)...")
                risk_results = train_risk_model(features_df)
                print(f"  F1 score:     {risk_results.get('f1_score', 'N/A')}")
                print(f"  At-risk kids: {risk_results.get('at_risk_in_data', 0)}")
                print(f"  Top feature:  {risk_results.get('top_feature', 'N/A')}")

                chapter_results["training"] = {
                    "progress": prog_results,
                    "risk":     risk_results,
                }
                model_exists = True

            # ── Step 3: Run predictions ────────────────────────
            print("  Running progress predictions...")
            progress_preds = predict_progress(features_df)

            print("  Running risk predictions...")
            risk_preds = predict_risk(features_df)

            # ── Step 4: Write to ml_predictions table ─────────
            print("  Writing predictions to database...")
            written = 0

            for _, row in features_df.iterrows():
                kid_id   = int(row["kid_id"])
                prog_row = progress_preds[progress_preds["kid_id"] == kid_id]
                risk_row = risk_preds[risk_preds["kid_id"] == kid_id]

                if prog_row.empty or risk_row.empty:
                    continue

                prog = prog_row.iloc[0]
                risk = risk_row.iloc[0]

                level_map = {
                    "low":    RiskLevel.low,
                    "medium": RiskLevel.medium,
                    "high":   RiskLevel.high
                }
                risk_level_enum = level_map.get(str(risk["risk_level"]), RiskLevel.low)

                prediction = MlPrediction(
                    kid_id=kid_id,
                    predicted_math_level=str(prog.get("predicted_math_level", "basic_operations")),
                    predicted_eng_level=str(prog.get("predicted_english_level", "letter")),
                    at_risk=bool(risk["at_risk"]),
                    risk_level=risk_level_enum,
                    risk_score=float(risk["risk_score"]),
                    risk_reason=str(risk["risk_reason"]),
                    model_version="2.0",
                    predicted_at=datetime.utcnow(),
                )
                db.add(prediction)
                written += 1

            db.commit()
            print(f"  Written {written} predictions")

            # ── Step 5: Resource demand forecasting ───────────
            print("  Forecasting resource demand...")
            wishlist_items = forecast_resources(
                db, progress_preds, features_df, chapter.id
            )
            added = populate_wishlist(db, wishlist_items)
            print(f"  Added {added} items to wishlist")

            chapter_results["predictions"] = {
                "kids_processed":       written,
                "at_risk_flagged":      int(risk_preds["at_risk"].sum()),
                "wishlist_items_added": added,
            }
            results[chapter.name] = chapter_results

        print("\nML pipeline complete.")
        return {"status": "success", "results": results}

    except Exception as e:
        db.rollback()
        print(f"Pipeline failed: {e}")
        raise
    finally:
        db.close()


def train_all(retrain: bool = True) -> dict:
    """Train all models from scratch. Call this once after seeding."""
    return run_pipeline(retrain=retrain)


if __name__ == "__main__":
    print("Running ImpactBridge ML pipeline manually...")
    result = run_pipeline(retrain=True)
    print(result)
