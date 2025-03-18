"""
Script to create sample transaction data for testing without using signals.
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

# Import models directly
from django.db import connection
from apps.core.utils import generate_transaction_id


def create_sample_transactions(count=50):
    """Create sample transactions for testing using direct SQL."""
    print(f"Creating {count} sample transactions...")
    
    # Sample data
    currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
    user_ids = [f'user_{i}' for i in range(1, 11)]
    merchant_ids = [f'merchant_{i}' for i in range(1, 6)]
    device_ids = [f'device_{i}' for i in range(1, 8)]
    statuses = ['pending', 'approved', 'rejected', 'flagged']
    
    # Create transactions
    with connection.cursor() as cursor:
        for i in range(count):
            # Determine transaction type
            tx_type = random.choice(['pos', 'ecommerce', 'wallet'])
            
            # Common transaction data
            transaction_id = generate_transaction_id(f'tx_{tx_type}')
            amount = round(random.uniform(10, 1000), 2)
            currency = random.choice(currencies)
            user_id = random.choice(user_ids)
            timestamp = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            status = random.choice(statuses)
            is_flagged = status == 'flagged'
            risk_score = round(random.uniform(0, 100), 2)
            merchant_id = random.choice(merchant_ids)
            device_id = random.choice(device_ids)
            
            # Insert base transaction record
            cursor.execute("""
                INSERT INTO transactions_transaction (
                    transaction_id, transaction_type, channel, amount, currency, 
                    user_id, merchant_id, timestamp, status, risk_score, 
                    device_id, is_flagged, location_data, payment_method_data, 
                    metadata, flag_reason, review_status, reviewed_by, 
                    reviewed_at, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    NULL, NULL, NULL, NULL, %s, %s
                )
            """, [
                transaction_id,
                'acquiring' if tx_type in ['pos', 'ecommerce'] else 'wallet',
                tx_type,
                amount,
                currency,
                user_id,
                merchant_id,
                timestamp,
                status,
                risk_score,
                device_id,
                is_flagged,
                '{"country": "US", "city": "New York", "zip": "10001", "ip_address": "192.168.1.1"}',
                '{"type": "credit_card", "card_details": {"masked_card_number": "************1234"}}',
                '{}',
                timestamp,
                timestamp
            ])
            
            # Insert specific transaction type record
            if tx_type == 'pos':
                cursor.execute("""
                    INSERT INTO transactions_postransaction (
                        transaction_ptr_id, terminal_id, entry_mode, terminal_type,
                        attendance, condition, mcc, authorization_code, recurring_payment,
                        response_code, processor_response_code, avs_result, cvv_result,
                        response_time
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    transaction_id,
                    f'term_{random.randint(100, 999)}',
                    random.choice(['chip', 'swipe', 'contactless', 'manual']),
                    random.choice(['standard', 'mobile', 'unattended']),
                    random.choice(['attended', 'unattended']),
                    random.choice(['card_present', 'card_not_present']),
                    str(random.randint(1000, 9999)),
                    f'auth_{random.randint(100, 999)}',
                    random.choice([True, False]),
                    random.choice(['approved', 'declined', 'error']),
                    str(random.randint(0, 99)).zfill(2),
                    random.choice(['Y', 'N', 'P', 'U']),
                    random.choice(['M', 'N', 'P', 'U']),
                    random.uniform(100, 500)
                ])
            elif tx_type == 'ecommerce':
                cursor.execute("""
                    INSERT INTO transactions_ecommercetransaction (
                        transaction_ptr_id, website_url, is_3ds_verified, device_fingerprint,
                        shipping_address, billing_address, is_billing_shipping_match,
                        mcc, authorization_code, recurring_payment, response_code,
                        processor_response_code, avs_result, cvv_result, response_time
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    transaction_id,
                    f'https://example{random.randint(1, 10)}.com',
                    random.choice([True, False]),
                    f'fp_{random.randint(100000, 999999)}',
                    '{"street": "123 Main St", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US"}',
                    '{"street": "123 Main St", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US"}',
                    random.choice([True, False]),
                    str(random.randint(1000, 9999)),
                    f'auth_{random.randint(100, 999)}',
                    random.choice([True, False]),
                    random.choice(['approved', 'declined', 'error']),
                    str(random.randint(0, 99)).zfill(2),
                    random.choice(['Y', 'N', 'P', 'U']),
                    random.choice(['M', 'N', 'P', 'U']),
                    random.uniform(100, 500)
                ])
            else:  # wallet
                cursor.execute("""
                    INSERT INTO transactions_wallettransaction (
                        transaction_ptr_id, wallet_id, source_type, destination_type,
                        source_id, destination_id, transaction_purpose, is_internal
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    transaction_id,
                    f'wallet_{random.randint(100, 999)}',
                    random.choice(['wallet', 'bank_account', 'card', 'external']),
                    random.choice(['wallet', 'bank_account', 'card', 'external']),
                    f'source_{random.randint(100, 999)}',
                    f'dest_{random.randint(100, 999)}',
                    random.choice(['deposit', 'withdrawal', 'transfer', 'payment', 'refund']),
                    random.choice([True, False])
                ])
            
            print(f"Created {tx_type} transaction: {transaction_id}")
    
    print("Sample data creation complete!")


if __name__ == '__main__':
    # Get count from command line argument if provided
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    create_sample_transactions(count)