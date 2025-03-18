"""
Response service for the Fraud Engine.

This service is responsible for constructing the response to the client
after fraud detection is complete.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def construct_response(transaction, decision_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct a response to the client based on the fraud decision.
    
    Args:
        transaction: The transaction object
        decision_result: The decision result from the fraud engine
        
    Returns:
        Dictionary with the response data
    """
    # Basic response structure
    response = {
        'transaction_id': transaction.transaction_id,
        'status': decision_result.get('status', 'pending'),
        'risk_score': decision_result.get('risk_score', 0.0),
    }
    
    # Add additional information based on decision
    decision = decision_result.get('decision', 'approve')
    
    if decision == 'approve':
        response['message'] = 'Transaction approved'
        response['approval_code'] = generate_approval_code(transaction)
    elif decision == 'reject':
        response['message'] = 'Transaction rejected'
        response['reason_code'] = 'FRAUD_SUSPECTED'
    elif decision == 'review':
        response['message'] = 'Transaction flagged for review'
        response['reason_code'] = 'MANUAL_REVIEW_REQUIRED'
    
    logger.info(f"Response for transaction {transaction.transaction_id}: {response['status']}")
    
    return response


def generate_approval_code(transaction) -> str:
    """
    Generate an approval code for an approved transaction.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Approval code string
    """
    import random
    import string
    
    # Generate a random 6-character alphanumeric code
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(6))
    
    return code