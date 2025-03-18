"""
Optimized response code ML model for fraud detection.

This model uses advanced features and hyperparameter tuning to improve
fraud detection based on response codes.
"""

import os
import pickle
import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from django.conf import settings
from django.utils import timezone
from ..models import MLModel

logger = logging.getLogger(__name__)


def train_optimized_response_code_model(data=None):
    """
    Train an optimized model that uses response codes as features.
    
    Args:
        data: Optional training data. If None, synthetic data will be generated.
        
    Returns:
        Trained model and performance metrics
    """
    logger.info("Training optimized response code model...")
    
    # If no data provided, generate synthetic data
    if data is None:
        data = generate_synthetic_data()
    
    # Prepare features and target
    X = data.drop('is_fraud', axis=1)
    y = data['is_fraud']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define feature types
    categorical_features = [
        'transaction_type', 'channel', 'country', 'payment_method_type', 
        'response_code', 'entry_mode', 'condition', 'source_type', 
        'destination_type', 'transaction_purpose'
    ]
    
    # Add previous response code features if they exist
    prev_response_features = [col for col in X.columns if col.startswith('prev_response_code_')]
    categorical_features.extend(prev_response_features)
    
    # Identify numerical features
    numerical_features = [
        col for col in X.columns 
        if col not in categorical_features and X[col].dtype in ['int64', 'float64']
    ]
    
    # Define preprocessing
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    numerical_transformer = StandardScaler()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_features),
            ('num', numerical_transformer, numerical_features)
        ],
        remainder='drop'
    )
    
    # Define models to try
    models = {
        'random_forest': RandomForestClassifier(random_state=42),
        'gradient_boosting': GradientBoostingClassifier(random_state=42)
    }
    
    # Define parameter grids for each model
    param_grids = {
        'random_forest': {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [8, 12, 16],
            'classifier__min_samples_split': [2, 5],
            'classifier__class_weight': ['balanced', None]
        },
        'gradient_boosting': {
            'classifier__n_estimators': [100, 200],
            'classifier__learning_rate': [0.05, 0.1],
            'classifier__max_depth': [3, 5],
            'classifier__subsample': [0.8, 1.0]
        }
    }
    
    best_model = None
    best_score = 0
    best_params = None
    best_model_name = None
    
    # Try each model with grid search
    for model_name, model in models.items():
        logger.info(f"Tuning {model_name} model...")
        
        # Create pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', model)
        ])
        
        # Grid search
        grid_search = GridSearchCV(
            pipeline, 
            param_grids[model_name], 
            cv=5, 
            scoring='f1',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        
        # Evaluate best model from grid search
        y_pred = grid_search.predict(X_test)
        y_prob = grid_search.predict_proba(X_test)[:, 1]
        
        f1 = f1_score(y_test, y_pred)
        
        logger.info(f"{model_name} best F1 score: {f1:.4f}")
        logger.info(f"{model_name} best parameters: {grid_search.best_params_}")
        
        # Keep track of best model
        if f1 > best_score:
            best_score = f1
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_model_name = model_name
    
    logger.info(f"Best model: {best_model_name} with F1 score: {best_score:.4f}")
    
    # Final evaluation of best model
    y_pred = best_model.predict(X_test)
    y_prob = best_model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'auc_roc': roc_auc_score(y_test, y_prob)
    }
    
    logger.info(f"Final metrics: {metrics}")
    
    # Save the model
    model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'optimized_response_code_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    # Create or update model in database
    relative_path = os.path.join('ml_models', 'optimized_response_code_model.pkl')
    
    # Get feature importance if available
    feature_importance = {}
    if hasattr(best_model.named_steps['classifier'], 'feature_importances_'):
        # For tree-based models
        importances = best_model.named_steps['classifier'].feature_importances_
        
        # Get feature names after preprocessing
        feature_names = []
        
        # For categorical features, get the one-hot encoded feature names
        if hasattr(best_model.named_steps['preprocessor'].transformers_[0][1], 'get_feature_names_out'):
            cat_features = best_model.named_steps['preprocessor'].transformers_[0][1].get_feature_names_out(categorical_features)
            feature_names.extend(cat_features)
        
        # For numerical features, use the original feature names
        feature_names.extend(numerical_features)
        
        # Create feature importance dictionary
        for feature, importance in zip(feature_names, importances):
            feature_importance[feature] = float(importance)
    
    ml_model, created = MLModel.objects.update_or_create(
        name='Optimized Response Code Analysis',
        version='2.0',
        defaults={
            'description': 'Optimized model for response code-based fraud detection',
            'model_type': 'classification',
            'file_path': relative_path,
            'is_active': True,
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'auc_roc': metrics['auc_roc'],
            'training_date': timezone.now(),
            'training_data_size': len(data),
            'training_parameters': best_params,
            'feature_importance': feature_importance,
            'metadata': {
                'model_type': best_model_name,
                'hyperparameter_tuning': 'grid_search',
                'advanced_features': True
            }
        }
    )
    
    if created:
        logger.info(f"Created model: {ml_model.name} v{ml_model.version}")
    else:
        logger.info(f"Updated model: {ml_model.name} v{ml_model.version}")
    
    return best_model, metrics


def generate_synthetic_data(n_samples=5000):
    """
    Generate synthetic data for training the optimized response code model.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with synthetic data
    """
    logger.info(f"Generating {n_samples} synthetic data samples...")
    
    # Define response codes and their fraud probabilities
    response_codes = {
        '00': 0.01,  # Approved - very low fraud probability
        '05': 0.30,  # Do Not Honor - moderate fraud probability
        '12': 0.20,  # Invalid Transaction - moderate fraud probability
        '14': 0.40,  # Invalid Card Number - higher fraud probability
        '41': 0.60,  # Lost Card - high fraud probability
        '43': 0.70,  # Stolen Card - high fraud probability
        '51': 0.25,  # Insufficient Funds - moderate fraud probability
        '54': 0.35,  # Expired Card - moderate-high fraud probability
        '91': 0.15,  # Issuer or Switch Inoperative - lower fraud probability
    }
    
    # Generate data
    data = []
    for i in range(n_samples):
        # Basic transaction features
        transaction_type = np.random.choice(['purchase', 'authorization', 'refund', 'withdrawal'])
        channel = np.random.choice(['pos', 'ecommerce', 'wallet'])
        amount = np.random.lognormal(mean=4.0, sigma=1.0)  # Random amount
        country = np.random.choice(['US', 'CA', 'GB', 'FR', 'DE', 'JP', 'AU', 'BR', 'RU', 'CN'])
        is_high_risk_country = 1 if country in ['RU', 'CN', 'BR'] else 0
        payment_method_type = np.random.choice(['credit_card', 'debit_card', 'wallet', 'bank_transfer'])
        
        # Time-based features
        hour_of_day = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)
        is_weekend = 1 if day_of_week >= 5 else 0
        is_night = 1 if hour_of_day < 6 or hour_of_day >= 22 else 0
        
        # Response code features
        response_code = np.random.choice(list(response_codes.keys()))
        fraud_prob_from_code = response_codes[response_code]
        
        # Previous response codes (sequence)
        prev_response_code_1 = np.random.choice(list(response_codes.keys()))
        prev_response_code_2 = np.random.choice(list(response_codes.keys()))
        prev_response_code_3 = np.random.choice(list(response_codes.keys()))
        
        # Response code counts
        response_code_00_count = np.random.randint(0, 10)
        response_code_51_count = np.random.randint(0, 5)
        response_code_14_count = np.random.randint(0, 3)
        response_code_43_count = np.random.randint(0, 2)
        
        # Response code velocities
        current_response_code_velocity_24h = np.random.randint(0, 5)
        
        # Advanced features
        high_risk_response_code_count = np.random.randint(0, 5)
        medium_risk_response_code_count = np.random.randint(0, 8)
        approved_count = np.random.randint(0, 15)
        declined_count = np.random.randint(0, 10)
        declined_to_approved_ratio = declined_count / approved_count if approved_count > 0 else 0
        channel_switch_count = np.random.randint(0, 3)
        response_code_risk_score = np.random.uniform(0, 100)
        
        # Base fraud probability
        base_fraud_prob = 0.05
        
        # Adjust fraud probability based on risk factors
        if amount > 1000:
            base_fraud_prob += 0.2
        if is_night:
            base_fraud_prob += 0.1
        if is_high_risk_country:
            base_fraud_prob += 0.15
        if channel == 'ecommerce':
            base_fraud_prob += 0.05
        if high_risk_response_code_count > 2:
            base_fraud_prob += 0.3
        if declined_to_approved_ratio > 1:
            base_fraud_prob += 0.2
        if response_code_risk_score > 70:
            base_fraud_prob += 0.4
        
        # Combine base fraud probability with response code probability
        fraud_prob = 0.4 * base_fraud_prob + 0.6 * fraud_prob_from_code
        
        # Cap probability at 0.95
        fraud_prob = min(fraud_prob, 0.95)
        
        # Determine if transaction is fraudulent based on probability
        is_fraud = np.random.random() < fraud_prob
        
        # Create record
        record = {
            'transaction_type': transaction_type,
            'channel': channel,
            'amount': amount,
            'country': country,
            'is_high_risk_country': is_high_risk_country,
            'payment_method_type': payment_method_type,
            'hour_of_day': hour_of_day,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'is_night': is_night,
            'response_code': response_code,
            'prev_response_code_1': prev_response_code_1,
            'prev_response_code_2': prev_response_code_2,
            'prev_response_code_3': prev_response_code_3,
            'response_code_00_count': response_code_00_count,
            'response_code_51_count': response_code_51_count,
            'response_code_14_count': response_code_14_count,
            'response_code_43_count': response_code_43_count,
            'current_response_code_velocity_24h': current_response_code_velocity_24h,
            'high_risk_response_code_count': high_risk_response_code_count,
            'medium_risk_response_code_count': medium_risk_response_code_count,
            'approved_count': approved_count,
            'declined_count': declined_count,
            'declined_to_approved_ratio': declined_to_approved_ratio,
            'channel_switch_count': channel_switch_count,
            'response_code_risk_score': response_code_risk_score,
            'is_fraud': int(is_fraud)
        }
        
        # Add channel-specific features
        if channel == 'pos':
            record.update({
                'entry_mode': np.random.choice(['chip', 'swipe', 'contactless', 'manual']),
                'condition': np.random.choice(['card_present', 'card_not_present']),
            })
        elif channel == 'wallet':
            record.update({
                'source_type': np.random.choice(['wallet', 'bank_account', 'card']),
                'destination_type': np.random.choice(['wallet', 'bank_account', 'card']),
                'transaction_purpose': np.random.choice(['deposit', 'withdrawal', 'transfer', 'payment']),
            })
        
        data.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Fill missing values for channel-specific features
    for col in ['entry_mode', 'condition', 'source_type', 'destination_type', 'transaction_purpose']:
        if col in df.columns:
            df[col].fillna('unknown', inplace=True)
    
    return df


def save_dummy_optimized_model(base_dir):
    """
    Save a dummy optimized response code model for testing.
    
    Args:
        base_dir: Base directory of the project
        
    Returns:
        Relative path to the saved model
    """
    # Create a simple pipeline with random forest
    categorical_features = ['transaction_type', 'channel', 'response_code']
    numerical_features = ['amount', 'hour_of_day', 'day_of_week']
    
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    numerical_transformer = StandardScaler()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_features),
            ('num', numerical_transformer, numerical_features)
        ],
        remainder='drop'
    )
    
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Create some dummy data to fit the model
    X = pd.DataFrame({
        'transaction_type': np.random.choice(['purchase', 'authorization'], 100),
        'channel': np.random.choice(['pos', 'ecommerce'], 100),
        'response_code': np.random.choice(['00', '51', '43'], 100),
        'amount': np.random.rand(100) * 1000,
        'hour_of_day': np.random.randint(0, 24, 100),
        'day_of_week': np.random.randint(0, 7, 100)
    })
    y = np.random.randint(0, 2, 100)  # Binary target
    
    # Fit the model
    model.fit(X, y)
    
    # Create directory if it doesn't exist
    model_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(model_dir, exist_ok=True)
    
    # Save the model
    model_path = os.path.join(model_dir, 'optimized_response_code_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Return relative path
    return os.path.join('ml_models', 'optimized_response_code_model.pkl')