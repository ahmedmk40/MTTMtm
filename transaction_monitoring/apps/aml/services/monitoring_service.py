"""
Monitoring service for the AML app.

This service is responsible for monitoring transactions for AML risks.
"""

import time
import logging
import uuid
from typing import Dict, Any
from django.utils import timezone
from django.db.models import Sum, Count, F
from ..models import AMLRiskProfile, AMLAlert, TransactionPattern
from apps.core.constants import SUSPICIOUS_MCCS, HIGH_RISK_COUNTRIES
from .pattern_detection_service import (
    detect_round_amount_patterns,
    detect_round_transfers_patterns,
    detect_identical_amount_patterns,
    detect_multiple_transactions_between_accounts,
    check_aml_patterns
)

logger = logging.getLogger(__name__)


def check_aml_risk(transaction) -> Dict[str, Any]:
    """
    Check a transaction for AML risks.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the AML risk check result
    """
    start_time = time.time()
    
    # Initialize result
    result = {
        'risk_score': 0.0,
        'is_suspicious': False,
        'triggered_rules': [],
        'patterns_detected': [],
        'execution_time': 0.0,
    }
    
    # Get or create risk profile for the user
    risk_profile, _ = AMLRiskProfile.objects.get_or_create(
        user_id=transaction.user_id,
        defaults={
            'risk_level': 'low',
            'risk_score': 0.0,
        }
    )
    
    # Check for structuring (transactions just below reporting thresholds)
    if check_structuring(transaction):
        pattern = record_pattern(
            transaction.user_id,
            'structuring',
            {
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'timestamp': transaction.timestamp.isoformat(),
            },
            risk_score=80.0
        )
        
        result['patterns_detected'].append({
            'type': 'structuring',
            'description': 'Transaction amount just below reporting threshold',
            'risk_score': 80.0,
        })
        
        result['triggered_rules'].append({
            'id': 'aml_structuring',
            'name': 'Structuring Detection',
            'description': 'Transaction amount just below reporting threshold',
            'rule_type': 'aml',
            'action': 'review',
            'risk_score': 80.0,
        })
        
        result['risk_score'] = max(result['risk_score'], 80.0)
        result['is_suspicious'] = True
    
    # Check for round amounts
    if check_round_amount(transaction):
        pattern = record_pattern(
            transaction.user_id,
            'round_amount',
            {
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'timestamp': transaction.timestamp.isoformat(),
            },
            risk_score=60.0
        )
        
        result['patterns_detected'].append({
            'type': 'round_amount',
            'description': 'Transaction with suspiciously round amount',
            'risk_score': 60.0,
        })
        
        result['triggered_rules'].append({
            'id': 'aml_round_amount',
            'name': 'Round Amount Detection',
            'description': 'Transaction with suspiciously round amount',
            'rule_type': 'aml',
            'action': 'review',
            'risk_score': 60.0,
        })
        
        result['risk_score'] = max(result['risk_score'], 60.0)
        result['is_suspicious'] = True
    
    # Check for high-risk jurisdictions
    if check_high_risk_jurisdiction(transaction):
        pattern = record_pattern(
            transaction.user_id,
            'cross_border',
            {
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'timestamp': transaction.timestamp.isoformat(),
                'country': transaction.location_data.get('country', 'unknown'),
            },
            risk_score=70.0
        )
        
        result['patterns_detected'].append({
            'type': 'cross_border',
            'description': 'Transaction involving high-risk jurisdiction',
            'risk_score': 70.0,
        })
        
        result['triggered_rules'].append({
            'id': 'aml_high_risk_jurisdiction',
            'name': 'High-Risk Jurisdiction',
            'description': 'Transaction involving high-risk jurisdiction',
            'rule_type': 'aml',
            'action': 'review',
            'risk_score': 70.0,
        })
        
        result['risk_score'] = max(result['risk_score'], 70.0)
        result['is_suspicious'] = True
    
    # Check for rapid movement of funds
    if check_rapid_movement(transaction):
        pattern = record_pattern(
            transaction.user_id,
            'rapid_movement',
            {
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'timestamp': transaction.timestamp.isoformat(),
                'source_type': getattr(transaction, 'source_type', 'unknown'),
                'destination_type': getattr(transaction, 'destination_type', 'unknown'),
            },
            risk_score=75.0
        )
        
        result['patterns_detected'].append({
            'type': 'rapid_movement',
            'description': 'Rapid movement of funds',
            'risk_score': 75.0,
        })
        
        result['triggered_rules'].append({
            'id': 'aml_rapid_movement',
            'name': 'Rapid Fund Movement',
            'description': 'Rapid movement of funds through accounts',
            'rule_type': 'aml',
            'action': 'review',
            'risk_score': 75.0,
        })
        
        result['risk_score'] = max(result['risk_score'], 75.0)
        result['is_suspicious'] = True
    
    # Check for advanced AML patterns
    aml_patterns_result = check_aml_patterns(transaction)
    
    # Add detected patterns to the result
    for pattern in aml_patterns_result.get('patterns_detected', []):
        result['patterns_detected'].append(pattern)
        
        # Add corresponding triggered rule
        result['triggered_rules'].append({
            'id': f"aml_{pattern['pattern_type']}",
            'name': pattern['pattern_type'].replace('_', ' ').title(),
            'description': pattern['description'],
            'rule_type': 'aml',
            'action': 'review',
            'risk_score': pattern['risk_score'],
        })
        
        # Update overall risk score
        result['risk_score'] = max(result['risk_score'], pattern['risk_score'])
        result['is_suspicious'] = True
    
    # Create AML alert if suspicious
    if result['is_suspicious']:
        create_aml_alert(transaction, result)
        
        # Update risk profile
        update_risk_profile(risk_profile, transaction, result)
    
    # Calculate execution time
    result['execution_time'] = (time.time() - start_time) * 1000
    
    logger.info(
        f"AML check for transaction {transaction.transaction_id}: "
        f"risk_score={result['risk_score']:.2f}, "
        f"is_suspicious={result['is_suspicious']}, "
        f"patterns_detected={len(result['patterns_detected'])}, "
        f"execution_time={result['execution_time']:.2f}ms"
    )
    
    return result


def check_structuring(transaction) -> bool:
    """
    Check for structuring (transactions just below reporting thresholds).
    
    Args:
        transaction: The transaction object
        
    Returns:
        True if structuring is detected, False otherwise
    """
    amount = float(transaction.amount)
    
    # Common reporting thresholds
    thresholds = [10000, 5000, 3000]
    
    for threshold in thresholds:
        # Check if amount is just below threshold (within 10%)
        if amount >= threshold * 0.9 and amount < threshold:
            return True
    
    return False


def check_round_amount(transaction) -> bool:
    """
    Check for suspiciously round amounts.
    
    Args:
        transaction: The transaction object
        
    Returns:
        True if round amount is detected, False otherwise
    """
    amount = float(transaction.amount)
    
    # Check if amount is a round number
    if amount >= 1000 and (amount % 1000 == 0 or amount % 500 == 0):
        return True
    
    return False


def check_high_risk_jurisdiction(transaction) -> bool:
    """
    Check for transactions involving high-risk jurisdictions.
    
    Args:
        transaction: The transaction object
        
    Returns:
        True if high-risk jurisdiction is detected, False otherwise
    """
    # Check if transaction involves a high-risk country
    if hasattr(transaction, 'location_data') and transaction.location_data:
        country = transaction.location_data.get('country')
        if country and country in HIGH_RISK_COUNTRIES:
            return True
    
    return False


def check_rapid_movement(transaction) -> bool:
    """
    Check for rapid movement of funds.
    
    Args:
        transaction: The transaction object
        
    Returns:
        True if rapid movement is detected, False otherwise
    """
    # Check if transaction is a transfer or withdrawal
    if transaction.channel == 'wallet' and hasattr(transaction, 'transaction_purpose'):
        if transaction.transaction_purpose in ['transfer', 'withdrawal'] and float(transaction.amount) > 5000:
            return True
    
    return False


def record_pattern(user_id: str, pattern_type: str, pattern_data: Dict[str, Any], risk_score: float) -> TransactionPattern:
    """
    Record a transaction pattern.
    
    Args:
        user_id: The user ID
        pattern_type: The type of pattern
        pattern_data: The pattern data
        risk_score: The risk score
        
    Returns:
        The created or updated TransactionPattern instance
    """
    # Try to find an existing pattern
    try:
        pattern = TransactionPattern.objects.get(
            user_id=user_id,
            pattern_type=pattern_type
        )
        
        # Update existing pattern
        pattern.last_detected = timezone.now()
        pattern.occurrence_count += 1
        
        # Update risk score (take the higher value)
        pattern.risk_score = max(pattern.risk_score, risk_score)
        
        # Mark as suspicious if occurrence count is high enough
        if pattern.occurrence_count >= 3:
            pattern.is_suspicious = True
        
        # Add new pattern data
        if 'transactions' not in pattern.pattern_data:
            pattern.pattern_data['transactions'] = []
        
        pattern.pattern_data['transactions'].append(pattern_data)
        
        # Keep only the last 10 transactions
        if len(pattern.pattern_data['transactions']) > 10:
            pattern.pattern_data['transactions'] = pattern.pattern_data['transactions'][-10:]
        
        pattern.save()
    
    except TransactionPattern.DoesNotExist:
        # Create new pattern
        pattern = TransactionPattern.objects.create(
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_data={
                'transactions': [pattern_data]
            },
            risk_score=risk_score,
            is_suspicious=False  # Not suspicious on first occurrence
        )
    
    return pattern


def create_aml_alert(transaction, result: Dict[str, Any]) -> AMLAlert:
    """
    Create an AML alert.
    
    Args:
        transaction: The transaction object
        result: The AML check result
        
    Returns:
        The created AMLAlert instance
    """
    # Generate alert ID
    alert_id = f"AML-{uuid.uuid4().hex[:8].upper()}"
    
    # Determine alert type based on patterns
    alert_type = 'other'
    if result['patterns_detected']:
        alert_type = result['patterns_detected'][0]['type']
    
    # Create description
    description = f"Suspicious transaction detected: {transaction.transaction_id}\n\n"
    
    for pattern in result['patterns_detected']:
        description += f"- {pattern['description']}\n"
    
    description += f"\nRisk Score: {result['risk_score']:.2f}"
    
    # Create alert
    alert = AMLAlert.objects.create(
        alert_id=alert_id,
        user_id=transaction.user_id,
        alert_type=alert_type,
        description=description,
        status='open',
        risk_score=result['risk_score'],
        related_transactions=[transaction.transaction_id],
        detection_data={
            'patterns_detected': result['patterns_detected'],
            'triggered_rules': result['triggered_rules'],
        }
    )
    
    logger.info(f"Created AML alert {alert_id} for transaction {transaction.transaction_id}")
    
    return alert


def update_risk_profile(risk_profile: AMLRiskProfile, transaction, result: Dict[str, Any]) -> AMLRiskProfile:
    """
    Update a user's AML risk profile.
    
    Args:
        risk_profile: The AMLRiskProfile instance
        transaction: The transaction object
        result: The AML check result
        
    Returns:
        The updated AMLRiskProfile instance
    """
    # Update transaction stats
    risk_profile.transaction_count += 1
    risk_profile.transaction_volume += float(transaction.amount)
    
    # Update high-risk transaction count if suspicious
    if result['is_suspicious']:
        risk_profile.high_risk_transactions += 1
    
    # Update suspicious patterns count
    if result['patterns_detected']:
        risk_profile.suspicious_patterns += len(result['patterns_detected'])
    
    # Update risk factors
    if not risk_profile.risk_factors:
        risk_profile.risk_factors = []
    
    for pattern in result['patterns_detected']:
        if pattern['type'] not in risk_profile.risk_factors:
            risk_profile.risk_factors.append(pattern['type'])
    
    # Calculate new risk score
    # This is a simplified approach - in a real system, you'd use a more sophisticated algorithm
    base_score = 0.0
    
    # Add score based on high-risk transactions ratio
    if risk_profile.transaction_count > 0:
        high_risk_ratio = risk_profile.high_risk_transactions / risk_profile.transaction_count
        base_score += high_risk_ratio * 50.0
    
    # Add score based on suspicious patterns
    base_score += min(risk_profile.suspicious_patterns * 5.0, 50.0)
    
    # Add score based on transaction volume
    if risk_profile.transaction_volume > 100000:
        base_score += 20.0
    elif risk_profile.transaction_volume > 50000:
        base_score += 10.0
    elif risk_profile.transaction_volume > 10000:
        base_score += 5.0
    
    # Cap at 100
    risk_profile.risk_score = min(base_score, 100.0)
    
    # Update risk level based on score
    if risk_profile.risk_score >= 80.0:
        risk_profile.risk_level = 'critical'
    elif risk_profile.risk_score >= 60.0:
        risk_profile.risk_level = 'high'
    elif risk_profile.risk_score >= 30.0:
        risk_profile.risk_level = 'medium'
    else:
        risk_profile.risk_level = 'low'
    
    # Save changes
    risk_profile.save()
    
    logger.info(
        f"Updated AML risk profile for user {risk_profile.user_id}: "
        f"risk_score={risk_profile.risk_score:.2f}, "
        f"risk_level={risk_profile.risk_level}"
    )
    
    return risk_profile