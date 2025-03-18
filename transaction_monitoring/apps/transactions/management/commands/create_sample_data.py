"""
Management command to create sample transaction data for testing.
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from apps.core.utils import generate_transaction_id


class Command(BaseCommand):
    help = 'Create sample transaction data for testing'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=50,
                            help='Number of transactions to create (default: 50)')

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Creating {count} sample transactions...")
        
        # Sample data
        currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        user_ids = [f'user_{i}' for i in range(1, 11)]
        merchant_ids = [f'merchant_{i}' for i in range(1, 6)]
        device_ids = [f'device_{i}' for i in range(1, 8)]
        statuses = ['pending', 'approved', 'rejected', 'flagged']
        
        # Temporarily disconnect signals
        from django.db.models.signals import post_save
        from apps.transactions.signals import transaction_post_save
        
        post_save.disconnect(transaction_post_save, sender=Transaction)
        post_save.disconnect(transaction_post_save, sender=POSTransaction)
        post_save.disconnect(transaction_post_save, sender=EcommerceTransaction)
        post_save.disconnect(transaction_post_save, sender=WalletTransaction)
        
        try:
            # Create transactions in a single transaction to speed things up
            with db_transaction.atomic():
                for i in range(count):
                    # Determine transaction type
                    tx_type = random.choice(['pos', 'ecommerce', 'wallet'])
                    
                    # Common transaction data
                    amount = Decimal(str(round(random.uniform(10, 1000), 2)))
                    currency = random.choice(currencies)
                    user_id = random.choice(user_ids)
                    timestamp = timezone.now() - timedelta(days=random.randint(0, 30), 
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
                                    'masked_card_number': f'************{random.randint(1000, 9999)}',
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
                                    'masked_card_number': f'************{random.randint(1000, 9999)}',
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
                    self.stdout.write(f"Created {tx_type} transaction: {transaction.transaction_id}")
        finally:
            # Reconnect signals
            post_save.connect(transaction_post_save, sender=Transaction)
            post_save.connect(transaction_post_save, sender=POSTransaction)
            post_save.connect(transaction_post_save, sender=EcommerceTransaction)
            post_save.connect(transaction_post_save, sender=WalletTransaction)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} sample transactions!"))