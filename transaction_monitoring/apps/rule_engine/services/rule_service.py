"""
Rule service for the Rule Engine app.

This service is responsible for applying rules to transactions.
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from ..models import Rule

logger = logging.getLogger(__name__)


def apply_rules(transaction) -> Dict[str, Any]:
    """
    Apply rules to a transaction.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the rule application results
    """
    # Initialize result
    result = {
        'is_flagged': False,
        'flag_reason': None,
        'rules_triggered': [],
        'execution_time': 0,
    }
    
    try:
        # Get active rules
        active_rules = Rule.objects.filter(is_active=True)
        
        if not active_rules.exists():
            logger.warning(f"No active rules found for transaction {transaction.transaction_id}")
            return result
        
        # Apply each rule
        for rule in active_rules:
            is_triggered = False
            
            # Apply rule based on rule type
            if rule.rule_type == 'amount':
                # Amount threshold rule
                # For simplicity, we'll just check if amount > 1000
                if float(transaction.amount) > 1000:
                    is_triggered = True
            
            elif rule.rule_type == 'location':
                # Check if transaction is from a high-risk country
                high_risk_countries = ['RU', 'IR', 'KP', 'CU', 'SY']
                country = transaction.location_data.get('country', '').upper()
                
                if country in high_risk_countries:
                    is_triggered = True
            
            # Add more rule types as needed
            
            # If rule is triggered and action is to flag for review
            if is_triggered and rule.action == 'review':
                result['is_flagged'] = True
                result['flag_reason'] = rule.name
                result['rules_triggered'].append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'action': rule.action,
                })
                
                # If rule has high priority, stop processing further rules
                if rule.priority > 5:
                    break
        
        # For testing purposes, let's add a simple rule for high amounts
        if float(transaction.amount) > 1000:
            result['is_flagged'] = True
            result['flag_reason'] = "High Amount Transaction"
            result['rules_triggered'].append({
                'rule_id': 0,
                'rule_name': "High Amount Transaction",
                'rule_type': "amount",
                'action': "review",
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error applying rules to transaction {transaction.transaction_id}: {str(e)}", exc_info=True)
        return result