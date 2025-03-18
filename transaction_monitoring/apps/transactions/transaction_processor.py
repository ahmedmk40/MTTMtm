"""
Transaction processor module for handling transaction creation without Celery.
"""

from django.utils import timezone
from apps.core.utils import generate_transaction_id
from apps.transactions.models import POSTransaction, EcommerceTransaction, WalletTransaction
from apps.fraud_engine.tasks import process_transaction


def create_transaction(form_data):
    """
    Create a transaction based on form data.
    
    Args:
        form_data: Cleaned form data from TransactionCreateForm
        
    Returns:
        The created transaction object
    """
    # Get form data
    transaction_type = form_data.get('transaction_type')
    channel = form_data.get('channel')
    amount = form_data.get('amount')
    currency = form_data.get('currency')
    user_id = form_data.get('user_id')
    merchant_id = form_data.get('merchant_id', '')
    device_id = form_data.get('device_id', '')
    
    # Generate transaction ID
    transaction_id = generate_transaction_id()
    
    # Create transaction based on channel
    if channel == 'pos':
        # Create POS Transaction
        transaction = POSTransaction.objects.create(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            channel=channel,
            amount=amount,
            currency=currency,
            user_id=user_id,
            timestamp=timezone.now(),
            merchant_id=merchant_id,
            device_id=device_id,
            status='pending',
            terminal_id=form_data.get('terminal_id', ''),
            entry_mode=form_data.get('entry_mode', ''),
            terminal_type=form_data.get('terminal_type', ''),
            attendance=form_data.get('attendance', ''),
            condition=form_data.get('condition', ''),
        )
        
        # Create location data
        location_data = {}
        if form_data.get('location_city'):
            location_data['city'] = form_data.get('location_city')
        if form_data.get('location_country'):
            location_data['country'] = form_data.get('location_country')
        if form_data.get('location_postal_code'):
            location_data['postal_code'] = form_data.get('location_postal_code')
        if form_data.get('location_latitude') and form_data.get('location_longitude'):
            location_data['latitude'] = float(form_data.get('location_latitude'))
            location_data['longitude'] = float(form_data.get('location_longitude'))
        
        # Create payment method data
        payment_method_data = {
            'type': form_data.get('payment_method_type', '')
        }
        
        if form_data.get('payment_method_type') in ['credit_card', 'debit_card']:
            payment_method_data['card_details'] = {
                'card_number': form_data.get('card_number', ''),
                'expiry_date': form_data.get('card_expiry', ''),
                'cvv': form_data.get('card_cvv', ''),
                'cardholder_name': form_data.get('cardholder_name', '')
            }
        
        # Create metadata
        metadata = {}
        if form_data.get('metadata_notes'):
            metadata['notes'] = form_data.get('metadata_notes')
        
        # Set JSON fields
        transaction.location_data = location_data
        transaction.payment_method_data = payment_method_data
        transaction.metadata = metadata
        
        # Save transaction
        transaction.save()
        
    elif channel == 'ecommerce':
        # Create E-commerce Transaction
        transaction = EcommerceTransaction.objects.create(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            channel=channel,
            amount=amount,
            currency=currency,
            user_id=user_id,
            timestamp=timezone.now(),
            merchant_id=merchant_id,
            device_id=device_id,
            status='pending',
            website_url=form_data.get('website_url', ''),
            is_3ds_verified=form_data.get('is_3ds_verified', False),
            device_fingerprint=form_data.get('device_fingerprint', ''),
            is_billing_shipping_match=form_data.get('billing_same_as_shipping', True),
        )
        
        # Create location data
        location_data = {}
        if form_data.get('location_city'):
            location_data['city'] = form_data.get('location_city')
        if form_data.get('location_country'):
            location_data['country'] = form_data.get('location_country')
        if form_data.get('location_postal_code'):
            location_data['postal_code'] = form_data.get('location_postal_code')
        if form_data.get('location_latitude') and form_data.get('location_longitude'):
            location_data['latitude'] = float(form_data.get('location_latitude'))
            location_data['longitude'] = float(form_data.get('location_longitude'))
        
        # Create payment method data
        payment_method_data = {
            'type': form_data.get('payment_method_type', '')
        }
        
        if form_data.get('payment_method_type') in ['credit_card', 'debit_card']:
            payment_method_data['card_details'] = {
                'card_number': form_data.get('card_number', ''),
                'expiry_date': form_data.get('card_expiry', ''),
                'cvv': form_data.get('card_cvv', ''),
                'cardholder_name': form_data.get('cardholder_name', '')
            }
        
        # Create shipping address
        shipping_address = {
            'street': form_data.get('shipping_street', ''),
            'city': form_data.get('shipping_city', ''),
            'state': form_data.get('shipping_state', ''),
            'postal_code': form_data.get('shipping_postal_code', ''),
            'country': form_data.get('shipping_country', '')
        }
        
        # Create billing address
        if form_data.get('billing_same_as_shipping', True):
            billing_address = shipping_address.copy()
        else:
            billing_address = {
                'street': form_data.get('billing_street', ''),
                'city': form_data.get('billing_city', ''),
                'state': form_data.get('billing_state', ''),
                'postal_code': form_data.get('billing_postal_code', ''),
                'country': form_data.get('billing_country', '')
            }
        
        # Create metadata
        metadata = {}
        if form_data.get('metadata_notes'):
            metadata['notes'] = form_data.get('metadata_notes')
        
        # Set JSON fields
        transaction.location_data = location_data
        transaction.payment_method_data = payment_method_data
        transaction.shipping_address = shipping_address
        transaction.billing_address = billing_address
        transaction.metadata = metadata
        
        # Save transaction
        transaction.save()
        
    elif channel == 'wallet':
        # Create Wallet Transaction
        transaction = WalletTransaction.objects.create(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            channel=channel,
            amount=amount,
            currency=currency,
            user_id=user_id,
            timestamp=timezone.now(),
            merchant_id=merchant_id,
            device_id=device_id,
            status='pending',
            wallet_id=form_data.get('wallet_id', ''),
            source_type=form_data.get('source_type', ''),
            destination_type=form_data.get('destination_type', ''),
            source_id=form_data.get('source_id', ''),
            destination_id=form_data.get('destination_id', ''),
            transaction_purpose=form_data.get('transaction_purpose', ''),
            is_internal=form_data.get('is_internal', False),
        )
        
        # Create location data
        location_data = {}
        if form_data.get('location_city'):
            location_data['city'] = form_data.get('location_city')
        if form_data.get('location_country'):
            location_data['country'] = form_data.get('location_country')
        if form_data.get('location_postal_code'):
            location_data['postal_code'] = form_data.get('location_postal_code')
        if form_data.get('location_latitude') and form_data.get('location_longitude'):
            location_data['latitude'] = float(form_data.get('location_latitude'))
            location_data['longitude'] = float(form_data.get('location_longitude'))
        
        # Create payment method data
        payment_method_data = {
            'type': form_data.get('payment_method_type', '')
        }
        
        # Create metadata
        metadata = {}
        if form_data.get('metadata_notes'):
            metadata['notes'] = form_data.get('metadata_notes')
        
        # Set JSON fields
        transaction.location_data = location_data
        transaction.payment_method_data = payment_method_data
        transaction.metadata = metadata
        
        # Save transaction
        transaction.save()
        
    else:
        raise ValueError(f"Invalid channel: {channel}")
    
    # Process the transaction directly (no Celery)
    try:
        # Simulate fraud detection processing
        import random
        
        # Generate a random risk score between 1 and 100
        risk_score = random.randint(1, 100)
        
        # Update transaction with results
        transaction.risk_score = risk_score
        transaction.is_flagged = risk_score > 80  # Flag if risk score is high
        transaction.save()
        
        # Log the processing
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Transaction {transaction.transaction_id} processed with risk score: {risk_score}")
    except Exception as e:
        # Log the error but don't raise it to avoid breaking the transaction creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}", exc_info=True)
    
    return transaction