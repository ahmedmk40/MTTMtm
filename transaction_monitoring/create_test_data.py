"""
Script to create test data for the transaction network visualization.
"""

import os
import sys
import json
import random
import django
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Import Django models
from django.utils import timezone
from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction

# Sample data
USER_IDS = [
    "user_12345", "user_67890", "user_abcde", "user_fghij", "user_klmno",
    "high_risk_user_1", "high_risk_user_2", "high_risk_user_3", "high_risk_user_4", "high_risk_user_5"
]

MERCHANT_IDS = [
    "merchant_12345", "merchant_67890", "merchant_abcde", "merchant_fghij", "merchant_klmno",
    "merchant_high_risk", "merchant_medium_risk", "merchant_low_risk"
]

DEVICE_IDS = [
    "device_123", "device_456", "device_789", "device_abc", "device_def"
]

LOCATIONS = [
    {"city": "New York", "country": "US", "postal_code": "10001"},
    {"city": "Los Angeles", "country": "US", "postal_code": "90001"},
    {"city": "Chicago", "country": "US", "postal_code": "60601"},
    {"city": "London", "country": "GB", "postal_code": "EC1A 1BB"},
    {"city": "Paris", "country": "FR", "postal_code": "75001"},
    {"city": "Berlin", "country": "DE", "postal_code": "10115"},
    {"city": "Moscow", "country": "RU", "postal_code": "101000"},
    {"city": "Tokyo", "country": "JP", "postal_code": "100-0001"}
]

TERMINAL_IDS = [
    "term_123", "term_456", "term_789", "term_abc", "term_def"
]

WEBSITE_URLS = [
    "https://example.com", "https://shop.example.com", "https://store.example.org",
    "https://marketplace.example.net", "https://buy.example.io"
]

WALLET_IDS = [
    "wallet_12345", "wallet_67890", "wallet_abcde", "wallet_fghij", "wallet_klmno"
]

# Create test transactions
def create_test_transactions(count=50):
    """Create test transactions for network visualization."""
    print(f"Creating {count} test transactions...")
    
    # Get existing transaction IDs to avoid duplicates
    existing_ids = set(Transaction.objects.values_list('transaction_id', flat=True))
    
    # Create transactions
    for i in range(count):
        # Generate a unique transaction ID
        while True:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = ''.join(random.choices('0123456789abcdef', k=8))
            transaction_id = f"tx_{timestamp}_{unique_id}"
            if transaction_id not in existing_ids:
                existing_ids.add(transaction_id)
                break
        
        # Common transaction data
        transaction_type = random.choice(["acquiring", "wallet"])
        channel = random.choice(["pos", "ecommerce", "wallet"])
        amount = round(random.uniform(10, 5000), 2)
        currency = "USD"
        user_id = random.choice(USER_IDS)
        merchant_id = random.choice(MERCHANT_IDS)
        device_id = random.choice(DEVICE_IDS)
        location_data = random.choice(LOCATIONS)
        
        # Random timestamp within the last 30 days
        days_ago = random.randint(0, 30)
        timestamp = timezone.now() - timedelta(days=days_ago)
        
        # Payment method data
        payment_method_data = {
            "type": "credit_card",
            "card_details": {
                "card_number": "4111111111111111",
                "expiry_date": "12/25",
                "cvv": "123",
                "cardholder_name": "Test User"
            }
        }
        
        # Create transaction based on channel
        if channel == "pos":
            transaction = POSTransaction.objects.create(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                channel=channel,
                amount=amount,
                currency=currency,
                user_id=user_id,
                merchant_id=merchant_id,
                device_id=device_id,
                location_data=location_data,
                payment_method_data=payment_method_data,
                terminal_id=random.choice(TERMINAL_IDS),
                entry_mode=random.choice(["chip", "swipe", "contactless", "manual"]),
                terminal_type="countertop",
                attendance=random.choice(["attended", "unattended"]),
                condition=random.choice(["card_present", "card_not_present"]),
                timestamp=timestamp,
                status="pending"
            )
        elif channel == "ecommerce":
            transaction = EcommerceTransaction.objects.create(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                channel=channel,
                amount=amount,
                currency=currency,
                user_id=user_id,
                merchant_id=merchant_id,
                device_id=device_id,
                location_data=location_data,
                payment_method_data=payment_method_data,
                website_url=random.choice(WEBSITE_URLS),
                is_3ds_verified=random.choice([True, False]),
                device_fingerprint=f"fp_{unique_id}",
                shipping_address={
                    "street": "123 Main St",
                    "city": location_data["city"],
                    "country": location_data["country"],
                    "postal_code": location_data["postal_code"]
                },
                billing_address={
                    "street": "123 Main St",
                    "city": location_data["city"],
                    "country": location_data["country"],
                    "postal_code": location_data["postal_code"]
                },
                is_billing_shipping_match=True,
                timestamp=timestamp,
                status="pending"
            )
        else:  # wallet
            transaction = WalletTransaction.objects.create(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                channel=channel,
                amount=amount,
                currency=currency,
                user_id=user_id,
                device_id=device_id,
                location_data=location_data,
                payment_method_data=payment_method_data,
                wallet_id=random.choice(WALLET_IDS),
                source_type=random.choice(["wallet", "bank_account", "card"]),
                destination_type=random.choice(["wallet", "bank_account", "card"]),
                source_id=f"source_{unique_id}",
                destination_id=f"dest_{unique_id}",
                transaction_purpose=random.choice(["deposit", "withdrawal", "transfer", "payment"]),
                is_internal=random.choice([True, False]),
                timestamp=timestamp,
                status="pending"
            )
        
        # Randomly set risk score and flag status
        if random.random() < 0.2:  # 20% chance of being flagged
            transaction.risk_score = round(random.uniform(70, 95), 2)
            transaction.is_flagged = True
            transaction.flag_reason = "Test flagged transaction"
            transaction.status = "flagged"
        else:
            transaction.risk_score = round(random.uniform(10, 60), 2)
            transaction.is_flagged = False
            transaction.status = "approved"
        
        transaction.save()
        
        print(f"Created transaction: {transaction.transaction_id}")
    
    print(f"Created {count} test transactions successfully.")

if __name__ == "__main__":
    # Get count from command line argument or use default
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    create_test_transactions(count)