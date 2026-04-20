"""
Model 1 — Progress Trajectory Predictor
=========================================
Algorithm : Ridge Regression
Target    : Next level index per kid in 4 weeks
Evaluation: RMSE on 20% held-out test set

Predicts both English and Math level advancement.
Output is a level string — e.g. "word", "basic_operations"

Why Ridge?
Our features are correlated — a stuck kid also tends to have
low ratings and low attendance. Ridge handles multicollinearity
better than plain OLS and generalises on small datasets.

Interview answer:
"I used Ridge Regression to predict level advancement because
our feature set has correlated inputs — stuck flag correlates
with low ratings and low attendance. Ridge's L2 regularisation
prevents overfitting on a dataset of ~100 kids per chapter."
"""

import numpy as np
import pandas as pd
import joblib
import os
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from app.ml.features import FEATURE_COLUMNS, ENGLISH_LEVELS, MATH_LEVELS, num_to_level

MODEL_DIR = "app/ml/saved"


def train_progress_model(features_df: pd.DataFrame) -> dict:
    """
    Train Ridge Regression for level progression prediction.
    One model per subject (english, math).
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    if len(features_df) < 10:
        return {"error": "Need at least 10 kids to train"}

    X       = features_df[FEATURE_COLUMNS].fillna(0)
    results = {}

    for subject, target_col, level_list in [
        ("english", "current_english_level_num", ENGLISH_LEVELS),
        ("math",    "current_math_level_num",    MATH_LEVELS),
    ]:
        y = features_df[target_col].fillna(0)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s  = scaler.transform(X_test)

        model = Ridge(alpha=1.0)
        model.fit(X_train_s, y_train)

        y_pred = model.predict(X_test_s)
        rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
        r2     = model.score(X_test_s, y_test)

        joblib.dump(model,  f"{MODEL_DIR}/progress_model_{subject}.joblib")
        joblib.dump(scaler, f"{MODEL_DIR}/progress_scaler_{subject}.joblib")

        coef_df = pd.DataFrame({
            "feature":     FEATURE_COLUMNS,
            "coefficient": model.coef_
        }).sort_values("coefficient", ascending=False)

        results[subject] = {
            "rmse":         round(rmse, 3),
            "r2":           round(r2, 3),
            "train_size":   len(X_train),
            "test_size":    len(X_test),
            "top_feature":  coef_df.iloc[0]["feature"],
            "levels":       level_list,
        }

    return results


def predict_progress(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict which level each kid will be at in 4 weeks.
    Returns DataFrame with kid_id, predicted_english_level, predicted_math_level.
    """
    X           = features_df[FEATURE_COLUMNS].fillna(0)
    predictions = features_df[["kid_id"]].copy()

    for subject, current_col, level_list in [
        ("english", "current_english_level_num", ENGLISH_LEVELS),
        ("math",    "current_math_level_num",    MATH_LEVELS),
    ]:
        model_path  = f"{MODEL_DIR}/progress_model_{subject}.joblib"
        scaler_path = f"{MODEL_DIR}/progress_scaler_{subject}.joblib"

        if not os.path.exists(model_path):
            # Fallback: use velocity heuristic
            current_nums = features_df[current_col].fillna(0).values
            velocity     = features_df["levels_per_month"].fillna(0.3).values
            predicted    = np.clip(
                np.round(current_nums + velocity).astype(int),
                0, len(level_list) - 1
            )
            predictions[f"predicted_{subject}_level"] = [level_list[i] for i in predicted]
            predictions[f"predicted_{subject}_level_num"] = predicted
            continue

        model  = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        X_scaled  = scaler.transform(X)
        raw_pred  = model.predict(X_scaled)

        # Growth = predicted - current, clipped to realistic range (0-2 levels in 4 weeks)
        current   = features_df[current_col].fillna(0).values
        growth    = np.clip(raw_pred - current, 0, 2)
        predicted = np.clip(np.round(current + growth).astype(int), 0, len(level_list) - 1)

        predictions[f"predicted_{subject}_level"]     = [level_list[i] for i in predicted]
        predictions[f"predicted_{subject}_level_num"] = predicted

    return predictions
