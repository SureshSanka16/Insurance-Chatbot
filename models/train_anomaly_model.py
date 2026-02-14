"""
Isolation Forest Anomaly Detection Model Training
Identifies anomalous claim patterns in health insurance claims

Anomaly detection complements fraud detection by:
- Detecting unusual patterns not seen during training
- Identifying outliers in claim behavior
- Flagging claims with unusual feature combinations
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')


def train_anomaly_model():
    """
    Train IsolationForest model for anomaly detection
    
    Uses the same features as fraud model, but focuses on detecting
    unusual patterns rather than known fraud signatures.
    """
    
    # Load dataset
    print("Loading fraud dataset for anomaly training...")
    import os
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fraud_dataset.csv')
    df = pd.read_csv(dataset_path)
    
    # Select same features as fraud model (excluding fraud_label)
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
    y_true = df['fraud_label']  # For evaluation only
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Features: {len(feature_columns)}")
    print(f"Samples: {len(X)}")
    
    # Option 1: Train on full dataset (recommended for unsupervised learning)
    # Option 2: Train only on normal claims (use if sufficient normal samples exist)
    
    # Using Option 1: Full dataset
    print(f"\nTraining on full dataset (both normal and fraudulent claims)")
    print(f"Normal claims: {(y_true == 0).sum()}")
    print(f"Fraudulent claims: {(y_true == 1).sum()}")
    
    # Train IsolationForest
    print("\n" + "="*60)
    print("Training IsolationForest Model...")
    print("="*60)
    
    # Model parameters:
    # - n_estimators: Number of isolation trees (200 for robustness)
    # - contamination: Expected proportion of anomalies (0.1 = 10%)
    # - random_state: For reproducibility
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    
    # Fit the model
    model.fit(X)
    
    print("✓ Anomaly detection model training completed")
    
    # Make predictions
    # IsolationForest returns: 1 = normal, -1 = anomaly
    predictions = model.predict(X)
    anomaly_scores = model.decision_function(X)
    
    # Convert predictions to binary: 1 for normal, 0 for anomaly
    anomaly_flags = (predictions == -1).astype(int)
    
    # Evaluation
    print("\n" + "="*60)
    print("ANOMALY DETECTION RESULTS")
    print("="*60)
    print(f"Total samples: {len(predictions)}")
    print(f"Normal predictions (1): {(predictions == 1).sum()}")
    print(f"Anomaly predictions (-1): {(predictions == -1).sum()}")
    print(f"Anomaly rate: {(predictions == -1).mean()*100:.2f}%")
    
    # Decision function statistics
    print("\n" + "="*60)
    print("ANOMALY SCORE DISTRIBUTION")
    print("="*60)
    print(f"Mean score: {anomaly_scores.mean():.4f}")
    print(f"Std dev: {anomaly_scores.std():.4f}")
    print(f"Min score: {anomaly_scores.min():.4f}")
    print(f"Max score: {anomaly_scores.max():.4f}")
    print(f"\nNote: Lower scores indicate higher anomaly likelihood")
    
    # Overlap analysis with fraud labels
    print("\n" + "="*60)
    print("OVERLAP WITH FRAUD LABELS")
    print("="*60)
    
    anomaly_mask = predictions == -1
    fraud_mask = y_true == 1
    
    # Cases where anomaly detection flags fraudulent claims
    fraud_detected_as_anomaly = (anomaly_mask & fraud_mask).sum()
    total_fraud = fraud_mask.sum()
    
    # Cases where anomaly detection flags legitimate claims
    legit_detected_as_anomaly = (anomaly_mask & ~fraud_mask).sum()
    total_legit = (~fraud_mask).sum()
    
    print(f"Fraudulent claims flagged as anomalies: {fraud_detected_as_anomaly}/{total_fraud} ({fraud_detected_as_anomaly/total_fraud*100:.2f}%)")
    print(f"Legitimate claims flagged as anomalies: {legit_detected_as_anomaly}/{total_legit} ({legit_detected_as_anomaly/total_legit*100:.2f}%)")
    
    print("\nInterpretation:")
    print("- Anomaly detection captures unusual patterns in both fraud and legitimate claims")
    print("- It complements fraud model by detecting outliers beyond trained fraud signatures")
    print("- Legitimate anomalies may be unusual but valid claims (e.g., rare conditions)")
    
    # Feature importance (approximate using prediction variance)
    print("\n" + "="*60)
    print("FEATURE SENSITIVITY ANALYSIS")
    print("="*60)
    
    # Calculate feature importance by measuring prediction sensitivity
    feature_importance = []
    baseline_score = anomaly_scores.mean()
    
    for i, feature in enumerate(feature_columns):
        # Perturb feature and measure score change
        X_perturbed = X.astype(float).copy()
        X_perturbed.iloc[:, i] = X_perturbed.iloc[:, i].mean()
        perturbed_scores = model.decision_function(X_perturbed)
        importance = np.abs(perturbed_scores.mean() - baseline_score)
        feature_importance.append(importance)
    
    feature_importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    print("Top features affecting anomaly detection:")
    print(feature_importance_df.head(10).to_string(index=False))
    
    # Save model
    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, 'anomaly_model.pkl')
    joblib.dump(model, model_path)
    print(f"\n✓ Anomaly model saved to {model_path}")
    
    # Save model metadata
    model_info = {
        'features': feature_columns,
        'model_type': 'IsolationForest',
        'n_estimators': 200,
        'contamination': 0.1,
        'anomaly_interpretation': {
            -1: 'Anomaly',
            1: 'Normal'
        }
    }
    info_path = os.path.join(model_dir, 'anomaly_model_info.pkl')
    joblib.dump(model_info, info_path)
    print(f"✓ Model metadata saved to {info_path}")
    
    # Test predictions on sample cases
    print("\n" + "="*60)
    print("SAMPLE PREDICTIONS")
    print("="*60)
    
    # Get a normal and anomalous sample
    normal_idx = predictions == 1
    anomaly_idx = predictions == -1
    
    if anomaly_idx.sum() > 0:
        print("\nExample Normal Claim:")
        normal_sample = X[normal_idx].iloc[0]
        normal_pred = model.predict([normal_sample])[0]
        normal_score = model.decision_function([normal_sample])[0]
        print(f"Prediction: {normal_pred} (1=normal, -1=anomaly)")
        print(f"Anomaly score: {normal_score:.4f}")
        
        print("\nExample Anomalous Claim:")
        anomaly_sample = X[anomaly_idx].iloc[0]
        anomaly_pred = model.predict([anomaly_sample])[0]
        anomaly_score = model.decision_function([anomaly_sample])[0]
        print(f"Prediction: {anomaly_pred} (1=normal, -1=anomaly)")
        print(f"Anomaly score: {anomaly_score:.4f}")
    
    return model, feature_importance_df


if __name__ == "__main__":
    print("="*60)
    print("ANOMALY DETECTION MODEL TRAINING")
    print("="*60)
    print("\nThis script trains an IsolationForest model to detect")
    print("anomalous patterns in health insurance claims.")
    print("\nAnomalies complement fraud detection by identifying:")
    print("  • Unusual claim patterns")
    print("  • Outlier behavior")
    print("  • Novel fraud techniques")
    print("  • Data quality issues")
    print("="*60)
    
    model, feature_importance = train_anomaly_model()
    
    print("\n" + "="*60)
    print("Training completed successfully!")
    print("="*60)
    print("\nModel files created:")
    print("  - anomaly_model.pkl")
    print("  - anomaly_model_info.pkl")
    print("\nYou can now use this model alongside fraud detection.")
