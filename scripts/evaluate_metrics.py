import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, roc_auc_score, precision_score, recall_score
from imblearn.over_sampling import SMOTE

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.ml.features import build_features, FEATURE_COLUMNS
from app.ml.risk_model import _label_at_risk

def run_evaluation():
    db = SessionLocal()
    try:
        print("Fetching data from all chapters...")
        # build_features returns a DataFrame for a specific chapter or all chapters if chapter_id is None
        features_df = build_features(db, chapter_id=None)
        
        if features_df.empty:
            print("No data found in database. Seed it first!")
            return

        print(f"Dataset Size: {len(features_df)} kids")
        
        X = features_df[FEATURE_COLUMNS].fillna(0)
        y = _label_at_risk(features_df)
        
        at_risk_count = int(y.sum())
        stable_count = len(y) - at_risk_count
        print(f"Distribution: {at_risk_count} at-risk, {stable_count} stable ({at_risk_count/len(y):.1%} minority class)")

        # Split using Stratified K-Fold for more robust results on small data
        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=max(2, min(5, at_risk_count)), shuffle=True, random_state=42)
        
        f1s, precs, recs, aucs = [], [], [], []
        
        print(f"Running {skf.get_n_splits()}-Fold Cross Validation...")
        
        for i, (train_index, test_index) in enumerate(skf.split(X, y)):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            # Apply SMOTE to training fold
            n_at_risk_train = int(y_train.sum())
            if n_at_risk_train > 1:
                k = min(5, n_at_risk_train - 1)
                smote = SMOTE(random_state=42, k_neighbors=k)
                X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
            else:
                X_train_bal, y_train_bal = X_train, y_train
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100, 
                max_depth=6, 
                class_weight="balanced", 
                random_state=42
            )
            model.fit(X_train_bal, y_train_bal)
            
            # Predict
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1] if len(np.unique(y_test)) > 1 else np.zeros(len(y_test))

            # Metrics for this fold
            f1s.append(f1_score(y_test, y_pred, zero_division=0))
            precs.append(precision_score(y_test, y_pred, zero_division=0))
            recs.append(recall_score(y_test, y_pred, zero_division=0))
            try:
                if len(np.unique(y_test)) > 1:
                    aucs.append(roc_auc_score(y_test, y_prob))
            except ValueError:
                pass

        print("\n" + "="*40)
        print("      FINAL AGGREGATE METRICS (K-FOLD)")
        print("="*40)
        print(f"F1-Score:  {np.mean(f1s):.3f}")
        print(f"Precision: {np.mean(precs):.3f}")
        print(f"Recall:    {np.mean(recs):.3f}")
        print(f"ROC-AUC:   {np.mean(aucs) if aucs else 0.0:.3f}")
        print("-" * 40)
        print(f"Total Kids: {len(X)}")
        print(f"At-Risk Kids: {at_risk_count}")
        print("="*40)

    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation()
