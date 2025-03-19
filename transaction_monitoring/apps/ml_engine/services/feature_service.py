"""
Feature extraction service for the ML Engine.

This service is responsible for extracting and transforming features from transactions
for use in ML models.
"""

import logging
from typing import Dict, Any, List
from django.utils import timezone
from ..models import FeatureDefinition
from .advanced_features import extract_advanced_features

logger = logging.getLogger(__name__)


def extract_features(transaction) -> Dict[str, Any]:
    """
    Extract features from a transaction for ML models.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary of features
    """
    # Initialize features dictionary
    features = {}
    
    # Basic transaction features
    features['amount'] = float(transaction.amount)
    features['transaction_type'] = transaction.transaction_type
    features['channel'] = transaction.channel
    
    # Time-based features
    transaction_time = transaction.timestamp
    features['hour_of_day'] = transaction_time.hour
    features['day_of_week'] = transaction_time.weekday()
    features['is_weekend'] = 1 if transaction_time.weekday() >= 5 else 0
    features['is_night'] = 1 if transaction_time.hour < 6 or transaction_time.hour >= 22 else 0
    
    # Location features
    if hasattr(transaction, 'location_data') and transaction.location_data:
        location = transaction.location_data
        features['country'] = location.get('country', 'unknown')
        features['has_ip'] = 1 if location.get('ip_address') else 0
        
        # Check if coordinates are available
        if location.get('latitude') and location.get('longitude'):
            features['has_coordinates'] = 1
        else:
            features['has_coordinates'] = 0
    else:
        features['country'] = 'unknown'
        features['has_ip'] = 0
        features['has_coordinates'] = 0
    
    # Payment method features
    if hasattr(transaction, 'payment_method_data') and transaction.payment_method_data:
        payment_method = transaction.payment_method_data
        features['payment_method_type'] = payment_method.get('type', 'unknown')
        
        # Card-specific features
        if payment_method.get('type') in ['credit_card', 'debit_card']:
            card_details = payment_method.get('card_details', {})
            features['is_new_card'] = 1 if card_details.get('is_new', False) else 0
            
            # Extract card BIN (first 6 digits) if available
            if 'masked_card_number' in card_details:
                masked_number = card_details['masked_card_number']
                if masked_number and len(masked_number) >= 6 and not masked_number.startswith('*'):
                    features['card_bin'] = masked_number[:6]
                else:
                    features['card_bin'] = 'unknown'
            else:
                features['card_bin'] = 'unknown'
    else:
        features['payment_method_type'] = 'unknown'
        features['is_new_card'] = 0
        features['card_bin'] = 'unknown'
    
    # Channel-specific features
    if transaction.channel == 'pos':
        if hasattr(transaction, 'entry_mode'):
            features['entry_mode'] = transaction.entry_mode
        if hasattr(transaction, 'terminal_type'):
            features['terminal_type'] = transaction.terminal_type
        if hasattr(transaction, 'attendance'):
            features['attendance'] = transaction.attendance
        if hasattr(transaction, 'condition'):
            features['condition'] = transaction.condition
    
    elif transaction.channel == 'ecommerce':
        if hasattr(transaction, 'is_3ds_verified'):
            features['is_3ds_verified'] = 1 if transaction.is_3ds_verified else 0
        if hasattr(transaction, 'is_billing_shipping_match'):
            features['is_billing_shipping_match'] = 1 if transaction.is_billing_shipping_match else 0
    
    elif transaction.channel == 'wallet':
        if hasattr(transaction, 'source_type'):
            features['source_type'] = transaction.source_type
        if hasattr(transaction, 'destination_type'):
            features['destination_type'] = transaction.destination_type
        if hasattr(transaction, 'transaction_purpose'):
            features['transaction_purpose'] = transaction.transaction_purpose
        if hasattr(transaction, 'is_internal'):
            features['is_internal'] = 1 if transaction.is_internal else 0
    
    # Add MCC if available
    if hasattr(transaction, 'mcc') and transaction.mcc:
        features['mcc'] = transaction.mcc
    else:
        features['mcc'] = 'unknown'
        
    # Add response code if available
    if hasattr(transaction, 'response_code') and transaction.response_code:
        features['response_code'] = transaction.response_code
    else:
        features['response_code'] = '00'  # Default to approved
    
    # Extract advanced features
    advanced_features = extract_advanced_features(transaction)
    features.update(advanced_features)
    
    logger.debug(f"Extracted {len(features)} features for transaction {transaction.transaction_id}")
    
    return features


def transform_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw features into model-ready features.
    
    Args:
        features: Dictionary of raw features
        
    Returns:
        Dictionary of transformed features
    """
    transformed = {}
    
    # Numeric features (keep as is)
    numeric_features = ['amount', 'hour_of_day', 'day_of_week', 'is_weekend', 
                        'is_night', 'has_ip', 'has_coordinates', 'is_new_card',
                        'is_3ds_verified', 'is_billing_shipping_match', 'is_internal']
    
    for feature in numeric_features:
        if feature in features:
            transformed[feature] = features[feature]
    
    # Categorical features (one-hot encode)
    categorical_features = {
        'transaction_type': ['acquiring', 'wallet'],
        'channel': ['pos', 'ecommerce', 'wallet'],
        'payment_method_type': ['credit_card', 'debit_card', 'wallet', 'bank_transfer', 'unknown'],
        'entry_mode': ['chip', 'swipe', 'contactless', 'manual', 'online'],
        'condition': ['card_present', 'card_not_present'],
        'source_type': ['wallet', 'bank_account', 'card', 'external'],
        'destination_type': ['wallet', 'bank_account', 'card', 'external'],
        'transaction_purpose': ['deposit', 'withdrawal', 'transfer', 'payment', 'refund'],
        'response_code': ['00', '01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'],
    }
    
    for feature, categories in categorical_features.items():
        if feature in features:
            value = features[feature]
            for category in categories:
                transformed[f"{feature}_{category}"] = 1 if value == category else 0
    
    # Special handling for country (high-risk vs. low-risk)
    from apps.core.constants import HIGH_RISK_COUNTRIES
    if 'country' in features:
        transformed['is_high_risk_country'] = 1 if features['country'] in HIGH_RISK_COUNTRIES else 0
    
    # Special handling for MCC (suspicious vs. non-suspicious)
    from apps.core.constants import SUSPICIOUS_MCCS
    if 'mcc' in features:
        transformed['is_suspicious_mcc'] = 1 if features['mcc'] in SUSPICIOUS_MCCS else 0
    
    logger.debug(f"Transformed features into {len(transformed)} model-ready features")
    
    return transformed