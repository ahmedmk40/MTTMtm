#!/usr/bin/env python
"""
Test script for enhanced ML integration with response codes.

This script tests the enhanced ML models with advanced features and SHAP explanations.
"""

import os
import sys
import django
import json
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Import Django models and services
from apps.transactions.models import Transaction, POSTransaction, WalletTransaction
from apps.ml_engine.services.prediction_service import get_fraud_prediction
from apps.ml_engine.ml_models.optimized_response_code_model import train_optimized_response_code_model
from apps.ml_engine.services.advanced_features import extract_advanced_features
from django.utils import timezone


def create_test_transaction(transaction_type, channel, response_code, amount=100.00, is_high_risk=False):
    """
    Create a test transaction with the specified response code.
    
    Args:
        transaction_type (str): Type of transaction
        channel (str): Transaction channel
        response_code (str): Response code
        amount (float): Transaction amount
        is_high_risk (bool): Whether to add high-risk attributes
        
    Returns:
        Transaction: The created transaction
    """
    transaction_id = f"test_tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{response_code}"
    
    # Common transaction data
    transaction_data = {
        'transaction_id': transaction_id,
        'transaction_type': transaction_type,
        'channel': channel,
        'amount': amount,
        'currency': 'USD',
        'user_id': 'test_user',
        'timestamp': timezone.now(),
        'response_code': response_code,
        'status': 'pending',
    }
    
    # Add high-risk attributes if specified
    location_data = {
        'country': 'RU' if is_high_risk else 'US',
        'city': 'Moscow' if is_high_risk else 'New York',
        'zip': '101000' if is_high_risk else '10001',
        'ip_address': '192.168.1.1'
    }
    
    # Create transaction based on channel
    if channel == 'pos':
        transaction = POSTransaction.objects.create(
            **transaction_data,
            merchant_id='TEST_MERCHANT',
            device_id='TEST_DEVICE',
            terminal_id='TEST_TERMINAL',
            entry_mode='manual' if is_high_risk else 'chip',
            terminal_type='POS Terminal',
            attendance='unattended' if is_high_risk else 'attended',
            condition='card_not_present' if is_high_risk else 'card_present',
            location_data=location_data,
            payment_method_data={
                'type': 'credit_card',
                'card_details': {
                    'masked_card_number': '************1111',
                    'cardholder_name': 'Test User',
                    'expiry_date': '12/25',
                    'is_new': True if is_high_risk else False
                }
            }
        )
    elif channel == 'wallet':
        transaction = WalletTransaction.objects.create(
            **transaction_data,
            wallet_id='TEST_WALLET',
            source_type='wallet',
            source_id='TEST_WALLET',
            destination_type='bank_account',
            destination_id='TEST_BANK',
            transaction_purpose='transfer',
            is_internal=False,
            location_data=location_data,
            payment_method_data={
                'type': 'wallet',
                'wallet_details': {
                    'wallet_type': 'digital',
                    'wallet_provider': 'test_provider',
                }
            }
        )
    else:
        raise ValueError(f"Unsupported channel: {channel}")
    
    return transaction


def test_advanced_features():
    """
    Test the advanced feature extraction.
    """
    print("Testing advanced feature extraction...")
    
    # Create a transaction with a high-risk response code
    transaction = create_test_transaction('purchase', 'pos', '43', 100.00, True)
    
    # Extract advanced features
    features = extract_advanced_features(transaction)
    
    print(f"Extracted {len(features)} advanced features:")
    for feature, value in features.items():
        print(f"  {feature}: {value}")
    
    return features


def test_optimized_model():
    """
    Test the optimized response code model.
    """
    print("\nTraining optimized response code model...")
    
    # Train the model
    model, metrics = train_optimized_response_code_model()
    
    print("Model metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value}")
    
    return model, metrics


def test_enhanced_prediction():
    """
    Test the enhanced prediction with SHAP explanations.
    """
    print("\nTesting enhanced prediction with SHAP explanations...")
    
    # Create test transactions with different response codes
    test_cases = [
        ('purchase', 'pos', '00', 100.00, False),  # Approved, low risk
        ('purchase', 'pos', '43', 100.00, True),   # Stolen card, high risk
    ]
    
    results = []
    
    for transaction_type, channel, response_code, amount, is_high_risk in test_cases:
        print(f"\nCreating {channel} transaction with response code {response_code}, high risk: {is_high_risk}")
        transaction = create_test_transaction(transaction_type, channel, response_code, amount, is_high_risk)
        
        print(f"Getting ML prediction for transaction {transaction.transaction_id}...")
        ml_results = get_fraud_prediction(transaction)
        
        # Print risk score and fraudulent status
        print(f"Risk Score: {ml_results['risk_score']:.2f}")
        print(f"Is Fraudulent: {ml_results['is_fraudulent']}")
        
        # Print model scores
        print("Model Scores:")
        for model, score in ml_results.get('model_scores', {}).items():
            print(f"  {model}: {score:.2f}")
        
        # Print response code explanation if available
        if 'response_code_explanation' in ml_results:
            explanation = ml_results['response_code_explanation']
            print("\nResponse Code Explanation:")
            print(f"  {explanation.get('explanation_text', '')}")
            
            print("\nRisk Factors:")
            for factor in explanation.get('risk_factors', [])[:3]:  # Show top 3 factors
                print(f"  {factor.get('factor')}: {factor.get('description')} ({factor.get('risk_level')} risk)")
        
        results.append({
            'transaction_id': transaction.transaction_id,
            'response_code': response_code,
            'is_high_risk': is_high_risk,
            'risk_score': ml_results['risk_score'],
            'is_fraudulent': ml_results['is_fraudulent'],
            'explanation': ml_results.get('response_code_explanation', {}).get('explanation_text', '')
        })
    
    return results


if __name__ == "__main__":
    # Test advanced features
    features = test_advanced_features()
    
    # Test optimized model
    try:
        model, metrics = test_optimized_model()
    except Exception as e:
        print(f"Error training optimized model: {str(e)}")
        print("Continuing with existing models...")
    
    # Test enhanced prediction
    results = test_enhanced_prediction()
    
    # Save results to file
    with open('enhanced_ml_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to enhanced_ml_results.json")