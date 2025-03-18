"""
Block service for the Fraud Engine.

This service is responsible for checking if a transaction should be blocked
based on blocklist entries.
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from django.db import models
from apps.core.utils import hash_sensitive_data
from ..models import BlockList

logger = logging.getLogger(__name__)


def check_blocklist(transaction) -> Dict[str, Any]:
    """
    Check if any entity in the transaction is on the blocklist.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the blocklist check result
    """
    result = {
        'is_blocked': False,
        'reason': '',
        'blocked_entities': []
    }
    
    # Get active blocklist entries
    blocklist_entries = BlockList.objects.filter(
        is_active=True
    ).filter(
        # Filter out expired entries
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    )
    
    # Check user_id
    user_blocklist = blocklist_entries.filter(
        entity_type='user_id',
        entity_value=transaction.user_id
    ).first()
    
    if user_blocklist:
        result['is_blocked'] = True
        result['reason'] = user_blocklist.reason
        result['blocked_entities'].append({
            'type': 'user_id',
            'value': transaction.user_id
        })
        logger.info(f"Transaction {transaction.transaction_id} blocked: User {transaction.user_id} is on blocklist")
        return result
    
    # Check device_id
    if hasattr(transaction, 'device_id') and transaction.device_id:
        device_blocklist = blocklist_entries.filter(
            entity_type='device_id',
            entity_value=transaction.device_id
        ).first()
        
        if device_blocklist:
            result['is_blocked'] = True
            result['reason'] = device_blocklist.reason
            result['blocked_entities'].append({
                'type': 'device_id',
                'value': transaction.device_id
            })
            logger.info(f"Transaction {transaction.transaction_id} blocked: Device {transaction.device_id} is on blocklist")
            return result
    
    # Check IP address
    if hasattr(transaction, 'location_data') and transaction.location_data:
        ip_address = transaction.location_data.get('ip_address')
        if ip_address:
            ip_blocklist = blocklist_entries.filter(
                entity_type='ip_address',
                entity_value=ip_address
            ).first()
            
            if ip_blocklist:
                result['is_blocked'] = True
                result['reason'] = ip_blocklist.reason
                result['blocked_entities'].append({
                    'type': 'ip_address',
                    'value': ip_address
                })
                logger.info(f"Transaction {transaction.transaction_id} blocked: IP {ip_address} is on blocklist")
                return result
    
    # Check merchant_id
    if hasattr(transaction, 'merchant_id') and transaction.merchant_id:
        merchant_blocklist = blocklist_entries.filter(
            entity_type='merchant_id',
            entity_value=transaction.merchant_id
        ).first()
        
        if merchant_blocklist:
            result['is_blocked'] = True
            result['reason'] = merchant_blocklist.reason
            result['blocked_entities'].append({
                'type': 'merchant_id',
                'value': transaction.merchant_id
            })
            logger.info(f"Transaction {transaction.transaction_id} blocked: Merchant {transaction.merchant_id} is on blocklist")
            return result
    
    # Check card number (if present)
    if hasattr(transaction, 'payment_method_data') and transaction.payment_method_data:
        payment_method = transaction.payment_method_data.get('type')
        
        if payment_method in ['credit_card', 'debit_card']:
            card_details = transaction.payment_method_data.get('card_details', {})
            if card_details and 'card_number' in card_details:
                # Hash the card number for comparison with blocklist
                card_hash = hash_sensitive_data(card_details['card_number'])
                
                card_blocklist = blocklist_entries.filter(
                    entity_type='card_number',
                    entity_value=card_hash
                ).first()
                
                if card_blocklist:
                    result['is_blocked'] = True
                    result['reason'] = card_blocklist.reason
                    result['blocked_entities'].append({
                        'type': 'card_number',
                        'value': 'MASKED'  # Don't include actual card number in result
                    })
                    logger.info(f"Transaction {transaction.transaction_id} blocked: Card is on blocklist")
                    return result
    
    # Check email (if present in metadata)
    if hasattr(transaction, 'metadata') and transaction.metadata:
        email = transaction.metadata.get('customer_email')
        if email:
            email_blocklist = blocklist_entries.filter(
                entity_type='email',
                entity_value=email
            ).first()
            
            if email_blocklist:
                result['is_blocked'] = True
                result['reason'] = email_blocklist.reason
                result['blocked_entities'].append({
                    'type': 'email',
                    'value': email
                })
                logger.info(f"Transaction {transaction.transaction_id} blocked: Email {email} is on blocklist")
                return result
    
    return result


def add_to_blocklist(entity_type, entity_value, reason, added_by, expires_at=None):
    """
    Add an entity to the blocklist.
    
    Args:
        entity_type: Type of entity (user_id, card_number, etc.)
        entity_value: Value of the entity
        reason: Reason for blocking
        added_by: User who added the entity to the blocklist
        expires_at: Expiration date (optional)
        
    Returns:
        The created BlockList entry
    """
    # Hash card numbers
    if entity_type == 'card_number':
        entity_value = hash_sensitive_data(entity_value)
    
    # Create or update blocklist entry
    blocklist_entry, created = BlockList.objects.update_or_create(
        entity_type=entity_type,
        entity_value=entity_value,
        defaults={
            'reason': reason,
            'is_active': True,
            'expires_at': expires_at,
            'added_by': added_by
        }
    )
    
    logger.info(
        f"{'Added' if created else 'Updated'} blocklist entry: "
        f"{entity_type} {entity_value} by {added_by}"
    )
    
    return blocklist_entry