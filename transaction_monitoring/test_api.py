"""
Script to test the transaction monitoring API.
"""

import os
import sys
import json
import uuid
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Import Django models and services
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.transactions.models import Transaction, POSTransaction
from apps.ml_engine.services.prediction_service import get_fraud_prediction
from apps.rule_engine.services import apply_rules

# Create a test transaction
def create_test_transaction():
    """Create a test transaction and process it."""
    print("Creating test transaction...")
    
    # Create a POS transaction with a unique ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    transaction = POSTransaction.objects.create(
        transaction_id=f"tx_{timestamp}_{unique_id}",
        transaction_type="acquiring",
        channel="pos",
        amount=2500.00,
        currency="USD",
        user_id="high_risk_user_test",
        merchant_id="merchant_high_risk",
        device_id="device_test",
        location_data={
            "city": "New York",
            "country": "US",
            "postal_code": "10001"
        },
        payment_method_data={
            "type": "credit_card",
            "card_details": {
                "card_number": "4111111111111111",
                "expiry_date": "12/25",
                "cvv": "123",
                "cardholder_name": "High Risk Test"
            }
        },
        terminal_id="term_test",
        entry_mode="chip",
        terminal_type="countertop",
        attendance="attended",
        condition="card_present",
        timestamp=django.utils.timezone.now(),
        status="pending"
    )
    
    print(f"Transaction created: {transaction.transaction_id}")
    
    # Process the transaction
    print("\nApplying rules...")
    rule_results = apply_rules(transaction)
    print(f"Rule results: {json.dumps(rule_results, indent=2)}")
    
    print("\nGetting ML prediction...")
    ml_results = get_fraud_prediction(transaction)
    
    # Convert to JSON-serializable format
    serializable_results = {
        'risk_score': float(ml_results.get('risk_score', 0)),
        'is_fraudulent': bool(ml_results.get('is_fraudulent', False)),
        'execution_time': float(ml_results.get('execution_time', 0)),
        'model_name': ml_results.get('model_name'),
        'model_version': ml_results.get('model_version'),
    }
    
    print(f"ML results: {json.dumps(serializable_results, indent=2)}")
    
    # Update transaction with results
    transaction.risk_score = ml_results.get('risk_score', 0)
    transaction.is_flagged = rule_results.get('is_flagged', False) or ml_results.get('is_fraudulent', False)
    
    if transaction.is_flagged:
        transaction.flag_reason = rule_results.get('flag_reason') or 'ML model flagged as high risk'
        transaction.status = 'flagged'
    else:
        transaction.status = 'approved'
    
    transaction.save()
    
    print(f"\nTransaction updated: {transaction.transaction_id}")
    print(f"Status: {transaction.status}")
    print(f"Risk Score: {transaction.risk_score}")
    print(f"Is Flagged: {transaction.is_flagged}")
    print(f"Flag Reason: {transaction.flag_reason}")
    
    return transaction

if __name__ == "__main__":
    create_test_transaction()