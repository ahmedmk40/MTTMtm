"""
Velocity-based anomaly detection model for fraud detection.

This model analyzes transaction velocity patterns to detect anomalies.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score


def create_dummy_velocity_data(n_samples=1000, n_users=100):
    """
    Create dummy velocity data for model training.
    
    Args:
        n_samples: Number of samples to generate
        n_users: Number of unique users
        
    Returns:
        DataFrame with dummy velocity data
    """
    np.random.seed(42)
    
    # Generate user IDs
    user_ids = [f"user_{i}" for i in range(n_users)]
    
    # Generate features
    data = {
        'user_id': np.random.choice(user_ids, size=n_samples),
        # Transaction count velocities
        'tx_count_1min': np.random.poisson(lam=0.1, size=n_samples),
        'tx_count_5min': np.random.poisson(lam=0.3, size=n_samples),
        'tx_count_15min': np.random.poisson(lam=0.5, size=n_samples),
        'tx_count_1hour': np.random.poisson(lam=1, size=n_samples),
        'tx_count_6hour': np.random.poisson(lam=3, size=n_samples),
        'tx_count_24hour': np.random.poisson(lam=5, size=n_samples),
        
        # Amount velocities
        'amount_1min': np.random.exponential(scale=50, size=n_samples),
        'amount_5min': np.random.exponential(scale=100, size=n_samples),
        'amount_15min': np.random.exponential(scale=200, size=n_samples),
        'amount_1hour': np.random.exponential(scale=500, size=n_samples),
        'amount_6hour': np.random.exponential(scale=1000, size=n_samples),
        'amount_24hour': np.random.exponential(scale=2000, size=n_samples),
        
        # Merchant count velocities
        'merchant_count_1hour': np.random.poisson(lam=1, size=n_samples),
        'merchant_count_24hour': np.random.poisson(lam=3, size=n_samples),
        
        # Location count velocities
        'location_count_1hour': np.random.poisson(lam=0.5, size=n_samples),
        'location_count_24hour': np.random.poisson(lam=1, size=n_samples),
        
        # Device count velocities
        'device_count_1hour': np.random.poisson(lam=0.2, size=n_samples),
        'device_count_24hour': np.random.poisson(lam=0.5, size=n_samples),
        
        # IP count velocities
        'ip_count_1hour': np.random.poisson(lam=0.2, size=n_samples),
        'ip_count_24hour': np.random.poisson(lam=0.5, size=n_samples),
        
        # Failed transaction velocities
        'failed_tx_count_1hour': np.random.poisson(lam=0.1, size=n_samples),
        'failed_tx_count_24hour': np.random.poisson(lam=0.3, size=n_samples),
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Generate anomaly labels (for evaluation only, not used in training)
    # Higher probability of anomaly for:
    # - High transaction counts in short time periods
    # - High amounts in short time periods
    # - Multiple merchants/locations/devices/IPs in short time periods
    # - Failed transactions
    anomaly_prob = (
        0.01 +  # Base anomaly rate
        0.2 * (df['tx_count_1min'] > 1) +  # More than 1 transaction per minute
        0.15 * (df['tx_count_5min'] > 3) +  # More than 3 transactions in 5 minutes
        0.1 * (df['amount_1min'] > 200) +  # High amount in 1 minute
        0.1 * (df['amount_5min'] > 500) +  # High amount in 5 minutes
        0.15 * (df['merchant_count_1hour'] > 3) +  # Multiple merchants in 1 hour
        0.15 * (df['location_count_1hour'] > 2) +  # Multiple locations in 1 hour
        0.2 * (df['device_count_1hour'] > 1) +  # Multiple devices in 1 hour
        0.2 * (df['ip_count_1hour'] > 1) +  # Multiple IPs in 1 hour
        0.15 * (df['failed_tx_count_1hour'] > 2)  # Failed transactions in 1 hour
    )
    
    # Clip probabilities to [0, 1]
    anomaly_prob = np.clip(anomaly_prob, 0, 1)
    
    # Generate anomaly labels
    df['is_anomaly'] = np.random.binomial(1, anomaly_prob)
    
    return df


def train_velocity_model():
    """
    Train a velocity-based anomaly detection model.
    
    Returns:
        Tuple of (model, metrics)
    """
    # Create dummy data
    df = create_dummy_velocity_data(n_samples=5000, n_users=200)
    
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
            # We'll use a simple heuristic based on feature correlation with anomaly
            feature: float(abs(np.corrcoef(X[feature], y_true)[0, 1]))
            for feature in X.columns
        }
    }
    
    # Store feature names in the model for later use
    model.feature_names_in_ = X.columns.tolist()
    
    return model, metrics


def save_dummy_velocity_model(base_dir):
    """
    Train and save a dummy velocity model.
    
    Args:
        base_dir: Base directory to save the model
        
    Returns:
        Relative path to the saved model
    """
    # Create directory for models if it doesn't exist
    models_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Train model
    model, _ = train_velocity_model()
    
    # Create file path
    file_name = "velocity_anomaly_v1.pkl"
    full_path = os.path.join(models_dir, file_name)
    
    # Save model to file
    with open(full_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Saved dummy velocity model to {full_path}")
    
    return os.path.join('ml_models', file_name)