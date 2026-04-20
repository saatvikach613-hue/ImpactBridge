"""
Model 3 — Resource Demand Forecaster
======================================
Maps predicted levels to specific U&I teaching resources.
This is the pipeline that closes the loop:
Session log → level tracking → ML prediction → resource need → donor wishlist

Resource catalogue is based on U&I Teach program materials:
- Foundational Literacy Program (letter → word → sentence → story)
- Foundational Numeracy Program (pre_number → number_recognition → basic_operations)
- Academic Support Program (advanced_operations → syllabus_aligned)
"""

import pandas as pd
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models import WishlistItem, Kid, WishlistStatus
from app.ml.features import ENGLISH_LEVELS, MATH_LEVELS

# ── U&I level-to-resource mapping ─────────────────────────────────────────────
# Based on U&I Teach program materials for each literacy/numeracy level

ENGLISH_RESOURCES = {
    "letter":   {"item": "Phonics & alphabet flashcard set",              "cost": 140},
    "word":     {"item": "Word building & reading cards",                  "cost": 160},
    "sentence": {"item": "Sentence construction workbook",                 "cost": 200},
    "story":    {"item": "Story books — Telugu & English (set of 5)",      "cost": 380},
    "advanced": {"item": "Advanced reading comprehension book",            "cost": 240},
}

MATH_RESOURCES = {
    "pre_number":           {"item": "Pre-number activity kit (counting, sorting)",  "cost": 280},
    "number_recognition":   {"item": "Number recognition workbook (1-100)",          "cost": 160},
    "basic_operations":     {"item": "Basic operations workbook (add/subtract)",     "cost": 200},
    "advanced_operations":  {"item": "Advanced math workbook (fractions, decimals)", "cost": 240},
    "syllabus_aligned":     {"item": "School syllabus math workbook",                "cost": 220},
}

SUPPLEMENTARY_RESOURCES = {
    "stuck":   {"item": "Math activity kit (hands-on learning)",          "cost": 280},
    "visual":  {"item": "Sketchbook + colour pencils (visual learner kit)", "cost": 180},
    "stories": {"item": "Story books — extra set",                         "cost": 320},
}


def forecast_resources(
    db: Session,
    progress_predictions: pd.DataFrame,
    features_df: pd.DataFrame,
    chapter_id: int
) -> list:
    """
    Takes progress predictions per kid and maps them to specific
    U&I teaching resources. Returns list of wishlist items to create.

    This is the full loop:
    predicted level → resource needed → wishlist item → donor funds it
    """
    if progress_predictions.empty:
        return []

    kids     = db.query(Kid).filter_by(chapter_id=chapter_id, is_active=True).all()
    kid_map  = {k.id: k for k in kids}
    need_date = date.today() + timedelta(weeks=4)
    wishlist_items = []

    for _, row in progress_predictions.iterrows():
        kid_id = int(row["kid_id"])
        kid    = kid_map.get(kid_id)
        if not kid:
            continue

        # Get current levels — handle enum values
        current_eng = kid.english_level
        current_math = kid.math_level
        if hasattr(current_eng, 'value'):
            current_eng = current_eng.value
        if hasattr(current_math, 'value'):
            current_math = current_math.value

        predicted_eng  = str(row.get("predicted_english_level", current_eng))
        predicted_math = str(row.get("predicted_math_level", current_math))

        # Only generate wishlist item if kid will advance to a new level
        for subject, current_level, predicted_level, resource_map in [
            ("english", current_eng,  predicted_eng,  ENGLISH_RESOURCES),
            ("math",    current_math, predicted_math, MATH_RESOURCES),
        ]:
            current_idx   = ENGLISH_LEVELS.index(current_level) if subject == "english" \
                            else MATH_LEVELS.index(current_level) if current_level in MATH_LEVELS else 0
            predicted_idx = ENGLISH_LEVELS.index(predicted_level) if subject == "english" \
                            else MATH_LEVELS.index(predicted_level) if predicted_level in MATH_LEVELS else 0

            # Kid will advance — they'll need the resource for their next level
            if predicted_idx > current_idx:
                resource = resource_map.get(predicted_level)
                if not resource:
                    continue

                # Don't duplicate existing open items
                existing = db.query(WishlistItem).filter_by(
                    kid_id=kid_id,
                    item_name=resource["item"],
                    status=WishlistStatus.open
                ).first()
                if not existing:
                    wishlist_items.append({
                        "kid_id":               kid_id,
                        "item_name":            resource["item"],
                        "description":          f"Predicted to reach {predicted_level} level in {subject} within 4 weeks",
                        "amount_needed":        resource["cost"],
                        "predicted_need_date":  need_date,
                        "ml_generated":         True,
                        "status":               WishlistStatus.open,
                    })

        # Supplementary resources for stuck kids
        feat_row = features_df[features_df["kid_id"] == kid_id]
        if not feat_row.empty and feat_row.iloc[0].get("stuck_flag", 0) == 1:
            resource = SUPPLEMENTARY_RESOURCES["stuck"]
            existing = db.query(WishlistItem).filter_by(
                kid_id=kid_id,
                item_name=resource["item"],
                status=WishlistStatus.open
            ).first()
            if not existing:
                wishlist_items.append({
                    "kid_id":               kid_id,
                    "item_name":            resource["item"],
                    "description":          f"Hands-on kit for kid stuck at current level",
                    "amount_needed":        resource["cost"],
                    "predicted_need_date":  need_date,
                    "ml_generated":         True,
                    "status":               WishlistStatus.open,
                })

    return wishlist_items


def populate_wishlist(db: Session, wishlist_items: list) -> int:
    """Insert ML-generated wishlist items into the database."""
    count = 0
    for item_data in wishlist_items:
        item = WishlistItem(**item_data)
        db.add(item)
        count += 1
    if count > 0:
        db.commit()
    return count
