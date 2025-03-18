"""
Views for response code analytics.

This module provides views for displaying response code analytics and visualizations.
"""

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

from apps.transactions.models import Transaction
from apps.ml_engine.models import MLPrediction
from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES, RESPONSE_CODE_DESCRIPTIONS
from apps.ml_engine.services.visualization_service import (
    generate_response_code_distribution_plot,
    generate_response_code_time_series,
    generate_response_code_heatmap,
    generate_risk_score_by_response_code,
    generate_response_code_sankey
)

logger = logging.getLogger(__name__)


@login_required
def response_code_dashboard(request):
    """
    View for the response code analytics dashboard.
    
    Args:
        request: HTTP request
        
    Returns:
        Rendered response
    """
    # Get time period from query parameters
    period = request.GET.get('period', 'month')
    
    # Determine days based on period
    if period == 'day':
        days = 1
    elif period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    elif period == 'quarter':
        days = 90
    elif period == 'year':
        days = 365
    else:
        days = 30  # Default to month
    
    # Generate visualizations
    distribution_plot = generate_response_code_distribution_plot(days=days)
    time_series_plot = generate_response_code_time_series(days=days, interval='day' if days <= 7 else 'week')
    heatmap_plot = generate_response_code_heatmap(days=days)
    risk_score_plot = generate_risk_score_by_response_code(days=days)
    sankey_plot = generate_response_code_sankey(days=days)
    
    # Get high-risk response code data
    high_risk_codes = get_high_risk_response_code_data(days=days)
    
    # Get response code patterns
    response_patterns = get_response_code_patterns(days=days)
    
    context = {
        'period': period,
        'days': days,
        'distribution_plot': distribution_plot,
        'time_series_plot': time_series_plot,
        'heatmap_plot': heatmap_plot,
        'risk_score_plot': risk_score_plot,
        'sankey_plot': sankey_plot,
        'high_risk_codes': high_risk_codes,
        'response_patterns': response_patterns
    }
    
    return render(request, 'ml_engine/response_code_dashboard.html', context)


def get_high_risk_response_code_data(days=30):
    """
    Get data for high-risk response codes.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of dictionaries with response code data
    """
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions in date range
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get response code counts
    response_code_counts = transactions.values('response_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get transaction IDs
    transaction_ids = transactions.values_list('transaction_id', flat=True)
    
    # Get ML predictions
    predictions = MLPrediction.objects.filter(
        transaction_id__in=transaction_ids
    )
    
    # Create mapping of transaction_id to prediction
    prediction_map = {p.transaction_id: p.prediction for p in predictions}
    
    # Calculate average risk score and fraud rate for each response code
    high_risk_data = []
    
    for item in response_code_counts:
        response_code = item['response_code']
        count = item['count']
        
        # Skip if no response code
        if not response_code:
            continue
        
        # Get transactions with this response code
        code_transactions = transactions.filter(response_code=response_code)
        code_transaction_ids = code_transactions.values_list('transaction_id', flat=True)
        
        # Calculate average risk score
        risk_scores = [prediction_map.get(tx_id, 0) for tx_id in code_transaction_ids if tx_id in prediction_map]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Calculate fraud rate (transactions with risk score > 80)
        fraud_count = sum(1 for score in risk_scores if score > 80)
        fraud_rate = (fraud_count / len(risk_scores) * 100) if risk_scores else 0
        
        # Add to result if high or medium risk
        if response_code in HIGH_RISK_RESPONSE_CODES or response_code in MEDIUM_RISK_RESPONSE_CODES:
            high_risk_data.append({
                'response_code': response_code,
                'description': RESPONSE_CODE_DESCRIPTIONS.get(response_code, 'Unknown'),
                'count': count,
                'avg_risk_score': avg_risk_score,
                'fraud_rate': fraud_rate
            })
    
    # Sort by average risk score
    high_risk_data.sort(key=lambda x: x['avg_risk_score'], reverse=True)
    
    return high_risk_data


def get_response_code_patterns(days=30):
    """
    Get common response code patterns.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of dictionaries with pattern data
    """
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions in date range
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).order_by('user_id', 'timestamp')
    
    # Group transactions by user
    user_transactions = {}
    for tx in transactions:
        if tx.user_id not in user_transactions:
            user_transactions[tx.user_id] = []
        user_transactions[tx.user_id].append(tx)
    
    # Find patterns (sequences of 2-3 response codes)
    patterns = {}
    fraud_patterns = {}
    
    for user_id, txs in user_transactions.items():
        # Skip if less than 2 transactions
        if len(txs) < 2:
            continue
        
        # Get response codes
        codes = [tx.response_code for tx in txs if tx.response_code]
        
        # Generate patterns of length 2
        for i in range(len(codes) - 1):
            pattern = f"{codes[i]} → {codes[i+1]}"
            patterns[pattern] = patterns.get(pattern, 0) + 1
            
            # Check if followed by fraud
            if i + 2 < len(txs):
                # Get ML prediction for the next transaction
                tx_id = txs[i+2].transaction_id
                prediction = MLPrediction.objects.filter(transaction_id=tx_id).first()
                
                if prediction and prediction.prediction > 80:
                    fraud_patterns[pattern] = fraud_patterns.get(pattern, 0) + 1
        
        # Generate patterns of length 3
        for i in range(len(codes) - 2):
            pattern = f"{codes[i]} → {codes[i+1]} → {codes[i+2]}"
            patterns[pattern] = patterns.get(pattern, 0) + 1
            
            # Check if this is a fraud pattern
            tx_id = txs[i+2].transaction_id
            prediction = MLPrediction.objects.filter(transaction_id=tx_id).first()
            
            if prediction and prediction.prediction > 80:
                fraud_patterns[pattern] = fraud_patterns.get(pattern, 0) + 1
    
    # Convert to list of dictionaries
    pattern_data = []
    
    for pattern, count in patterns.items():
        if count >= 2:  # Only include patterns that occur at least twice
            fraud_count = fraud_patterns.get(pattern, 0)
            fraud_rate = (fraud_count / count * 100) if count > 0 else 0
            
            pattern_data.append({
                'pattern': pattern,
                'count': count,
                'fraud_rate': fraud_rate
            })
    
    # Sort by fraud rate
    pattern_data.sort(key=lambda x: x['fraud_rate'], reverse=True)
    
    return pattern_data[:10]  # Return top 10 patterns