"""
Decision service for the Fraud Engine.

This service is responsible for making the final fraud decision based on
the results from all detection engines.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def make_fraud_decision(transaction, results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make a fraud decision based on the results from all detection engines.
    
    Args:
        transaction: The transaction object
        results: Dictionary containing results from all detection engines
        
    Returns:
        Dictionary with the decision result
    """
    # Extract results from each engine
    block_result = results.get('block_check', {})
    rule_result = results.get('rule_engine', {})
    velocity_result = results.get('velocity_engine', {})
    ml_result = results.get('ml_engine', {})
    aml_result = results.get('aml_engine', {})
    triggered_rules = results.get('triggered_rules', [])
    
    # Initialize decision result
    decision_result = {
        'decision': 'approve',  # Default decision
        'status': 'approved',   # Default transaction status
        'is_flagged': False,    # Default flag status
        'flag_reason': '',      # Default flag reason
        'risk_score': 0.0,      # Default risk score
        'is_fraudulent': False  # Default fraud status
    }
    
    # If blocked, reject immediately
    if block_result.get('is_blocked', False):
        decision_result['decision'] = 'reject'
        decision_result['status'] = 'rejected'
        decision_result['is_flagged'] = True
        decision_result['flag_reason'] = block_result.get('reason', 'Blocked entity')
        decision_result['risk_score'] = 100.0
        decision_result['is_fraudulent'] = True
        return decision_result
    
    # Calculate combined risk score
    # We'll use a weighted average of scores from different engines
    rule_score = rule_result.get('risk_score', 0.0)
    velocity_score = velocity_result.get('risk_score', 0.0)
    ml_score = ml_result.get('risk_score', 0.0)
    aml_score = aml_result.get('risk_score', 0.0)
    
    # Weights for each engine (should sum to 1.0)
    rule_weight = 0.3
    velocity_weight = 0.2
    ml_weight = 0.3
    aml_weight = 0.2
    
    # Calculate weighted average
    combined_score = (
        rule_score * rule_weight +
        velocity_score * velocity_weight +
        ml_score * ml_weight +
        aml_score * aml_weight
    )
    
    # Round to 2 decimal places
    combined_score = round(combined_score, 2)
    decision_result['risk_score'] = combined_score
    
    # Check for automatic reject rules
    auto_reject_rules = [
        rule for rule in triggered_rules
        if rule.get('action') == 'reject'
    ]
    
    if auto_reject_rules:
        decision_result['decision'] = 'reject'
        decision_result['status'] = 'rejected'
        decision_result['is_flagged'] = True
        decision_result['flag_reason'] = f"Automatic rejection: {auto_reject_rules[0].get('name', 'Unknown rule')}"
        decision_result['is_fraudulent'] = True
        return decision_result
    
    # Check for review rules
    review_rules = [
        rule for rule in triggered_rules
        if rule.get('action') == 'review'
    ]
    
    # Make decision based on risk score and triggered rules
    if combined_score >= 80:
        # High risk - reject
        decision_result['decision'] = 'reject'
        decision_result['status'] = 'rejected'
        decision_result['is_flagged'] = True
        decision_result['flag_reason'] = f"High risk score: {combined_score}"
        decision_result['is_fraudulent'] = True
    elif combined_score >= 50 or review_rules:
        # Medium risk or review rules triggered - flag for review
        decision_result['decision'] = 'review'
        decision_result['status'] = 'flagged'
        decision_result['is_flagged'] = True
        
        if review_rules:
            decision_result['flag_reason'] = f"Review required: {review_rules[0].get('name', 'Unknown rule')}"
        else:
            decision_result['flag_reason'] = f"Medium risk score: {combined_score}"
    else:
        # Low risk - approve
        decision_result['decision'] = 'approve'
        decision_result['status'] = 'approved'
        decision_result['is_flagged'] = False
    
    logger.info(
        f"Fraud decision for transaction {transaction.transaction_id}: "
        f"{decision_result['decision']} with risk score {combined_score}"
    )
    
    return decision_result