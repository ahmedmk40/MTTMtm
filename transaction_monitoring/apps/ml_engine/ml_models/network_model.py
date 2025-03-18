"""
Network analysis model for fraud detection.

This model analyzes transaction networks to detect suspicious patterns.
"""

import os
import pickle
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score


def create_dummy_network_data(n_samples=1000, n_entities=200):
    """
    Create dummy network data for model training.
    
    Args:
        n_samples: Number of samples to generate
        n_entities: Number of unique entities (users, merchants, etc.)
        
    Returns:
        DataFrame with dummy network data
    """
    np.random.seed(42)
    
    # Generate entity IDs
    user_ids = [f"user_{i}" for i in range(n_entities)]
    merchant_ids = [f"merchant_{i}" for i in range(n_entities)]
    
    # Generate features
    data = {
        'user_id': np.random.choice(user_ids, size=n_samples),
        'merchant_id': np.random.choice(merchant_ids, size=n_samples),
        'amount': np.random.exponential(scale=500, size=n_samples),
        'timestamp': pd.date_range(start='2025-01-01', periods=n_samples, freq='H'),
        'channel': np.random.choice(['pos', 'ecommerce', 'wallet'], size=n_samples),
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create a graph from the transactions
    G = nx.Graph()
    
    # Add edges between users and merchants
    for _, row in df.iterrows():
        G.add_edge(row['user_id'], row['merchant_id'], weight=row['amount'])
    
    # Calculate network features
    user_degree = {}
    user_weighted_degree = {}
    merchant_degree = {}
    merchant_weighted_degree = {}
    
    for node in G.nodes():
        if node.startswith('user_'):
            user_degree[node] = G.degree(node)
            user_weighted_degree[node] = sum(G[node][neighbor]['weight'] for neighbor in G[node])
        elif node.startswith('merchant_'):
            merchant_degree[node] = G.degree(node)
            merchant_weighted_degree[node] = sum(G[node][neighbor]['weight'] for neighbor in G[node])
    
    # Add network features to the DataFrame
    df['user_degree'] = df['user_id'].map(user_degree)
    df['user_weighted_degree'] = df['user_id'].map(user_weighted_degree)
    df['merchant_degree'] = df['merchant_id'].map(merchant_degree)
    df['merchant_weighted_degree'] = df['merchant_id'].map(merchant_weighted_degree)
    
    # Add more network features
    df['user_avg_transaction'] = df['user_weighted_degree'] / df['user_degree']
    df['merchant_avg_transaction'] = df['merchant_weighted_degree'] / df['merchant_degree']
    
    # Generate anomaly labels (for evaluation only, not used in training)
    # Higher probability of anomaly for:
    # - Users with high degree but low weighted degree (many small transactions)
    # - Users with low degree but high weighted degree (few large transactions)
    # - Merchants with unusual patterns
    anomaly_prob = (
        0.01 +  # Base anomaly rate
        0.1 * ((df['user_degree'] > 10) & (df['user_avg_transaction'] < 100)) +  # Many small transactions
        0.15 * ((df['user_degree'] < 3) & (df['user_avg_transaction'] > 1000)) +  # Few large transactions
        0.1 * (df['merchant_degree'] > 20) +  # Very connected merchants
        0.05 * (df['amount'] > 1000)  # Large transactions
    )
    
    # Clip probabilities to [0, 1]
    anomaly_prob = np.clip(anomaly_prob, 0, 1)
    
    # Generate anomaly labels
    df['is_anomaly'] = np.random.binomial(1, anomaly_prob)
    
    return df


def train_network_model():
    """
    Train a network analysis model for fraud detection.
    
    Returns:
        Tuple of (model, metrics)
    """
    # Create dummy data
    df = create_dummy_network_data(n_samples=5000, n_entities=200)
    
    # Drop non-feature columns
    X = df.drop(columns=['user_id', 'merchant_id', 'timestamp', 'is_anomaly'])
    
    # One-hot encode categorical features
    X = pd.get_dummies(X, columns=['channel'], drop_first=False)
    
    # Target variable
    y = df['is_anomaly']
    
    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'precision': float(precision_score(y_test, y_pred)),
        'recall': float(recall_score(y_test, y_pred)),
        'f1_score': float(f1_score(y_test, y_pred)),
        'training_data_size': len(df),
        'feature_importance': {
            feature: float(importance)
            for feature, importance in zip(X.columns, model.feature_importances_)
        }
    }
    
    # Store feature names in the model for later use
    model.feature_names_in_ = X.columns.tolist()
    
    return model, metrics


def save_dummy_network_model(base_dir):
    """
    Train and save a dummy network analysis model.
    
    Args:
        base_dir: Base directory to save the model
        
    Returns:
        Relative path to the saved model
    """
    # Create directory for models if it doesn't exist
    models_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Train model
    model, _ = train_network_model()
    
    # Create file path
    file_name = "network_analysis_v1.pkl"
    full_path = os.path.join(models_dir, file_name)
    
    # Save model to file
    with open(full_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Saved dummy network model to {full_path}")
    
    return os.path.join('ml_models', file_name)