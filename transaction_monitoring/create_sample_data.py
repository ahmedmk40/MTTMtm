"""
Script to create sample transaction data for testing.
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Disable signals temporarily to avoid circular imports
from django.db.models.signals import post_save
from django.dispatch import receiver

# Store the original receivers
receivers = post_save.receivers
post_save.receivers = []

from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from apps.core.utils import generate_transaction_id

# Restore the original receivers
post_save.receivers = receivers


def create_sample_transactions(count=50):
    """Create sample transactions for testing."""
    print(f"Creating {count} sample transactions...")
    
    # Sample data
    currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
    user_ids = [f'user_{i}' for i in range(1, 11)]
    merchant_ids = [f'merchant_{i}' for i in range(1, 6)]
    device_ids = [f'device_{i}' for i in range(1, 8)]
    statuses = ['pending', 'approved', 'rejected', 'flagged']
    
    # Create transactions
    for i in range(count):
        # Determine transaction type
        tx_type = random.choice(['pos', 'ecommerce', 'wallet'])
        
        # Common transaction data
        amount = Decimal(str(round(random.uniform(10, 1000), 2)))
        currency = random.choice(currencies)
        user_id = random.choice(user_ids)
        timestamp = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), 
                                                          hours=random.randint(0, 23), 
                                                          minutes=random.randint(0, 59))
        status = random.choice(statuses)
        is_flagged = status == 'flagged'
        risk_score = Decimal(str(round(random.uniform(0, 100), 2)))
        
        # Create transaction based on type
        if tx_type == 'pos':
            transaction = POSTransaction(
                transaction_id=generate_transaction_id('tx_pos'),
                transaction_type='acquiring',
                channel='pos',
                amount=amount,
                currency=currency,
                user_id=user_id,
                merchant_id=random.choice(merchant_ids),
                timestamp=timestamp,
                status=status,
                risk_score=risk_score,
                device_id=random.choice(device_ids),
                is_flagged=is_flagged,
                location_data={
                    'country': 'US',
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'zip': random.choice(['10001', '90001', '60601', '77001', '85001']),
                    'ip_address': f'192.168.1.{random.randint(1, 255)}'
                },
                payment_method_data={
                    'type': 'credit_card',
                    'card_details': {
                        'card_number': f'41111111111111{random.randint(10, 99)}',
                        'expiry_month': str(random.randint(1, 12)).zfill(2),
                        'expiry_year': str(random.randint(2023, 2030)),
                        'cardholder_name': f'User {user_id}',
                        'cvv': str(random.randint(100, 999)),
                        'is_new': random.choice([True, False])
                    }
                },
                terminal_id=f'term_{random.randint(100, 999)}',
                entry_mode=random.choice(['chip', 'swipe', 'contactless', 'manual']),
                terminal_type=random.choice(['standard', 'mobile', 'unattended']),
                attendance=random.choice(['attended', 'unattended']),
                condition=random.choice(['card_present', 'card_not_present']),
                mcc=str(random.randint(1000, 9999)),
                authorization_code=f'auth_{random.randint(100, 999)}',
                recurring_payment=random.choice([True, False]),
                response_code=random.choice(['approved', 'declined', 'error']),
                processor_response_code=str(random.randint(0, 99)).zfill(2),
                avs_result=random.choice(['Y', 'N', 'P', 'U']),
                cvv_result=random.choice(['M', 'N', 'P', 'U']),
                response_time=random.uniform(100, 500)
            )
        elif tx_type == 'ecommerce':
            transaction = EcommerceTransaction(
                transaction_id=generate_transaction_id('tx_ecom'),
                transaction_type='acquiring',
                channel='ecommerce',
                amount=amount,
                currency=currency,
                user_id=user_id,
                merchant_id=random.choice(merchant_ids),
                timestamp=timestamp,
                status=status,
                risk_score=risk_score,
                device_id=random.choice(device_ids),
                is_flagged=is_flagged,
                location_data={
                    'country': 'US',
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'zip': random.choice(['10001', '90001', '60601', '77001', '85001']),
                    'ip_address': f'192.168.1.{random.randint(1, 255)}'
                },
                payment_method_data={
                    'type': 'credit_card',
                    'card_details': {
                        'card_number': f'41111111111111{random.randint(10, 99)}',
                        'expiry_month': str(random.randint(1, 12)).zfill(2),
                        'expiry_year': str(random.randint(2023, 2030)),
                        'cardholder_name': f'User {user_id}',
                        'cvv': str(random.randint(100, 999)),
                        'is_new': random.choice([True, False])
                    }
                },
                website_url=f'https://example{random.randint(1, 10)}.com',
                is_3ds_verified=random.choice([True, False]),
                device_fingerprint=f'fp_{random.randint(100000, 999999)}',
                shipping_address={
                    'street': f'{random.randint(1, 999)} Main St',
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'state': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
                    'postal_code': random.choice(['10001', '90001', '60601', '77001', '85001']),
                    'country': 'US'
                },
                billing_address={
                    'street': f'{random.randint(1, 999)} Main St',
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'state': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
                    'postal_code': random.choice(['10001', '90001', '60601', '77001', '85001']),
                    'country': 'US'
                },
                is_billing_shipping_match=random.choice([True, False]),
                mcc=str(random.randint(1000, 9999)),
                authorization_code=f'auth_{random.randint(100, 999)}',
                recurring_payment=random.choice([True, False]),
                response_code=random.choice(['approved', 'declined', 'error']),
                processor_response_code=str(random.randint(0, 99)).zfill(2),
                avs_result=random.choice(['Y', 'N', 'P', 'U']),
                cvv_result=random.choice(['M', 'N', 'P', 'U']),
                response_time=random.uniform(100, 500)
            )
        else:  # wallet
            transaction = WalletTransaction(
                transaction_id=generate_transaction_id('tx_wallet'),
                transaction_type='wallet',
                channel='wallet',
                amount=amount,
                currency=currency,
                user_id=user_id,
                timestamp=timestamp,
                status=status,
                risk_score=risk_score,
                device_id=random.choice(device_ids),
                is_flagged=is_flagged,
                location_data={
                    'country': 'US',
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'zip': random.choice(['10001', '90001', '60601', '77001', '85001']),
                    'ip_address': f'192.168.1.{random.randint(1, 255)}',
                    'latitude': round(random.uniform(25, 48), 4),
                    'longitude': round(random.uniform(-125, -70), 4)
                },
                payment_method_data={
                    'type': 'wallet',
                    'wallet_details': {
                        'wallet_type': 'digital',
                        'wallet_provider': random.choice(['example_wallet', 'fast_pay', 'money_app'])
                    }
                },
                wallet_id=f'wallet_{random.randint(100, 999)}',
                source_type=random.choice(['wallet', 'bank_account', 'card', 'external']),
                destination_type=random.choice(['wallet', 'bank_account', 'card', 'external']),
                source_id=f'source_{random.randint(100, 999)}',
                destination_id=f'dest_{random.randint(100, 999)}',
                transaction_purpose=random.choice(['deposit', 'withdrawal', 'transfer', 'payment', 'refund']),
                is_internal=random.choice([True, False])
            )
        
        transaction.save()
        print(f"Created {tx_type} transaction: {transaction.transaction_id}")
    
    print("Sample data creation complete!")


if __name__ == '__main__':
    # Get count from command line argument if provided
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    create_sample_transactions(count)