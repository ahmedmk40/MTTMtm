"""
Rule evaluation service for the Rule Engine.

This service is responsible for evaluating rules against transactions.
"""

import time
import logging
from typing import Dict, Any, List
from django.utils import timezone
from ..models import Rule, RuleExecution

logger = logging.getLogger(__name__)


def evaluate_rules(transaction) -> Dict[str, Any]:
    """
    Evaluate all applicable rules against a transaction.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the rule evaluation result
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
    
    # Get active rules applicable to this transaction channel
    channel = transaction.channel
    rules = Rule.objects.filter(is_active=True)
    
    if channel == 'pos':
        rules = rules.filter(applies_to_pos=True)
    elif channel == 'ecommerce':
        rules = rules.filter(applies_to_ecommerce=True)
    elif channel == 'wallet':
        rules = rules.filter(applies_to_wallet=True)
    
    # Filter by merchant-specific rules if applicable
    merchant_id = getattr(transaction, 'merchant_id', None)
    if merchant_id:
        # For SQLite compatibility, we need to filter in Python instead of using JSON field lookups
        # Get all rules first
        all_rules = list(rules)
        filtered_rules = []
        
        for rule in all_rules:
            # Skip rules where this merchant is explicitly excluded
            if merchant_id in rule.excluded_merchants:
                continue
            
            # Include rules that:
            # 1. Are not merchant-specific (apply to all merchants), OR
            # 2. Are merchant-specific AND include this merchant, OR
            # 3. Are merchant-specific with an empty included_merchants list (applies to all)
            if (not rule.merchant_specific or  # Not merchant-specific
                (rule.merchant_specific and not rule.included_merchants) or  # Merchant-specific but applies to all
                (rule.merchant_specific and merchant_id in rule.included_merchants)):  # Merchant-specific and includes this merchant
                filtered_rules.append(rule)
        
        # Replace the queryset with our filtered list
        rules = filtered_rules
    
    # Order by priority (higher priority first)
    if isinstance(rules, list):
        # If we've filtered in Python, sort the list
        rules = sorted(rules, key=lambda r: (-r.priority, r.name))
    else:
        # Otherwise, use the queryset's order_by method
        rules = rules.order_by('-priority')
    
    # Track the highest risk score from triggered rules
    max_risk_score = 0.0
    
    # Evaluate each rule
    for rule in rules:
        rule_start_time = time.time()
        
        # Convert transaction to a dictionary for rule evaluation
        transaction_dict = transaction_to_dict(transaction)
        
        # Evaluate the rule condition
        try:
            triggered, condition_values = evaluate_condition(rule.condition, transaction_dict)
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {str(e)}", exc_info=True)
            triggered = False
            condition_values = {'error': str(e)}
        
        # Calculate execution time in milliseconds
        execution_time = (time.time() - rule_start_time) * 1000
        
        # Record rule execution
        RuleExecution.objects.create(
            transaction_id=transaction.transaction_id,
            rule=rule,
            triggered=triggered,
            execution_time=execution_time,
            condition_values=condition_values
        )
        
        # Update rule metrics
        if triggered:
            rule.hit_count += 1
            rule.last_triggered = timezone.now()
            rule.save(update_fields=['hit_count', 'last_triggered'])
            
            # Add to triggered rules
            result['triggered_rules'].append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'rule_type': rule.rule_type,
                'action': rule.action,
                'risk_score': float(rule.risk_score),
                'condition_values': condition_values
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
        f"Rule evaluation for transaction {transaction.transaction_id}: "
        f"{result['rules_triggered']} of {result['rules_evaluated']} rules triggered "
        f"in {result['execution_time']:.2f}ms"
    )
    
    return result


def evaluate_condition(condition: str, transaction_dict: Dict[str, Any]) -> tuple:
    """
    Evaluate a rule condition against a transaction.
    
    Args:
        condition: The rule condition as a Python expression
        transaction_dict: The transaction data as a dictionary
        
    Returns:
        Tuple of (triggered, condition_values)
    """
    # Create a safe namespace for evaluation
    namespace = {
        'transaction': transaction_dict,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'round': round,
    }
    
    # Track values used in the condition
    condition_values = {}
    
    # Evaluate the condition
    try:
        result = eval(condition, {"__builtins__": {}}, namespace)
        
        # Extract key values used in the condition
        # This is a simplified approach - in a real system, you'd want to
        # parse the condition and extract the exact values used
        if 'amount' in condition:
            condition_values['amount'] = transaction_dict.get('amount')
        if 'currency' in condition:
            condition_values['currency'] = transaction_dict.get('currency')
        if 'user_id' in condition:
            condition_values['user_id'] = transaction_dict.get('user_id')
        if 'merchant_id' in condition:
            condition_values['merchant_id'] = transaction_dict.get('merchant_id')
        if 'location_data' in condition:
            condition_values['location_data'] = transaction_dict.get('location_data')
        if 'payment_method_data' in condition:
            condition_values['payment_method_data'] = transaction_dict.get('payment_method_data')
        
        return bool(result), condition_values
    except Exception as e:
        logger.error(f"Error evaluating condition: {condition} - {str(e)}", exc_info=True)
        return False, {'error': str(e)}


def transaction_to_dict(transaction) -> Dict[str, Any]:
    """
    Convert a transaction object to a dictionary for rule evaluation.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary representation of the transaction
    """
    # Start with basic fields
    result = {
        'transaction_id': transaction.transaction_id,
        'transaction_type': transaction.transaction_type,
        'channel': transaction.channel,
        'amount': float(transaction.amount),
        'currency': transaction.currency,
        'user_id': transaction.user_id,
        'timestamp': transaction.timestamp,
        'status': transaction.status,
    }
    
    # Add optional fields if they exist
    if hasattr(transaction, 'merchant_id') and transaction.merchant_id:
        result['merchant_id'] = transaction.merchant_id
    
    if hasattr(transaction, 'device_id') and transaction.device_id:
        result['device_id'] = transaction.device_id
    
    if hasattr(transaction, 'location_data') and transaction.location_data:
        result['location_data'] = transaction.location_data
    
    if hasattr(transaction, 'payment_method_data') and transaction.payment_method_data:
        result['payment_method_data'] = transaction.payment_method_data
    
    if hasattr(transaction, 'metadata') and transaction.metadata:
        result['metadata'] = transaction.metadata
    
    # Add channel-specific fields
    if transaction.channel == 'pos' and hasattr(transaction, 'terminal_id'):
        result['terminal_id'] = transaction.terminal_id
        result['entry_mode'] = getattr(transaction, 'entry_mode', None)
        result['terminal_type'] = getattr(transaction, 'terminal_type', None)
        result['attendance'] = getattr(transaction, 'attendance', None)
        result['condition'] = getattr(transaction, 'condition', None)
        result['mcc'] = getattr(transaction, 'mcc', None)
        result['authorization_code'] = getattr(transaction, 'authorization_code', None)
        result['recurring_payment'] = getattr(transaction, 'recurring_payment', False)
    
    elif transaction.channel == 'ecommerce':
        result['website_url'] = getattr(transaction, 'website_url', None)
        result['is_3ds_verified'] = getattr(transaction, 'is_3ds_verified', False)
        result['device_fingerprint'] = getattr(transaction, 'device_fingerprint', None)
        result['shipping_address'] = getattr(transaction, 'shipping_address', {})
        result['billing_address'] = getattr(transaction, 'billing_address', {})
        result['is_billing_shipping_match'] = getattr(transaction, 'is_billing_shipping_match', True)
        result['mcc'] = getattr(transaction, 'mcc', None)
        result['authorization_code'] = getattr(transaction, 'authorization_code', None)
        result['recurring_payment'] = getattr(transaction, 'recurring_payment', False)
    
    elif transaction.channel == 'wallet':
        result['wallet_id'] = getattr(transaction, 'wallet_id', None)
        result['source_type'] = getattr(transaction, 'source_type', None)
        result['destination_type'] = getattr(transaction, 'destination_type', None)
        result['source_id'] = getattr(transaction, 'source_id', None)
        result['destination_id'] = getattr(transaction, 'destination_id', None)
        result['transaction_purpose'] = getattr(transaction, 'transaction_purpose', None)
        result['is_internal'] = getattr(transaction, 'is_internal', False)
    
    return result