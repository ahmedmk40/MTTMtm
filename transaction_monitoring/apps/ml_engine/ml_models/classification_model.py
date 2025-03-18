"""
Classification model for fraud detection.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


def create_dummy_data(n_samples=1000):
    """
    Create dummy data for model training.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with dummy data
    """
    np.random.seed(42)
    
    # Generate features
    data = {
        'amount': np.random.exponential(scale=500, size=n_samples),
        'hour_of_day': np.random.randint(0, 24, size=n_samples),
        'day_of_week': np.random.randint(0, 7, size=n_samples),
        'is_weekend': np.random.randint(0, 2, size=n_samples),
        'is_night': np.random.randint(0, 2, size=n_samples),
        'has_ip': np.random.randint(0, 2, size=n_samples),
        'has_coordinates': np.random.randint(0, 2, size=n_samples),
        'is_new_card': np.random.randint(0, 2, size=n_samples),
        'is_high_risk_country': np.random.randint(0, 2, size=n_samples),
        'is_suspicious_mcc': np.random.randint(0, 2, size=n_samples),
        'transaction_type_acquiring': np.random.randint(0, 2, size=n_samples),
        'transaction_type_wallet': np.random.randint(0, 2, size=n_samples),
        'channel_pos': np.random.randint(0, 2, size=n_samples),
        'channel_ecommerce': np.random.randint(0, 2, size=n_samples),
        'channel_wallet': np.random.randint(0, 2, size=n_samples),
        'payment_method_type_credit_card': np.random.randint(0, 2, size=n_samples),
        'payment_method_type_debit_card': np.random.randint(0, 2, size=n_samples),
        'payment_method_type_wallet': np.random.randint(0, 2, size=n_samples),
        'payment_method_type_bank_transfer': np.random.randint(0, 2, size=n_samples),
        'payment_method_type_unknown': np.random.randint(0, 2, size=n_samples),
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Generate target variable (fraud)
    # Higher probability of fraud for:
    # - High amounts
    # - Night transactions
    # - New cards
    # - High-risk countries
    # - Suspicious MCCs
    fraud_prob = (
        0.01 +  # Base fraud rate
        0.1 * (df['amount'] > 1000) +  # High amount
        0.05 * df['is_night'] +  # Night transactions
        0.1 * df['is_new_card'] +  # New cards
        0.15 * df['is_high_risk_country'] +  # High-risk countries
        0.1 * df['is_suspicious_mcc']  # Suspicious MCCs
    )
    
    # Clip probabilities to [0, 1]
    fraud_prob = np.clip(fraud_prob, 0, 1)
    
    # Generate fraud labels
    df['is_fraud'] = np.random.binomial(1, fraud_prob)
    
    return df


def train_classification_model():
    """
    Train a classification model for fraud detection.
    
    Returns:
        Tuple of (model, metrics)
    """
    # Create dummy data
    df = create_dummy_data(n_samples=10000)
    
    # Split features and target
    X = df.drop(columns=['is_fraud'])
    y = df['is_fraud']
    
    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred)),
        'recall': float(recall_score(y_test, y_pred)),
        'f1_score': float(f1_score(y_test, y_pred)),
        'auc_roc': float(roc_auc_score(y_test, y_prob)),
        'training_data_size': len(df),
        'feature_importance': {
            feature: float(importance)
            for feature, importance in zip(X.columns, model.feature_importances_)
        }
    }
    
    return model, metrics


def save_dummy_model(base_dir):
    """
    Train and save a dummy classification model.
    
    Args:
        base_dir: Base directory to save the model
    """
    # Create directory for models if it doesn't exist
    models_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Train model
    model, _ = train_classification_model()
    
    # Create file path
    file_name = "fraud_classification_v1.pkl"
    full_path = os.path.join(models_dir, file_name)
    
    # Save model to file
    with open(full_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Saved dummy classification model to {full_path}")
    
    return os.path.join('ml_models', file_name)