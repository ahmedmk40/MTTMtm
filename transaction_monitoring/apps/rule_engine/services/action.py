"""
Rule action service for the Rule Engine.

This service is responsible for executing actions based on triggered rules.
"""

import logging
from typing import Dict, Any, List
from django.utils import timezone

logger = logging.getLogger(__name__)


def execute_rule_actions(transaction, triggered_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute actions for triggered rules.
    
    Args:
        transaction: The transaction object
        triggered_rules: List of triggered rules with their details
        
    Returns:
        Dictionary with the action execution result
    """
    result = {
        'actions_executed': [],
        'notifications_sent': [],
    }
    
    # Process each triggered rule
    for rule in triggered_rules:
        action = rule.get('action')
        
        if action == 'approve':
            # Approve the transaction
            result['actions_executed'].append({
                'rule_id': rule.get('id'),
                'rule_name': rule.get('name'),
                'action': 'approve',
                'status': 'success',
            })
        
        elif action == 'reject':
            # Reject the transaction
            result['actions_executed'].append({
                'rule_id': rule.get('id'),
                'rule_name': rule.get('name'),
                'action': 'reject',
                'status': 'success',
            })
        
        elif action == 'review':
            # Flag for review
            result['actions_executed'].append({
                'rule_id': rule.get('id'),
                'rule_name': rule.get('name'),
                'action': 'review',
                'status': 'success',
            })
            
            # Send notification to fraud analysts
            notification = send_review_notification(transaction, rule)
            if notification:
                result['notifications_sent'].append(notification)
        
        elif action == 'notify':
            # Send notification only
            notification = send_notification(transaction, rule)
            if notification:
                result['notifications_sent'].append(notification)
            
            result['actions_executed'].append({
                'rule_id': rule.get('id'),
                'rule_name': rule.get('name'),
                'action': 'notify',
                'status': 'success',
            })
    
    logger.info(
        f"Executed {len(result['actions_executed'])} actions and sent "
        f"{len(result['notifications_sent'])} notifications for transaction {transaction.transaction_id}"
    )
    
    return result


def send_review_notification(transaction, rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a notification for a transaction that needs review.
    
    Args:
        transaction: The transaction object
        rule: The triggered rule details
        
    Returns:
        Dictionary with the notification details or None if sending failed
    """
    try:
        # In a real system, this would send a notification to a queue or service
        # For now, we'll just log it
        logger.info(
            f"NOTIFICATION: Transaction {transaction.transaction_id} flagged for review "
            f"by rule '{rule.get('name')}'"
        )
        
        # Return notification details
        return {
            'type': 'review',
            'transaction_id': transaction.transaction_id,
            'rule_id': rule.get('id'),
            'rule_name': rule.get('name'),
            'timestamp': timezone.now().isoformat(),
            'status': 'sent',
        }
    except Exception as e:
        logger.error(f"Error sending review notification: {str(e)}", exc_info=True)
        return None


def send_notification(transaction, rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a general notification about a triggered rule.
    
    Args:
        transaction: The transaction object
        rule: The triggered rule details
        
    Returns:
        Dictionary with the notification details or None if sending failed
    """
    try:
        # In a real system, this would send a notification to a queue or service
        # For now, we'll just log it
        logger.info(
            f"NOTIFICATION: Rule '{rule.get('name')}' triggered for transaction {transaction.transaction_id}"
        )
        
        # Return notification details
        return {
            'type': 'info',
            'transaction_id': transaction.transaction_id,
            'rule_id': rule.get('id'),
            'rule_name': rule.get('name'),
            'timestamp': timezone.now().isoformat(),
            'status': 'sent',
        }
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)
        return None