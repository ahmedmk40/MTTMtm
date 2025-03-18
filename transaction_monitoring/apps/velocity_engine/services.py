"""
Services for the Velocity Engine app.
"""

import time
import logging
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction, models
from django.db.models import F
from .models import VelocityRule, VelocityCounter, VelocityAlert
from apps.core.utils import hash_sensitive_data
from apps.core.constants import (
    TIME_WINDOW_5_MIN,
    TIME_WINDOW_15_MIN,
    TIME_WINDOW_1_HOUR,
    TIME_WINDOW_6_HOURS,
    TIME_WINDOW_24_HOURS,
    TIME_WINDOW_7_DAYS,
    TIME_WINDOW_30_DAYS,
)

logger = logging.getLogger(__name__)


def check_velocity(transaction_obj) -> Dict[str, Any]:
    """
    Check transaction velocity against rules.
    
    Args:
        transaction_obj: The transaction object
        
    Returns:
        Dictionary with the velocity check result
    """
    start_time = time.time()
    
    # Initialize result
    result = {
        'triggered_rules': [],
        'risk_score': 0.0,
        'execution_time': 0.0,
        'rules_evaluated': 0,
        'rules_triggered': 0,
    }
    
    # Get active velocity rules applicable to this transaction channel
    channel = transaction_obj.channel
    rules = VelocityRule.objects.filter(is_active=True)
    
    if channel == 'pos':
        rules = rules.filter(applies_to_pos=True)
    elif channel == 'ecommerce':
        rules = rules.filter(applies_to_ecommerce=True)
    elif channel == 'wallet':
        rules = rules.filter(applies_to_wallet=True)
    
    # Apply amount filters if applicable
    amount = float(transaction_obj.amount)
    rules = rules.filter(
        (models.Q(min_amount__isnull=True) | models.Q(min_amount__lte=amount)) &
        (models.Q(max_amount__isnull=True) | models.Q(max_amount__gte=amount))
    )
    
    # Track the highest risk score from triggered rules
    max_risk_score = 0.0
    
    # Process each rule
    for rule in rules:
        rule_start_time = time.time()
        
        # Get entity value based on entity type
        entity_value = get_entity_value(transaction_obj, rule.entity_type)
        
        if entity_value:
            # Increment velocity counter
            counter = increment_counter(rule.entity_type, entity_value)
            
            # Get the count for the rule's time window
            count = get_count_for_window(counter, rule.time_window)
            
            # Check if threshold is exceeded
            if count > rule.threshold:
                # Create alert
                alert = VelocityAlert.objects.create(
                    transaction_id=transaction_obj.transaction_id,
                    rule=rule,
                    entity_type=rule.entity_type,
                    entity_value=entity_value if rule.entity_type != 'card_number' else 'MASKED',
                    count=count,
                    threshold=rule.threshold,
                    time_window=rule.time_window
                )
                
                # Update rule metrics
                rule.hit_count += 1
                rule.last_triggered = timezone.now()
                rule.save(update_fields=['hit_count', 'last_triggered'])
                
                # Add to triggered rules
                result['triggered_rules'].append({
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'rule_type': 'velocity',
                    'action': rule.action,
                    'risk_score': float(rule.risk_score),
                    'entity_type': rule.entity_type,
                    'time_window': rule.time_window,
                    'threshold': rule.threshold,
                    'count': count
                })
                
                # Update max risk score
                max_risk_score = max(max_risk_score, float(rule.risk_score))
                
                # Increment triggered count
                result['rules_triggered'] += 1
        
        # Increment evaluated count
        result['rules_evaluated'] += 1
    
    # Set the risk score to the highest from triggered rules
    result['risk_score'] = max_risk_score
    
    # Calculate total execution time in milliseconds
    result['execution_time'] = (time.time() - start_time) * 1000
    
    logger.info(
        f"Velocity check for transaction {transaction_obj.transaction_id}: "
        f"{result['rules_triggered']} of {result['rules_evaluated']} rules triggered "
        f"in {result['execution_time']:.2f}ms"
    )
    
    return result


def get_entity_value(transaction_obj, entity_type: str) -> str:
    """
    Get the entity value from a transaction based on entity type.
    
    Args:
        transaction_obj: The transaction object
        entity_type: The type of entity to extract
        
    Returns:
        The entity value or None if not found
    """
    if entity_type == 'user_id':
        return transaction_obj.user_id
    
    elif entity_type == 'card_number':
        if hasattr(transaction_obj, 'payment_method_data') and transaction_obj.payment_method_data:
            payment_method = transaction_obj.payment_method_data.get('type')
            if payment_method in ['credit_card', 'debit_card']:
                card_details = transaction_obj.payment_method_data.get('card_details', {})
                if card_details and 'card_number' in card_details:
                    # Hash the card number for consistent lookups
                    return hash_sensitive_data(card_details['card_number'])
    
    elif entity_type == 'device_id':
        return getattr(transaction_obj, 'device_id', None)
    
    elif entity_type == 'ip_address':
        if hasattr(transaction_obj, 'location_data') and transaction_obj.location_data:
            return transaction_obj.location_data.get('ip_address')
    
    elif entity_type == 'merchant_id':
        return getattr(transaction_obj, 'merchant_id', None)
    
    elif entity_type == 'email':
        if hasattr(transaction_obj, 'metadata') and transaction_obj.metadata:
            return transaction_obj.metadata.get('customer_email')
    
    return None


def increment_counter(entity_type: str, entity_value: str) -> VelocityCounter:
    """
    Increment velocity counters for an entity.
    
    Args:
        entity_type: The type of entity
        entity_value: The entity value
        
    Returns:
        The updated VelocityCounter object
    """
    # Get or create counter
    counter, created = VelocityCounter.objects.get_or_create(
        entity_type=entity_type,
        entity_value=entity_value
    )
    
    # Get current time
    now = timezone.now()
    
    # Calculate time deltas
    time_5m = now - timezone.timedelta(seconds=TIME_WINDOW_5_MIN)
    time_15m = now - timezone.timedelta(seconds=TIME_WINDOW_15_MIN)
    time_1h = now - timezone.timedelta(seconds=TIME_WINDOW_1_HOUR)
    time_6h = now - timezone.timedelta(seconds=TIME_WINDOW_6_HOURS)
    time_24h = now - timezone.timedelta(seconds=TIME_WINDOW_24_HOURS)
    time_7d = now - timezone.timedelta(seconds=TIME_WINDOW_7_DAYS)
    time_30d = now - timezone.timedelta(seconds=TIME_WINDOW_30_DAYS)
    
    # Reset counters if they're expired
    if counter.last_updated < time_5m:
        counter.count_5m = 0
    if counter.last_updated < time_15m:
        counter.count_15m = 0
    if counter.last_updated < time_1h:
        counter.count_1h = 0
    if counter.last_updated < time_6h:
        counter.count_6h = 0
    if counter.last_updated < time_24h:
        counter.count_24h = 0
    if counter.last_updated < time_7d:
        counter.count_7d = 0
    if counter.last_updated < time_30d:
        counter.count_30d = 0
    
    # Increment counters
    counter.count_5m += 1
    counter.count_15m += 1
    counter.count_1h += 1
    counter.count_6h += 1
    counter.count_24h += 1
    counter.count_7d += 1
    counter.count_30d += 1
    
    # Save counter
    counter.save()
    
    return counter


def get_count_for_window(counter: VelocityCounter, time_window: int) -> int:
    """
    Get the count for a specific time window.
    
    Args:
        counter: The VelocityCounter object
        time_window: The time window in seconds
        
    Returns:
        The count for the time window
    """
    if time_window == TIME_WINDOW_5_MIN:
        return counter.count_5m
    elif time_window == TIME_WINDOW_15_MIN:
        return counter.count_15m
    elif time_window == TIME_WINDOW_1_HOUR:
        return counter.count_1h
    elif time_window == TIME_WINDOW_6_HOURS:
        return counter.count_6h
    elif time_window == TIME_WINDOW_24_HOURS:
        return counter.count_24h
    elif time_window == TIME_WINDOW_7_DAYS:
        return counter.count_7d
    elif time_window == TIME_WINDOW_30_DAYS:
        return counter.count_30d
    else:
        return 0