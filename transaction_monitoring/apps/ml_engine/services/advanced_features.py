"""
Advanced feature engineering for ML models.

This module provides functions for extracting advanced features from transactions,
with a focus on response code patterns and sequences.
"""

import logging
from datetime import timedelta
from collections import Counter
from typing import Dict, Any, List, Tuple

from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q

from apps.transactions.models import Transaction
from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES

logger = logging.getLogger(__name__)


def extract_response_code_sequence(user_id: str, lookback_days: int = 30) -> List[str]:
    """
    Extract the sequence of response codes for a user in the last N days.
    
    Args:
        user_id: The user ID
        lookback_days: Number of days to look back
        
    Returns:
        List of response codes in chronological order
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    transactions = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).order_by('timestamp')
    
    return [tx.response_code for tx in transactions if tx.response_code]


def calculate_response_code_velocity(user_id: str, response_code: str = None, 
                                    lookback_hours: int = 24) -> Dict[str, int]:
    """
    Calculate the velocity of response codes for a user.
    
    Args:
        user_id: The user ID
        response_code: Specific response code to calculate velocity for (optional)
        lookback_hours: Number of hours to look back
        
    Returns:
        Dictionary with response code velocities
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(hours=lookback_hours)
    
    # Base query
    query = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # If specific response code is provided
    if response_code:
        query = query.filter(response_code=response_code)
        count = query.count()
        return {response_code: count}
    
    # Get counts for all response codes
    response_code_counts = query.values('response_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Convert to dictionary
    velocity = {item['response_code']: item['count'] for item in response_code_counts if item['response_code']}
    
    return velocity


def calculate_response_code_ratios(user_id: str, lookback_days: int = 30) -> Dict[str, float]:
    """
    Calculate ratios of different response codes for a user.
    
    Args:
        user_id: The user ID
        lookback_days: Number of days to look back
        
    Returns:
        Dictionary with response code ratios
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    transactions = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    total_count = transactions.count()
    if total_count == 0:
        return {}
    
    # Get counts for all response codes
    response_code_counts = transactions.values('response_code').annotate(
        count=Count('id')
    )
    
    # Calculate ratios
    ratios = {}
    for item in response_code_counts:
        if item['response_code']:
            ratios[item['response_code']] = item['count'] / total_count
    
    # Calculate special ratios
    approved_count = transactions.filter(response_code='00').count()
    declined_count = total_count - approved_count
    
    if total_count > 0:
        ratios['approved_ratio'] = approved_count / total_count
        ratios['declined_ratio'] = declined_count / total_count
    
    if approved_count > 0:
        ratios['declined_to_approved_ratio'] = declined_count / approved_count
    
    return ratios


def extract_cross_channel_patterns(user_id: str, lookback_days: int = 30) -> Dict[str, Any]:
    """
    Extract patterns of response codes across different channels for a user.
    
    Args:
        user_id: The user ID
        lookback_days: Number of days to look back
        
    Returns:
        Dictionary with cross-channel patterns
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    transactions = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get response code distributions by channel
    channels = transactions.values_list('channel', flat=True).distinct()
    
    patterns = {}
    for channel in channels:
        if not channel:
            continue
            
        channel_txs = transactions.filter(channel=channel)
        response_codes = channel_txs.values('response_code').annotate(count=Count('id'))
        
        patterns[channel] = {
            rc['response_code']: rc['count'] for rc in response_codes if rc['response_code']
        }
    
    # Calculate channel switching with same response code
    channel_switches = []
    prev_tx = None
    
    for tx in transactions.order_by('timestamp'):
        if prev_tx and tx.channel != prev_tx.channel and tx.response_code == prev_tx.response_code:
            channel_switches.append((prev_tx.channel, tx.channel, tx.response_code))
        prev_tx = tx
    
    patterns['channel_switches'] = channel_switches
    patterns['channel_switch_count'] = len(channel_switches)
    
    return patterns


def calculate_risk_score_from_response_codes(user_id: str, lookback_days: int = 30) -> float:
    """
    Calculate a risk score based on response code patterns.
    
    Args:
        user_id: The user ID
        lookback_days: Number of days to look back
        
    Returns:
        Risk score between 0 and 100
    """
    # Get response code sequence
    response_codes = extract_response_code_sequence(user_id, lookback_days)
    
    if not response_codes:
        return 0.0
    
    # Count response codes
    code_counts = Counter(response_codes)
    total_count = len(response_codes)
    
    # Calculate base risk score
    risk_score = 0.0
    
    # High risk response codes
    high_risk_count = sum(code_counts.get(code, 0) for code in HIGH_RISK_RESPONSE_CODES)
    risk_score += (high_risk_count / total_count) * 70 if total_count > 0 else 0
    
    # Medium risk response codes
    medium_risk_count = sum(code_counts.get(code, 0) for code in MEDIUM_RISK_RESPONSE_CODES)
    risk_score += (medium_risk_count / total_count) * 30 if total_count > 0 else 0
    
    # Consecutive declines
    consecutive_declines = 0
    max_consecutive_declines = 0
    
    for code in response_codes:
        if code != '00':  # Not approved
            consecutive_declines += 1
            max_consecutive_declines = max(max_consecutive_declines, consecutive_declines)
        else:
            consecutive_declines = 0
    
    # Add penalty for consecutive declines
    if max_consecutive_declines >= 3:
        risk_score += min(30, max_consecutive_declines * 5)
    
    # Calculate decline ratio
    approved_count = code_counts.get('00', 0)
    declined_count = total_count - approved_count
    
    if total_count > 0:
        decline_ratio = declined_count / total_count
        risk_score += decline_ratio * 20
    
    # Cap at 100
    return min(100, risk_score)


def extract_advanced_features(transaction) -> Dict[str, Any]:
    """
    Extract advanced features for a transaction, including response code patterns.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary of advanced features
    """
    features = {}
    
    # Skip if no user ID
    if not hasattr(transaction, 'user_id') or not transaction.user_id:
        return features
    
    user_id = transaction.user_id
    
    try:
        # Response code sequence features
        response_codes = extract_response_code_sequence(user_id, lookback_days=30)
        
        if response_codes:
            # Last 5 response codes
            last_5_codes = response_codes[-5:] if len(response_codes) >= 5 else response_codes
            for i, code in enumerate(reversed(last_5_codes)):
                features[f'prev_response_code_{i+1}'] = code
            
            # Response code counts
            code_counts = Counter(response_codes)
            for code, count in code_counts.items():
                features[f'response_code_{code}_count'] = count
            
            # High risk response code count
            features['high_risk_response_code_count'] = sum(
                code_counts.get(code, 0) for code in HIGH_RISK_RESPONSE_CODES
            )
            
            # Medium risk response code count
            features['medium_risk_response_code_count'] = sum(
                code_counts.get(code, 0) for code in MEDIUM_RISK_RESPONSE_CODES
            )
            
            # Approved vs declined counts
            features['approved_count'] = code_counts.get('00', 0)
            features['declined_count'] = sum(code_counts.values()) - features['approved_count']
            
            if features['approved_count'] > 0:
                features['declined_to_approved_ratio'] = features['declined_count'] / features['approved_count']
            else:
                features['declined_to_approved_ratio'] = features['declined_count'] if features['declined_count'] > 0 else 0
        
        # Response code velocity features
        velocity_24h = calculate_response_code_velocity(user_id, lookback_hours=24)
        for code, count in velocity_24h.items():
            features[f'response_code_{code}_velocity_24h'] = count
        
        # Current response code velocity
        if hasattr(transaction, 'response_code') and transaction.response_code:
            current_code = transaction.response_code
            features[f'current_response_code_velocity_24h'] = velocity_24h.get(current_code, 0)
        
        # Cross-channel patterns
        cross_channel = extract_cross_channel_patterns(user_id, lookback_days=30)
        features['channel_switch_count'] = cross_channel.get('channel_switch_count', 0)
        
        # Risk score from response codes
        features['response_code_risk_score'] = calculate_risk_score_from_response_codes(user_id, lookback_days=30)
        
    except Exception as e:
        logger.error(f"Error extracting advanced features for user {user_id}: {str(e)}", exc_info=True)
    
    return features