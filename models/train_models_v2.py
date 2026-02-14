"""
Updated ML Model Training - Fraud Detection & Anomaly Detection
Uses dataset matching current database schema
Includes hyperparameter tuning for better accuracy
"""

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, f1_score, accuracy_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import xgboost as xgb

# Optional visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Note: matplotlib/seaborn not available, skipping plots")

def train_fraud_model_v2():
    """
    Train improved XGBoost fraud detection model
    """
    print("="*70)
    print("FRAUD DETECTION MODEL TRAINING (UPDATED)")
    print("="*70)
    
    # Load updated dataset
    print("\n[1/6] Loading dataset...")
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fraud_dataset_v2.csv')
    df = pd.read_csv(dataset_path)
    
    # Select features (matching extract_features_from_claim)
    feature_columns = [
        'claim_amount',
        'claim_amount_ratio',
        'days_since_policy_start',
        'waiting_period_violation',
        'num_previous_claims',
        'days_since_last_claim',
        'blacklisted_hospital',
        'non_network_hospital',
        'room_rent_exceeded',
        'diagnosis_treatment_mismatch',
        'duplicate_invoice_flag',
        'late_submission_flag',
        'hospital_risk_score',
        'rapid_claim_flag',
        'claim_frequency_risk'
    ]
    
    X = df[feature_columns]
    y = df['fraud_label']
    
    print(f"   Dataset shape: {X.shape}")
    print(f"   Features: {len(feature_columns)}")
    print(f"   Fraudulent claims: {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"   Legitimate claims: {len(y)-y.sum()} ({(1-y.mean())*100:.1f}%)")
    
    # Train/test split with stratification
    print("\n[2/6] Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"   Train: {len(X_train)} samples")
    print(f"   Test: {len(X_test)} samples")
    
    # Calculate scale_pos_weight for class imbalance
    scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    print(f"   Scale pos weight: {scale_pos_weight:.2f}")
    
    # Hyperparameter tuning
    print("\n[3/6] Hyperparameter tuning with GridSearchCV...")
    
    param_grid = {
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.15],
        'n_estimators': [100, 150, 200],
        'min_child_weight': [1, 3, 5],
        'subsample': [0.8, 0.9],
        'colsample_bytree': [0.8, 0.9]
    }
    
    xgb_model = xgb.XGBClassifier(
        objective='binary:logistic',
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    # Use GridSearchCV with 5-fold CV
    grid_search = GridSearchCV(
        estimator=xgb_model,
        param_grid=param_grid,
        cv=5,
        scoring='f1',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"\n   Best parameters: {grid_search.best_params_}")
    print(f"   Best F1 score: {grid_search.best_score_:.4f}")
    
    # Get best model
    best_model = grid_search.best_estimator_
    
    # Evaluate on test set
    print("\n[4/6] Evaluating on test set...")
    y_pred = best_model.predict(X_test)
    y_pred_proba = best_model.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n   Test Set Performance:")
    print(f"   - Accuracy: {accuracy:.4f}")
    print(f"   - F1 Score: {f1:.4f}")
    print(f"   - ROC AUC: {roc_auc:.4f}")
    
    print(f"\n   Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraudulent']))
    
    print(f"\n   Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"   TN: {cm[0,0]}, FP: {cm[0,1]}")
    print(f"   FN: {cm[1,0]}, TP: {cm[1,1]}")
    
    # Feature importance
    print("\n[5/6] Feature importance:")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(10).iterrows():
        print(f"   {row['feature']:<35} {row['importance']:.4f}")
    
    # Save model
    print("\n[6/6] Saving model...")
    model_dir = os.path.dirname(__file__)
    
    # Save XGBoost model
    model_path = os.path.join(model_dir, 'fraud_model_v2.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"   ✓ Model saved: {model_path}")
    
    # Save metadata
    metadata = {
        'model_version': '2.0',
        'training_date': pd.Timestamp.now().isoformat(),
        'features': feature_columns,
        'n_train_samples': len(X_train),
        'n_test_samples': len(X_test),
        'test_accuracy': float(accuracy),
        'test_f1_score': float(f1),
        'test_roc_auc': float(roc_auc),
        'best_params': grid_search.best_params_,
        'feature_importance': feature_importance.to_dict('records')
    }
    
    metadata_path = os.path.join(model_dir, 'fraud_model_v2_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✓ Metadata saved: {metadata_path}")
    
    print("\n" + "="*70)
    print("FRAUD MODEL TRAINING COMPLETE!")
    print("="*70)
    
    return best_model, feature_importance


def train_anomaly_model_v2():
    """
    Train improved Isolation Forest anomaly detection model
    """
    print("\n" + "="*70)
    print("ANOMALY DETECTION MODEL TRAINING (UPDATED)")
    print("="*70)
    
    # Load dataset
    print("\n[1/5] Loading dataset...")
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fraud_dataset_v2.csv')
    df = pd.read_csv(dataset_path)
    
    # Use only legitimate claims for anomaly training
    legitimate_claims = df[df['fraud_label'] == 0]
    
    # Select features
    feature_columns = [
        'claim_amount',
        'claim_amount_ratio',
        'days_since_policy_start',
        'num_previous_claims',
        'days_since_last_claim',
        'hospital_risk_score',
        'claim_frequency_risk'
    ]
    
    X = legitimate_claims[feature_columns]
    
    print(f"   Training samples (legitimate only): {len(X)}")
    print(f"   Features: {len(feature_columns)}")
    
    # Scale features (important for Isolation Forest)
    print("\n[2/5] Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Isolation Forest with tuned parameters
    print("\n[3/5] Training Isolation Forest...")
    
    # Estimate contamination based on expected anomaly rate
    contamination = 0.05  # Expect 5% anomalies even in legitimate claims
    
    anomaly_model = IsolationForest(
        contamination=contamination,
        n_estimators=150,
        max_samples=256,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    anomaly_model.fit(X_scaled)
    
    # Evaluate on full dataset
    print("\n[4/5] Evaluating on full dataset...")
    X_full = df[feature_columns]
    X_full_scaled = scaler.transform(X_full)
    
    # Predict anomalies (-1 = anomaly, 1 = normal)
    predictions = anomaly_model.predict(X_full_scaled)
    anomaly_scores = anomaly_model.score_samples(X_full_scaled)
    
    # Convert to binary (1 = anomaly, 0 = normal)
    is_anomaly = (predictions == -1).astype(int)
    
    # Normalize scores to 0-1 range
    normalized_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min())
    normalized_scores = 1 - normalized_scores  # Invert so higher = more anomalous
    
    # Statistics
    anomaly_rate = is_anomaly.mean()
    fraud_detection_rate = df[df['fraud_label'] == 1]['fraud_label'].index.isin(
        df[is_anomaly == 1].index
    ).mean()
    
    print(f"\n   Anomaly Detection Results:")
    print(f"   - Anomalies detected: {is_anomaly.sum()} ({anomaly_rate*100:.1f}%)")
    print(f"   - Fraud claims flagged as anomalies: {fraud_detection_rate*100:.1f}%")
    print(f"   - Mean anomaly score: {normalized_scores.mean():.4f}")
    print(f"   - Std anomaly score: {normalized_scores.std():.4f}")
    
    # Save models
    print("\n[5/5] Saving models...")
    model_dir = os.path.dirname(__file__)
    
    # Save Isolation Forest
    anomaly_path = os.path.join(model_dir, 'anomaly_model_v2.pkl')
    with open(anomaly_path, 'wb') as f:
        pickle.dump(anomaly_model, f)
    print(f"   ✓ Anomaly model saved: {anomaly_path}")
    
    # Save scaler
    scaler_path = os.path.join(model_dir, 'anomaly_scaler_v2.pkl')
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   ✓ Scaler saved: {scaler_path}")
    
    # Save metadata
    metadata = {
        'model_version': '2.0',
        'training_date': pd.Timestamp.now().isoformat(),
        'features': feature_columns,
        'n_train_samples': len(X),
        'contamination': contamination,
        'anomaly_rate': float(anomaly_rate),
        'fraud_detection_rate': float(fraud_detection_rate)
    }
    
    metadata_path = os.path.join(model_dir, 'anomaly_model_v2_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✓ Metadata saved: {metadata_path}")
    
    print("\n" + "="*70)
    print("ANOMALY MODEL TRAINING COMPLETE!")
    print("="*70)
    
    return anomaly_model, scaler


if __name__ == "__main__":
    print("\n🤖 TRAINING ML MODELS - VERSION 2.0")
    print("Updated for current database schema")
    print("="*70)
    
    # Train fraud detection model
    fraud_model, fraud_importance = train_fraud_model_v2()
    
    # Train anomaly detection model
    anomaly_model, scaler = train_anomaly_model_v2()
    
    print("\n" + "="*70)
    print("✅ ALL MODELS TRAINED SUCCESSFULLY!")
    print("="*70)
    print("\nNext steps:")
    print("1. Update fraud_analysis_engine.py to load v2 models")
    print("2. Test with real claims in your system")
    print("3. Monitor performance and retrain as needed")
