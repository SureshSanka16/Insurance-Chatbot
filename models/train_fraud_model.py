"""
XGBoost Fraud Detection Model Training
Trains a classifier to detect fraudulent health insurance claims
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, classification_report, confusion_matrix, roc_auc_score
)
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

def train_fraud_model():
    """
    Train XGBoost model on synthetic fraud dataset
    """
    
    # Load dataset
    print("Loading fraud dataset...")
    import os
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fraud_dataset.csv')
    df = pd.read_csv(dataset_path)
    
    # Select features for model
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
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Features: {len(feature_columns)}")
    print(f"Samples: {len(X)}")
    
    # Split data 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Train fraud %: {y_train.mean()*100:.2f}%")
    print(f"Test fraud %: {y_test.mean()*100:.2f}%")
    
    # Train XGBoost classifier
    print("\n" + "="*60)
    print("Training XGBoost Classifier...")
    print("="*60)
    
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train, verbose=False)
    
    print("✓ Model training completed")
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    y_pred_proba_train = model.predict_proba(X_train)[:, 1]
    y_pred_proba_test = model.predict_proba(X_test)[:, 1]
    
    # Evaluation metrics
    print("\n" + "="*60)
    print("MODEL PERFORMANCE - TRAINING SET")
    print("="*60)
    print(f"Accuracy:  {accuracy_score(y_train, y_pred_train):.4f}")
    print(f"Precision: {precision_score(y_train, y_pred_train):.4f}")
    print(f"Recall:    {recall_score(y_train, y_pred_train):.4f}")
    print(f"F1-Score:  {f1_score(y_train, y_pred_train):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_train, y_pred_proba_train):.4f}")
    
    print("\n" + "="*60)
    print("MODEL PERFORMANCE - TEST SET")
    print("="*60)
    print(f"Accuracy:  {accuracy_score(y_test, y_pred_test):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred_test):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred_test):.4f}")
    print(f"F1-Score:  {f1_score(y_test, y_pred_test):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, y_pred_proba_test):.4f}")
    
    # Detailed classification report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(classification_report(y_test, y_pred_test, 
                                target_names=['Legitimate', 'Fraudulent']))
    
    # Confusion matrix
    print("\n" + "="*60)
    print("CONFUSION MATRIX")
    print("="*60)
    cm = confusion_matrix(y_test, y_pred_test)
    print(f"True Negatives:  {cm[0,0]}")
    print(f"False Positives: {cm[0,1]}")
    print(f"False Negatives: {cm[1,0]}")
    print(f"True Positives:  {cm[1,1]}")
    
    # Feature importance
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.to_string(index=False))
    
    # Save model
    import os
    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, 'fraud_model.pkl')
    joblib.dump(model, model_path)
    print(f"\n✓ Model saved to {model_path}")
    
    # Save feature list for later use
    feature_info = {
        'features': feature_columns,
        'model_type': 'XGBClassifier',
        'threshold_high_risk': 0.7,
        'threshold_medium_risk': 0.4
    }
    features_path = os.path.join(model_dir, 'fraud_model_features.pkl')
    joblib.dump(feature_info, features_path)
    print(f"✓ Feature info saved to {features_path}")
    
    return model, feature_importance


if __name__ == "__main__":
    model, feature_importance = train_fraud_model()
    
    print("\n" + "="*60)
    print("Training completed successfully!")
    print("="*60)
    print("\nModel files created:")
    print("  - fraud_model.pkl")
    print("  - fraud_model_features.pkl")
    print("\nYou can now use this model for fraud detection in the agent.")
