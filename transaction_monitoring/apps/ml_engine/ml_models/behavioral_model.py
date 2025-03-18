"""
Behavioral analysis model for fraud detection.

This model analyzes user behavior patterns to detect anomalies.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score


def create_dummy_behavioral_data(n_samples=1000, n_users=100):
    """
    Create dummy behavioral data for model training.
    
    Args:
        n_samples: Number of samples to generate
        n_users: Number of unique users
        
    Returns:
        DataFrame with dummy behavioral data
    """
    np.random.seed(42)
    
    # Generate user IDs
    user_ids = [f"user_{i}" for i in range(n_users)]
    
    # Generate features
    data = {
        'user_id': np.random.choice(user_ids, size=n_samples),
        'transaction_count_1d': np.random.poisson(lam=2, size=n_samples),
        'transaction_count_7d': np.random.poisson(lam=10, size=n_samples),
        'transaction_count_30d': np.random.poisson(lam=30, size=n_samples),
        'avg_amount_1d': np.random.exponential(scale=100, size=n_samples),
        'avg_amount_7d': np.random.exponential(scale=100, size=n_samples),
        'avg_amount_30d': np.random.exponential(scale=100, size=n_samples),
        'max_amount_30d': np.random.exponential(scale=500, size=n_samples),
        'distinct_merchants_7d': np.random.poisson(lam=5, size=n_samples),
        'distinct_countries_30d': np.random.poisson(lam=1, size=n_samples),
        'time_since_last_transaction': np.random.exponential(scale=24, size=n_samples),  # hours
        'velocity_amount_1d': np.random.exponential(scale=200, size=n_samples),
        'velocity_count_1d': np.random.poisson(lam=3, size=n_samples),
        'failed_attempts_24h': np.random.poisson(lam=0.2, size=n_samples),
        'device_count_30d': np.random.poisson(lam=1.5, size=n_samples),
        'location_count_30d': np.random.poisson(lam=2, size=n_samples),
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Generate anomaly labels (for evaluation only, not used in training)
    # Higher probability of anomaly for:
    # - High transaction counts
    # - High velocity
    # - Multiple countries
    # - Multiple devices
    # - Failed attempts
    anomaly_prob = (
        0.01 +  # Base anomaly rate
        0.1 * (df['transaction_count_1d'] > 5) +  # High transaction count
        0.1 * (df['velocity_amount_1d'] > 500) +  # High velocity
        0.15 * (df['distinct_countries_30d'] > 3) +  # Multiple countries
        0.1 * (df['device_count_30d'] > 3) +  # Multiple devices
        0.2 * (df['failed_attempts_24h'] > 2)  # Failed attempts
    )
    
    # Clip probabilities to [0, 1]
    anomaly_prob = np.clip(anomaly_prob, 0, 1)
    
    # Generate anomaly labels
    df['is_anomaly'] = np.random.binomial(1, anomaly_prob)
    
    return df


def train_behavioral_model():
    """
    Train a behavioral model for anomaly detection.
    
    Returns:
        Tuple of (model, metrics)
    """
    # Create dummy data
    df = create_dummy_behavioral_data(n_samples=10000, n_users=500)
    
    # Split features and target (target is only for evaluation)
    X = df.drop(columns=['user_id', 'is_anomaly'])
    y_true = df['is_anomaly']
    
    # Train model
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,  # Expected proportion of anomalies
        random_state=42
    )
    model.fit(X)
    
    # Make predictions
    # Convert to binary labels (1 for inliers, -1 for outliers)
    y_pred = model.predict(X)
    
    # Convert to 0 for inliers, 1 for outliers (to match our anomaly labels)
    y_pred_binary = np.where(y_pred == -1, 1, 0)
    
    # Calculate metrics
    metrics = {
        'precision': float(precision_score(y_true, y_pred_binary)),
        'recall': float(recall_score(y_true, y_pred_binary)),
        'f1_score': float(f1_score(y_true, y_pred_binary)),
        'training_data_size': len(df),
        'feature_importance': {
            # Isolation Forest doesn't provide feature importance directly
            # We'll use a simple heuristic based on the feature's range
            feature: float(1.0 / (i + 1))  # Just a placeholder
            for i, feature in enumerate(X.columns)
        }
    }
    
    # Store feature names in the model for later use
    model.feature_names_in_ = X.columns.tolist()
    
    return model, metrics


def save_dummy_behavioral_model(base_dir):
    """
    Train and save a dummy behavioral model.
    
    Args:
        base_dir: Base directory to save the model
        
    Returns:
        Relative path to the saved model
    """
    # Create directory for models if it doesn't exist
    models_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Train model
    model, _ = train_behavioral_model()
    
    # Create file path
    file_name = "behavioral_analysis_v1.pkl"
    full_path = os.path.join(models_dir, file_name)
    
    # Save model to file
    with open(full_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Saved dummy behavioral model to {full_path}")
    
    return os.path.join('ml_models', file_name)