#!/usr/bin/env python
"""
Test script for response code visualizations.

This script generates and saves various visualizations for response code patterns.
"""

import os
import sys
import django
import base64
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Import visualization service
from apps.ml_engine.services.visualization_service import (
    generate_response_code_distribution_plot,
    generate_response_code_time_series,
    generate_response_code_heatmap,
    generate_risk_score_by_response_code,
    generate_response_code_sequence_plot,
    generate_response_code_sankey,
    generate_shap_summary_plot
)

# Import other services
from apps.ml_engine.services.prediction_service import get_fraud_prediction
from apps.transactions.models import Transaction, POSTransaction, WalletTransaction
from django.utils import timezone


def save_visualization(img_str, filename):
    """
    Save a base64-encoded image to a file.
    
    Args:
        img_str: Base64-encoded image string
        filename: Output filename
    """
    if img_str:
        # Create visualizations directory if it doesn't exist
        os.makedirs('visualizations', exist_ok=True)
        
        # Decode and save image
        with open(f'visualizations/{filename}', 'wb') as f:
            f.write(base64.b64decode(img_str))
        
        print(f"Saved visualization to visualizations/{filename}")
    else:
        print(f"Failed to generate visualization for {filename}")


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


def create_test_transactions():
    """
    Create a set of test transactions with various response codes.
    """
    print("Creating test transactions...")
    
    # Test cases: (transaction_type, channel, response_code, amount, is_high_risk)
    test_cases = [
        ('purchase', 'pos', '00', 100.00, False),  # Approved, low risk
        ('purchase', 'pos', '51', 100.00, False),  # Insufficient funds, medium risk
        ('purchase', 'pos', '05', 100.00, False),  # Do not honor, medium risk
        ('purchase', 'pos', '14', 100.00, False),  # Invalid card, high risk
        ('purchase', 'pos', '43', 100.00, True),   # Stolen card, high risk
        ('purchase', 'ecommerce', '00', 100.00, False),  # Approved, low risk
        ('purchase', 'ecommerce', '51', 100.00, False),  # Insufficient funds, medium risk
        ('purchase', 'ecommerce', '14', 100.00, True),   # Invalid card, high risk
        ('wallet_to_bank', 'wallet', '00', 100.00, False),  # Approved, low risk
        ('wallet_to_bank', 'wallet', '01', 100.00, False),  # Insufficient balance, medium risk
        ('wallet_to_bank', 'wallet', '94', 100.00, True),   # Account not found, high risk
    ]
    
    transactions = []
    
    for transaction_type, channel, response_code, amount, is_high_risk in test_cases:
        print(f"Creating {channel} transaction with response code {response_code}, high risk: {is_high_risk}")
        transaction = create_test_transaction(transaction_type, channel, response_code, amount, is_high_risk)
        transactions.append(transaction)
    
    return transactions


def test_visualizations():
    """
    Test all visualization functions.
    """
    print("Testing response code visualizations...")
    
    # Create test transactions
    transactions = create_test_transactions()
    
    # Generate and save distribution plot
    print("\nGenerating response code distribution plot...")
    img_str = generate_response_code_distribution_plot(days=30)
    save_visualization(img_str, 'response_code_distribution.png')
    
    # Generate and save time series plot
    print("\nGenerating response code time series plot...")
    img_str = generate_response_code_time_series(days=30, interval='day')
    save_visualization(img_str, 'response_code_time_series.png')
    
    # Generate and save heatmap
    print("\nGenerating response code heatmap...")
    img_str = generate_response_code_heatmap(days=30)
    save_visualization(img_str, 'response_code_heatmap.png')
    
    # Generate and save risk score plot
    print("\nGenerating risk score by response code plot...")
    
    # First, get ML predictions for the transactions
    for transaction in transactions:
        print(f"Getting ML prediction for transaction {transaction.transaction_id}...")
        get_fraud_prediction(transaction)
    
    img_str = generate_risk_score_by_response_code(days=30)
    save_visualization(img_str, 'risk_score_by_response_code.png')
    
    # Generate and save sequence plot
    print("\nGenerating response code sequence plot...")
    img_str = generate_response_code_sequence_plot(user_id='test_user', days=30)
    save_visualization(img_str, 'response_code_sequence.png')
    
    # Generate and save Sankey diagram
    print("\nGenerating response code Sankey diagram...")
    img_str = generate_response_code_sankey(days=30)
    save_visualization(img_str, 'response_code_sankey.png')
    
    print("\nAll visualizations completed!")


if __name__ == "__main__":
    test_visualizations()