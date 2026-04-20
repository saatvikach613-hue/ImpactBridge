"""
Model 2 — At-Risk Classifier
==============================
Algorithm : Random Forest + SMOTE
Target    : Binary — at_risk (1) or stable (0)
Evaluation: F1 score (not accuracy — class imbalance)

Why Random Forest?
Disengagement risk is driven by feature interactions.
A kid stuck at 'letter' level with a volunteer who keeps
missing sessions AND declining ratings is far higher risk
than any single signal alone. Random Forest captures these
non-linear interactions naturally.

Why SMOTE?
Most kids are NOT at risk (~25% at any given time).
Without SMOTE, the model learns to predict everyone as
stable and still gets 75% accuracy. SMOTE synthetically
oversamples the at-risk minority class during training.

Interview answer:
"I evaluated on F1 rather than accuracy because false negatives
— missing an at-risk kid — are more costly than false positives.
A coordinator can handle an extra check-in. A kid falling through
the cracks for weeks is much harder to recover."
"""

import numpy as np
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from app.ml.features import FEATURE_COLUMNS, ENGLISH_LEVELS, MATH_LEVELS

MODEL_PATH = "app/ml/saved/risk_model.joblib"


def _label_at_risk(features_df: pd.DataFrame) -> pd.Series:
    """
    Rule-based labeling for training data.
    A kid is at-risk if they meet 2+ of these conditions.
    Mirrors what an experienced U&I coordinator would flag.
    """
    risk_score = (
        (features_df["attendance_rate"]       < 0.5).astype(int) +
        (features_df["avg_rating"]            < 1.5).astype(int) +
        (features_df["consecutive_struggles"] >= 2).astype(int)  +
        (features_df["stuck_flag"]            == 1).astype(int)  +
        (features_df["days_since_last_session"] > 14).astype(int) +
        (features_df["rating_trend"]          < -0.3).astype(int) +
        (features_df["volunteer_consistency"] < 0.5).astype(int)
    )
    return (risk_score >= 2).astype(int)


def train_risk_model(features_df: pd.DataFrame) -> dict:
    """
    Train Random Forest classifier with SMOTE for class balancing.
    """
    os.makedirs("app/ml/saved", exist_ok=True)

    if len(features_df) < 20:
        return {"error": "Need at least 20 kids to train"}

    X = features_df[FEATURE_COLUMNS].fillna(0)
    y = _label_at_risk(features_df)

    at_risk_count = int(y.sum())
    stable_count  = int(len(y) - at_risk_count)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if at_risk_count >= 2 else None
    )

    # Apply SMOTE only if we have enough minority samples
    if at_risk_count >= 5:
        try:
            from imblearn.over_sampling import SMOTE
            smote = SMOTE(
                random_state=42,
                k_neighbors=min(3, at_risk_count - 1)
            )
            X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
        except Exception:
            X_train_bal, y_train_bal = X_train, y_train
    else:
        X_train_bal, y_train_bal = X_train, y_train

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_bal, y_train_bal)

    y_pred = model.predict(X_test)
    f1     = f1_score(y_test, y_pred, zero_division=0)
    report = classification_report(y_test, y_pred, zero_division=0)

    importance_df = pd.DataFrame({
        "feature":    FEATURE_COLUMNS,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    joblib.dump(model, MODEL_PATH)

    return {
        "f1_score":          round(f1, 3),
        "at_risk_in_data":   at_risk_count,
        "stable_in_data":    stable_count,
        "train_size":        len(X_train_bal),
        "test_size":         len(X_test),
        "top_feature":       importance_df.iloc[0]["feature"],
        "classification_report": report,
    }


def predict_risk(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict at-risk status per kid.
    Returns kid_id, at_risk, risk_score, risk_level, risk_reason.
    Also includes current level context for the coordinator alert.
    """
    X           = features_df[FEATURE_COLUMNS].fillna(0)
    predictions = features_df[["kid_id", "current_english_level", "current_math_level"]].copy()

    if not os.path.exists(MODEL_PATH):
        # Fallback: rule-based
        y_rule = _label_at_risk(features_df)
        predictions["at_risk"]    = y_rule.values.astype(bool)
        predictions["risk_score"] = 0.5
        predictions["risk_level"] = y_rule.map({1: "medium", 0: "low"})
        predictions["risk_reason"] = "rule-based fallback (model not trained yet)"
        return predictions

    model  = joblib.load(MODEL_PATH)
    y_pred = model.predict(X)
    try:
        class_1_idx = list(model.classes_).index(1)
        y_prob = model.predict_proba(X)[:, class_1_idx]
    except ValueError:
        y_prob = np.zeros(len(X))

    def risk_level(prob):
        if prob >= 0.7: return "high"
        if prob >= 0.4: return "medium"
        return "low"

    def risk_reason(row):
        reasons = []
        if row["attendance_rate"] < 0.5:
            reasons.append("low attendance")
        if row["consecutive_struggles"] >= 2:
            reasons.append(f"{int(row['consecutive_struggles'])} consecutive struggling sessions")
        if row["stuck_flag"] == 1:
            # Include the actual level they're stuck at
            eng_level  = row.get("current_english_level", "")
            math_level = row.get("current_math_level", "")
            if eng_level:
                reasons.append(f"stuck at {eng_level} level in English")
            if math_level:
                reasons.append(f"stuck at {math_level} level in Math")
        if row["rating_trend"] < -0.3:
            reasons.append("declining session ratings")
        if row["days_since_last_session"] > 14:
            reasons.append("hasn't attended in 2+ weeks")
        if row["volunteer_consistency"] < 0.5:
            reasons.append("volunteer attendance irregular")
        return ", ".join(reasons) if reasons else "borderline pattern"

    predictions["at_risk"]    = y_pred.astype(bool)
    predictions["risk_score"] = np.round(y_prob, 3)
    predictions["risk_level"] = [risk_level(p) for p in y_prob]
    predictions["risk_reason"] = [
        risk_reason({**features_df.iloc[i].to_dict(),
                     "current_english_level": features_df.iloc[i].get("current_english_level", ""),
                     "current_math_level":    features_df.iloc[i].get("current_math_level", "")})
        for i in range(len(features_df))
    ]

    return predictions
