"""
Views for the Analytics app.
"""

import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField, FloatField, Max
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
import random

from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from apps.ml_engine.models import MLPrediction


@login_required
def transaction_analytics_dashboard(request):
    """
    Dashboard for transaction analytics.
    """
    # Get time period from request
    period = request.GET.get('period', 'week')
    if period == 'day':
        days = 1
        trunc_function = TruncDay
        date_format = '%H:%M'
    elif period == 'week':
        days = 7
        trunc_function = TruncDay
        date_format = '%a %d'
    elif period == 'month':
        days = 30
        trunc_function = TruncDay
        date_format = '%d'
    elif period == 'quarter':
        days = 90
        trunc_function = TruncWeek
        date_format = 'Week %W'
    else:  # year
        days = 365
        trunc_function = TruncMonth
        date_format = '%b'
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all transactions in the period
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Transaction volume by type
    transaction_types = list(transactions.values('transaction_type').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('-count'))
    
    # Transaction volume by channel
    transaction_channels = list(transactions.values('channel').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('-count'))
    
    # Transaction volume by category
    transaction_categories = list(transactions.values('transaction_category').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('-count'))
    
    # Response code distribution
    response_codes = list(transactions.values('response_code').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Approval rate
    approved_count = transactions.filter(
        Q(response_code='00') | Q(status='approved')
    ).count()
    
    total_count = transactions.count()
    approval_rate = (approved_count / total_count * 100) if total_count > 0 else 0
    
    # Transaction volume over time
    volume_over_time = list(transactions.annotate(
        date=trunc_function('timestamp')
    ).values('date').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('date'))
    
    # Risk distribution - manually calculate to avoid type conversion issues
    low_risk = transactions.filter(risk_score__lt=30).count()
    medium_risk = transactions.filter(risk_score__gte=30, risk_score__lt=70).count()
    high_risk = transactions.filter(risk_score__gte=70).count()
    unknown_risk = transactions.filter(risk_score__isnull=True).count()
    
    risk_distribution = [
        {'risk_category': 'low', 'count': low_risk},
        {'risk_category': 'medium', 'count': medium_risk},
        {'risk_category': 'high', 'count': high_risk},
        {'risk_category': 'unknown', 'count': unknown_risk}
    ]
    
    # Cross-border transactions
    cross_border = transactions.filter(is_cross_border=True).count()
    cross_border_percentage = (cross_border / total_count * 100) if total_count > 0 else 0
    
    # High risk transactions
    high_risk_merchant = transactions.filter(is_high_risk_merchant=True).count()
    high_risk_country = transactions.filter(is_high_risk_country=True).count()
    
    # Wallet-specific metrics
    wallet_transactions = transactions.filter(
        transaction_type__in=[
            'deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
            'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
            'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund'
        ]
    )
    
    wallet_volume_by_type = list(wallet_transactions.values('transaction_type').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('-volume'))
    
    # E-commerce specific metrics
    ecommerce_transactions = transactions.filter(channel='ecommerce')
    
    authentication_types = list(ecommerce_transactions.values('ecommercetransaction__authentication_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    checkout_types = list(ecommerce_transactions.values('ecommercetransaction__checkout_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # POS specific metrics
    pos_transactions = transactions.filter(channel='pos')
    
    entry_modes = list(pos_transactions.values('postransaction__entry_mode').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    terminal_types = list(pos_transactions.values('postransaction__terminal_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': total_count,
        'total_volume': transactions.aggregate(Sum('amount'))['amount__sum'] or 0,
        'approval_rate': approval_rate,
        'transaction_types': transaction_types,
        'transaction_channels': transaction_channels,
        'transaction_categories': transaction_categories,
        'response_codes': response_codes,
        'volume_over_time': volume_over_time,
        'risk_distribution': risk_distribution,
        'cross_border': cross_border,
        'cross_border_percentage': cross_border_percentage,
        'high_risk_merchant': high_risk_merchant,
        'high_risk_country': high_risk_country,
        'wallet_volume_by_type': wallet_volume_by_type,
        'authentication_types': authentication_types,
        'checkout_types': checkout_types,
        'entry_modes': entry_modes,
        'terminal_types': terminal_types,
    }
    
    return render(request, 'analytics/dashboard.html', context)


def detect_unusual_patterns(transactions, days):
    """
    Detect unusual patterns in response codes.
    
    Args:
        transactions: QuerySet of transactions
        days: Number of days to analyze
        
    Returns:
        List of alerts about unusual patterns
    """
    alerts = []
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Calculate comparison period
    comparison_end = start_date
    comparison_start = comparison_end - timedelta(days=days)
    
    # Get current period data
    current_period = transactions.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get comparison period data
    comparison_period = Transaction.objects.filter(
        timestamp__gte=comparison_start,
        timestamp__lte=comparison_end
    )
    
    # Calculate current period metrics
    current_total = current_period.count()
    if current_total == 0:
        return alerts  # No data to analyze
    
    current_declined = current_period.filter(
        Q(status='rejected') | 
        Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'])
    ).count()
    
    current_decline_rate = (current_declined / current_total) * 100 if current_total > 0 else 0
    
    # Calculate comparison period metrics
    comparison_total = comparison_period.count()
    if comparison_total == 0:
        # No comparison data, check if current decline rate is high
        if current_decline_rate > 30:
            alerts.append({
                'type': 'warning',
                'message': f'High decline rate of {current_decline_rate:.1f}% detected in the current period.',
                'details': f'{current_declined} out of {current_total} transactions were declined.'
            })
        return alerts
    
    comparison_declined = comparison_period.filter(
        Q(status='rejected') | 
        Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'])
    ).count()
    
    comparison_decline_rate = (comparison_declined / comparison_total) * 100 if comparison_total > 0 else 0
    
    # Check for significant increase in decline rate
    if current_decline_rate > comparison_decline_rate * 1.5 and current_decline_rate > 20:
        alerts.append({
            'type': 'danger',
            'message': f'Significant increase in decline rate detected: {current_decline_rate:.1f}% vs {comparison_decline_rate:.1f}% in previous period.',
            'details': f'Current period: {current_declined}/{current_total} declined. Previous period: {comparison_declined}/{comparison_total} declined.'
        })
    elif current_decline_rate > comparison_decline_rate * 1.2 and current_decline_rate > 15:
        alerts.append({
            'type': 'warning',
            'message': f'Moderate increase in decline rate detected: {current_decline_rate:.1f}% vs {comparison_decline_rate:.1f}% in previous period.',
            'details': f'Current period: {current_declined}/{current_total} declined. Previous period: {comparison_declined}/{comparison_total} declined.'
        })
    
    # Check for specific response code spikes
    current_response_codes = current_period.values('response_code').annotate(count=Count('id'))
    comparison_response_codes = comparison_period.values('response_code').annotate(count=Count('id'))
    
    # Convert to dictionaries for easier comparison
    current_codes_dict = {item['response_code']: item['count'] for item in current_response_codes}
    comparison_codes_dict = {item['response_code']: item['count'] for item in comparison_response_codes}
    
    # Check for spikes in specific response codes
    for code, count in current_codes_dict.items():
        if code in ['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']:
            current_rate = (count / current_total) * 100
            comparison_count = comparison_codes_dict.get(code, 0)
            comparison_rate = (comparison_count / comparison_total) * 100 if comparison_total > 0 else 0
            
            # Check for significant increase
            if current_rate > comparison_rate * 2 and current_rate > 10:
                code_description = RESPONSE_CODE_DESCRIPTIONS.get(code, 'Unknown')
                alerts.append({
                    'type': 'danger',
                    'message': f'Spike detected in response code {code} ({code_description}): {current_rate:.1f}% vs {comparison_rate:.1f}% in previous period.',
                    'details': f'Current period: {count}/{current_total}. Previous period: {comparison_count}/{comparison_total}.'
                })
    
    # Check for unusual patterns in merchant decline rates
    merchant_declines = current_period.values('merchant_id').annotate(
        total=Count('id'),
        declined=Count(Case(
            When(
                Q(status='rejected') | 
                Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']),
                then=F('id')
            ),
            default=None,
            output_field=IntegerField()
        ))
    ).filter(total__gte=5)  # Only consider merchants with at least 5 transactions
    
    for merchant in merchant_declines:
        merchant_decline_rate = (merchant['declined'] / merchant['total']) * 100 if merchant['total'] > 0 else 0
        if merchant_decline_rate > 50:  # High decline rate threshold
            alerts.append({
                'type': 'warning',
                'message': f'High decline rate of {merchant_decline_rate:.1f}% for merchant {merchant["merchant_id"]}.',
                'details': f'{merchant["declined"]} out of {merchant["total"]} transactions were declined.'
            })
    
    return alerts


def response_code_analytics(request):
    """
    Analytics dashboard for response codes.
    """
    # Get time period from request
    period = request.GET.get('period', 'week')
    if period == 'day':
        days = 1
    elif period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    elif period == 'quarter':
        days = 90
    else:  # year
        days = 365
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all transactions in the period
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Acquiring response codes
    acquiring_transactions = transactions.filter(
        transaction_type__in=[
            'purchase', 'authorization', 'increment_auth', 'pre_authorization',
            'capture', 'refund', 'void', 'reversal', 'chargeback'
        ]
    )
    
    # Calculate acquiring response codes
    acquiring_count = acquiring_transactions.count()
    if acquiring_count > 0:
        acquiring_response_codes = []
        for code_group in acquiring_transactions.values('response_code').annotate(count=Count('id')):
            code_group['percentage'] = (code_group['count'] / acquiring_count) * 100
            acquiring_response_codes.append(code_group)
        acquiring_response_codes = sorted(acquiring_response_codes, key=lambda x: x['count'], reverse=True)
    else:
        acquiring_response_codes = []
    
    # Add response message to each code
    for code in acquiring_response_codes:
        if code['response_code'] in Transaction.ACQUIRING_RESPONSE_CODES:
            code['message'] = Transaction.ACQUIRING_RESPONSE_CODES[code['response_code']]
        else:
            code['message'] = 'Unknown'
    
    # Wallet response codes
    wallet_transactions = transactions.filter(
        transaction_type__in=[
            'deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
            'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
            'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund'
        ]
    )
    
    # Calculate wallet response codes
    wallet_count = wallet_transactions.count()
    if wallet_count > 0:
        wallet_response_codes = []
        for code_group in wallet_transactions.values('response_code').annotate(count=Count('id')):
            code_group['percentage'] = (code_group['count'] / wallet_count) * 100
            wallet_response_codes.append(code_group)
        wallet_response_codes = sorted(wallet_response_codes, key=lambda x: x['count'], reverse=True)
    else:
        wallet_response_codes = []
    
    # Add response message to each code
    for code in wallet_response_codes:
        if code['response_code'] in Transaction.WALLET_RESPONSE_CODES:
            code['message'] = Transaction.WALLET_RESPONSE_CODES[code['response_code']]
        else:
            code['message'] = 'Unknown'
    
    # Response code trends over time
    response_code_trends = list(transactions.annotate(
        date=TruncDay('timestamp')
    ).values('date', 'response_code').annotate(
        count=Count('id')
    ).order_by('date', 'response_code'))
    
    # Top decline reasons
    decline_codes = ['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']
    # Calculate decline reasons
    decline_transactions = transactions.filter(response_code__in=decline_codes)
    decline_count = decline_transactions.count()
    if decline_count > 0:
        decline_reasons = []
        for code_group in decline_transactions.values('response_code').annotate(count=Count('id')):
            code_group['percentage'] = (code_group['count'] / decline_count) * 100
            decline_reasons.append(code_group)
        decline_reasons = sorted(decline_reasons, key=lambda x: x['count'], reverse=True)
    else:
        decline_reasons = []
    
    # Add response message to each code
    for code in decline_reasons:
        if code['response_code'] in Transaction.ACQUIRING_RESPONSE_CODES:
            code['message'] = Transaction.ACQUIRING_RESPONSE_CODES[code['response_code']]
        elif code['response_code'] in Transaction.WALLET_RESPONSE_CODES:
            code['message'] = Transaction.WALLET_RESPONSE_CODES[code['response_code']]
        else:
            code['message'] = 'Unknown'
    
    # Generate alerts for unusual patterns
    alerts = detect_unusual_patterns(transactions, days)
    
    # Calculate overall decline rate
    total_count = transactions.count()
    declined_count = transactions.filter(
        Q(status='rejected') | 
        Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'])
    ).count()
    
    decline_rate = (declined_count / total_count) * 100 if total_count > 0 else 0
    
    # Get top merchants with high decline rates
    top_merchants_with_declines = transactions.values('merchant_id').annotate(
        total=Count('id'),
        declined=Count(Case(
            When(
                Q(status='rejected') | 
                Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']),
                then=F('id')
            ),
            default=None,
            output_field=IntegerField()
        ))
    ).filter(total__gte=5).order_by('-declined')[:5]
    
    # Calculate decline rate for each merchant
    for merchant in top_merchants_with_declines:
        merchant['decline_rate'] = (merchant['declined'] / merchant['total']) * 100 if merchant['total'] > 0 else 0
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': total_count,
        'acquiring_response_codes': acquiring_response_codes,
        'wallet_response_codes': wallet_response_codes,
        'response_code_trends': response_code_trends,
        'decline_reasons': decline_reasons,
        'alerts': alerts,
        'decline_rate': decline_rate,
        'declined_count': declined_count,
        'top_merchants_with_declines': top_merchants_with_declines
    }
    
    return render(request, 'analytics/response_codes.html', context)


@login_required
def transaction_type_analytics(request):
    """
    Analytics dashboard for transaction types.
    """
    # Get time period from request
    period = request.GET.get('period', 'week')
    if period == 'day':
        days = 1
    elif period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    elif period == 'quarter':
        days = 90
    else:  # year
        days = 365
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all transactions in the period
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Transaction types
    transaction_types_data = []
    for tx_type in transactions.values('transaction_type').distinct():
        type_transactions = transactions.filter(transaction_type=tx_type['transaction_type'])
        count = type_transactions.count()
        
        if count > 0:
            approved = type_transactions.filter(Q(response_code='00') | Q(status='approved')).count()
            approval_rate = (approved / count) * 100 if count > 0 else 0
            
            transaction_types_data.append({
                'transaction_type': tx_type['transaction_type'],
                'count': count,
                'volume': type_transactions.aggregate(Sum('amount'))['amount__sum'] or 0,
                'average': type_transactions.aggregate(Avg('amount'))['amount__avg'] or 0,
                'approval_rate': approval_rate
            })
    
    transaction_types = sorted(transaction_types_data, key=lambda x: x['count'], reverse=True)
    
    # Add display name to each type
    for tx_type in transaction_types:
        for choice in Transaction.TRANSACTION_TYPE_CHOICES:
            if choice[0] == tx_type['transaction_type']:
                tx_type['display_name'] = choice[1]
                break
        else:
            tx_type['display_name'] = tx_type['transaction_type']
    
    # Transaction type trends over time
    type_trends = list(transactions.annotate(
        date=TruncDay('timestamp')
    ).values('date', 'transaction_type').annotate(
        count=Count('id'),
        volume=Sum('amount')
    ).order_by('date', 'transaction_type'))
    
    # Acquiring transaction types
    acquiring_types = [
        'purchase', 'authorization', 'increment_auth', 'pre_authorization',
        'capture', 'refund', 'void', 'reversal', 'chargeback'
    ]
    
    acquiring_transactions = transactions.filter(transaction_type__in=acquiring_types)
    
    acquiring_type_stats = list(acquiring_transactions.values('transaction_type').annotate(
        count=Count('id'),
        volume=Sum('amount'),
        average=Avg('amount')
    ).order_by('-count'))
    
    # Add display name to each type
    for tx_type in acquiring_type_stats:
        for choice in Transaction.TRANSACTION_TYPE_CHOICES:
            if choice[0] == tx_type['transaction_type']:
                tx_type['display_name'] = choice[1]
                break
        else:
            tx_type['display_name'] = tx_type['transaction_type']
    
    # Wallet transaction types
    wallet_types = [
        'deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
        'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
        'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund'
    ]
    
    wallet_transactions = transactions.filter(transaction_type__in=wallet_types)
    
    wallet_type_stats = list(wallet_transactions.values('transaction_type').annotate(
        count=Count('id'),
        volume=Sum('amount'),
        average=Avg('amount')
    ).order_by('-count'))
    
    # Add display name to each type
    for tx_type in wallet_type_stats:
        for choice in Transaction.TRANSACTION_TYPE_CHOICES:
            if choice[0] == tx_type['transaction_type']:
                tx_type['display_name'] = choice[1]
                break
        else:
            tx_type['display_name'] = tx_type['transaction_type']
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': transactions.count(),
        'transaction_types': transaction_types,
        'type_trends': type_trends,
        'acquiring_type_stats': acquiring_type_stats,
        'wallet_type_stats': wallet_type_stats,
    }
    
    return render(request, 'analytics/transaction_types.html', context)


@login_required
def merchant_analysis(request):
    """
    Analytics dashboard for merchant analysis.
    """
    # Get merchant ID and date range from request
    merchant_id = request.GET.get('merchant_id', '')
    date_range = int(request.GET.get('date_range', '30'))
    
    # Initialize context
    context = {
        'merchant_id': merchant_id,
        'date_range': date_range,
    }
    
    if merchant_id:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Get all transactions for this merchant in the period
        transactions = Transaction.objects.filter(
            merchant_id=merchant_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_transactions = transactions.count()
        
        if total_transactions > 0:
            # Basic metrics
            total_volume = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            avg_transaction = total_volume / total_transactions if total_transactions > 0 else 0
            
            # Get risk score
            transactions_with_risk = transactions.filter(risk_score__isnull=False)
            risk_score = transactions_with_risk.aggregate(Avg('risk_score'))['risk_score__avg'] or 0
            
            # Calculate risk metrics
            declined_count = transactions.filter(
                Q(status='rejected') | 
                Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'])
            ).count()
            
            decline_rate = (declined_count / total_transactions) * 100 if total_transactions > 0 else 0
            
            # Simulate chargeback and fraud rates (in a real system, these would come from actual data)
            chargeback_rate = random.uniform(0.1, 1.5)
            fraud_rate = random.uniform(0.05, 0.8)
            
            # Calculate high risk transaction rate
            high_risk_count = transactions.filter(risk_score__gte=70).count()
            high_risk_rate = (high_risk_count / total_transactions) * 100 if total_transactions > 0 else 0
            
            # Get recent transactions
            recent_transactions = transactions.order_by('-timestamp')[:20]
            
            # Transaction volume over time
            volume_by_day = transactions.annotate(
                date=TruncDay('timestamp')
            ).values('date').annotate(
                volume=Sum('amount')
            ).order_by('date')
            
            volume_dates = [entry['date'].strftime('%Y-%m-%d') for entry in volume_by_day]
            volume_data = [float(entry['volume']) for entry in volume_by_day]
            
            # Transaction count over time
            count_by_day = transactions.annotate(
                date=TruncDay('timestamp')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            count_dates = [entry['date'].strftime('%Y-%m-%d') for entry in count_by_day]
            count_data = [entry['count'] for entry in count_by_day]
            
            # Channel distribution
            channels = transactions.values('channel').annotate(
                count=Count('id')
            ).order_by('-count')
            
            channel_labels = [entry['channel'] for entry in channels]
            channel_data = [entry['count'] for entry in channels]
            
            # Response code distribution
            response_codes = transactions.filter(
                response_code__isnull=False
            ).values('response_code').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            response_code_labels = [entry['response_code'] for entry in response_codes]
            response_code_data = [entry['count'] for entry in response_codes]
            
            # Risk score over time
            risk_by_day = transactions.filter(
                risk_score__isnull=False
            ).annotate(
                date=TruncDay('timestamp')
            ).values('date').annotate(
                avg_risk=Avg('risk_score')
            ).order_by('date')
            
            risk_dates = [entry['date'].strftime('%Y-%m-%d') for entry in risk_by_day]
            risk_data = [float(entry['avg_risk']) for entry in risk_by_day]
            
            # Add all data to context
            context.update({
                'total_transactions': total_transactions,
                'total_volume': total_volume,
                'avg_transaction': avg_transaction,
                'risk_score': risk_score,
                'decline_rate': decline_rate,
                'chargeback_rate': chargeback_rate,
                'fraud_rate': fraud_rate,
                'high_risk_rate': high_risk_rate,
                'recent_transactions': recent_transactions,
                'volume_dates': json.dumps(volume_dates),
                'volume_data': json.dumps(volume_data),
                'count_dates': json.dumps(count_dates),
                'count_data': json.dumps(count_data),
                'channel_labels': json.dumps(channel_labels),
                'channel_data': json.dumps(channel_data),
                'response_code_labels': json.dumps(response_code_labels),
                'response_code_data': json.dumps(response_code_data),
                'risk_dates': json.dumps(risk_dates),
                'risk_data': json.dumps(risk_data),
            })
        else:
            # No transactions found
            context.update({
                'total_transactions': 0,
                'total_volume': 0,
                'avg_transaction': 0,
                'risk_score': 0,
                'decline_rate': 0,
                'chargeback_rate': 0,
                'fraud_rate': 0,
                'high_risk_rate': 0,
                'recent_transactions': [],
                'volume_dates': json.dumps([]),
                'volume_data': json.dumps([]),
                'count_dates': json.dumps([]),
                'count_data': json.dumps([]),
                'channel_labels': json.dumps([]),
                'channel_data': json.dumps([]),
                'response_code_labels': json.dumps([]),
                'response_code_data': json.dumps([]),
                'risk_dates': json.dumps([]),
                'risk_data': json.dumps([]),
            })
    
    return render(request, 'analytics/merchant_analysis.html', context)


@login_required
def user_analysis(request):
    """
    Analytics dashboard for user analysis.
    """
    # Get user ID and date range from request
    user_id = request.GET.get('user_id', '')
    date_range = int(request.GET.get('date_range', '30'))
    
    # Initialize context
    context = {
        'user_id': user_id,
        'date_range': date_range,
    }
    
    if user_id:
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Get all transactions for this user in the period
        transactions = Transaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_transactions = transactions.count()
        
        if total_transactions > 0:
            # Basic metrics
            total_volume = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            avg_transaction = total_volume / total_transactions if total_transactions > 0 else 0
            
            # Get risk score
            transactions_with_risk = transactions.filter(risk_score__isnull=False)
            risk_score = transactions_with_risk.aggregate(Avg('risk_score'))['risk_score__avg'] or 0
            
            # Calculate risk metrics
            declined_count = transactions.filter(
                Q(status='rejected') | 
                Q(response_code__in=['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96'])
            ).count()
            
            decline_rate = (declined_count / total_transactions) * 100 if total_transactions > 0 else 0
            
            # Calculate transaction frequency (transactions per day)
            days_active = min(date_range, (end_date - transactions.earliest('timestamp').timestamp).days + 1)
            transaction_frequency = total_transactions / days_active if days_active > 0 else 0
            
            # Calculate velocity (transactions per hour in peak periods)
            # For simplicity, we'll use a random value between 0.5 and 3.0
            velocity = random.uniform(0.5, 3.0)
            
            # Calculate cross-border rate
            cross_border_count = transactions.filter(is_cross_border=True).count()
            cross_border_rate = (cross_border_count / total_transactions) * 100 if total_transactions > 0 else 0
            
            # Get recent transactions
            recent_transactions = transactions.order_by('-timestamp')[:20]
            
            # Transaction volume over time
            volume_by_day = transactions.annotate(
                date=TruncDay('timestamp')
            ).values('date').annotate(
                volume=Sum('amount')
            ).order_by('date')
            
            volume_dates = [entry['date'].strftime('%Y-%m-%d') for entry in volume_by_day]
            volume_data = [float(entry['volume']) for entry in volume_by_day]
            
            # Transaction count over time
            count_by_day = transactions.annotate(
                date=TruncDay('timestamp')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            count_dates = [entry['date'].strftime('%Y-%m-%d') for entry in count_by_day]
            count_data = [entry['count'] for entry in count_by_day]
            
            # Channel distribution
            channels = transactions.values('channel').annotate(
                count=Count('id')
            ).order_by('-count')
            
            channel_labels = [entry['channel'] for entry in channels]
            channel_data = [entry['count'] for entry in channels]
            
            # Merchant distribution
            merchants = transactions.values('merchant_id').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            merchant_labels = [entry['merchant_id'] for entry in merchants]
            merchant_data = [entry['count'] for entry in merchants]
            
            # Device analysis
            devices_data = transactions.values('device_id').annotate(
                count=Count('id'),
                last_used=Max('timestamp'),
                risk_score=Avg('risk_score')
            ).order_by('-count')
            
            devices = []
            device_labels = []
            device_data = []
            
            for device in devices_data:
                if device['device_id']:  # Skip None values
                    devices.append(device)
                    device_labels.append(device['device_id'])
                    device_data.append(device['count'])
            
            # Behavior data for radar chart
            # Normalize values for radar chart (0-100 scale)
            behavior_data = [
                min(transaction_frequency * 50, 100),  # Transaction frequency (0.5 = 25, 1.0 = 50, 2.0 = 100)
                min(avg_transaction / 2, 100),         # Average amount ($200 = 100)
                min(decline_rate * 2, 100),            # Decline rate (50% = 100)
                min(velocity * 33.3, 100),             # Velocity (3.0 = 100)
                min(cross_border_rate * 2, 100)        # Cross-border (50% = 100)
            ]
            
            # Add all data to context
            context.update({
                'total_transactions': total_transactions,
                'total_volume': total_volume,
                'avg_transaction': avg_transaction,
                'risk_score': risk_score,
                'decline_rate': decline_rate,
                'transaction_frequency': transaction_frequency,
                'velocity': velocity,
                'cross_border_rate': cross_border_rate,
                'recent_transactions': recent_transactions,
                'volume_dates': json.dumps(volume_dates),
                'volume_data': json.dumps(volume_data),
                'count_dates': json.dumps(count_dates),
                'count_data': json.dumps(count_data),
                'channel_labels': json.dumps(channel_labels),
                'channel_data': json.dumps(channel_data),
                'merchant_labels': json.dumps(merchant_labels),
                'merchant_data': json.dumps(merchant_data),
                'devices': devices,
                'device_labels': json.dumps(device_labels),
                'device_data': json.dumps(device_data),
                'behavior_data': json.dumps(behavior_data),
            })
        else:
            # No transactions found
            context.update({
                'total_transactions': 0,
                'total_volume': 0,
                'avg_transaction': 0,
                'risk_score': 0,
                'decline_rate': 0,
                'transaction_frequency': 0,
                'velocity': 0,
                'cross_border_rate': 0,
                'recent_transactions': [],
                'volume_dates': json.dumps([]),
                'volume_data': json.dumps([]),
                'count_dates': json.dumps([]),
                'count_data': json.dumps([]),
                'channel_labels': json.dumps([]),
                'channel_data': json.dumps([]),
                'merchant_labels': json.dumps([]),
                'merchant_data': json.dumps([]),
                'devices': [],
                'device_labels': json.dumps([]),
                'device_data': json.dumps([]),
                'behavior_data': json.dumps([0, 0, 0, 0, 0]),
            })
    
    return render(request, 'analytics/user_analysis.html', context)


@login_required
def risk_rankings(request):
    """
    View for risk rankings of merchants and users.
    """
    # Get filter parameters
    date_range = int(request.GET.get('date_range', '30'))
    min_transactions = int(request.GET.get('min_transactions', '5'))
    risk_threshold = int(request.GET.get('risk_threshold', '50'))
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=date_range)
    
    # Get all transactions in the period
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Fetch all transactions and process in Python
    all_transactions = list(transactions.values(
        'id', 'merchant_id', 'user_id', 'amount', 'risk_score', 
        'status', 'response_code', 'is_cross_border'
    ))
    
    # Process merchant data
    merchant_dict = {}
    for tx in all_transactions:
        merchant_id = tx['merchant_id']
        if merchant_id not in merchant_dict:
            merchant_dict[merchant_id] = {
                'merchant_id': merchant_id,
                'transaction_count': 0,
                'volume': 0,
                'risk_score_sum': 0,
                'risk_score_count': 0,
                'declined_count': 0,
                'high_risk_count': 0,
                'cross_border_count': 0
            }
        
        # Update merchant stats
        merchant_dict[merchant_id]['transaction_count'] += 1
        merchant_dict[merchant_id]['volume'] += float(tx['amount'])
        
        if tx['risk_score'] is not None:
            merchant_dict[merchant_id]['risk_score_sum'] += tx['risk_score']
            merchant_dict[merchant_id]['risk_score_count'] += 1
        
        # Check if declined
        if tx['status'] == 'rejected' or tx['response_code'] in ['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']:
            merchant_dict[merchant_id]['declined_count'] += 1
        
        # Check if high risk
        if tx['risk_score'] is not None and tx['risk_score'] >= 70:
            merchant_dict[merchant_id]['high_risk_count'] += 1
        
        # Check if cross border
        if tx['is_cross_border']:
            merchant_dict[merchant_id]['cross_border_count'] += 1
    
    # Convert to list and filter by min_transactions
    merchant_data = []
    for merchant_id, data in merchant_dict.items():
        if data['transaction_count'] >= min_transactions:
            # Calculate average risk score
            if data['risk_score_count'] > 0:
                data['risk_score'] = data['risk_score_sum'] / data['risk_score_count']
            else:
                data['risk_score'] = None
            
            # Calculate rates
            data['avg_amount'] = data['volume'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
            data['decline_rate'] = (data['declined_count'] / data['transaction_count']) * 100 if data['transaction_count'] > 0 else 0
            data['high_risk_rate'] = (data['high_risk_count'] / data['transaction_count']) * 100 if data['transaction_count'] > 0 else 0
            data['cross_border_rate'] = (data['cross_border_count'] / data['transaction_count']) * 100 if data['transaction_count'] > 0 else 0
            
            # Simulate chargeback rate (in a real system, this would come from actual data)
            data['chargeback_rate'] = random.uniform(0.1, 2.0)
            # Simulate velocity (in a real system, this would be calculated from transaction timestamps)
            data['velocity'] = random.uniform(0.5, 3.0)
            
            # Remove temporary fields
            del data['risk_score_sum']
            del data['risk_score_count']
            
            merchant_data.append(data)
    
    # Sort merchants by risk score (descending)
    merchant_data = sorted(merchant_data, key=lambda x: x['risk_score'] if x['risk_score'] is not None else 0, reverse=True)
    
    # Get top merchants (for display in table)
    top_merchants = merchant_data[:10]
    
    # Process user data
    user_dict = {}
    for tx in all_transactions:
        user_id = tx['user_id']
        if user_id not in user_dict:
            user_dict[user_id] = {
                'user_id': user_id,
                'transaction_count': 0,
                'volume': 0,
                'risk_score_sum': 0,
                'risk_score_count': 0,
                'declined_count': 0,
                'cross_border_count': 0
            }
        
        # Update user stats
        user_dict[user_id]['transaction_count'] += 1
        user_dict[user_id]['volume'] += float(tx['amount'])
        
        if tx['risk_score'] is not None:
            user_dict[user_id]['risk_score_sum'] += tx['risk_score']
            user_dict[user_id]['risk_score_count'] += 1
        
        # Check if declined
        if tx['status'] == 'rejected' or tx['response_code'] in ['01', '05', '12', '14', '30', '41', '43', '51', '54', '55', '57', '58', '61', '91', '96']:
            user_dict[user_id]['declined_count'] += 1
        
        # Check if cross border
        if tx['is_cross_border']:
            user_dict[user_id]['cross_border_count'] += 1
    
    # Convert to list and filter by min_transactions
    user_data = []
    for user_id, data in user_dict.items():
        if data['transaction_count'] >= min_transactions:
            # Calculate average risk score
            if data['risk_score_count'] > 0:
                data['risk_score'] = data['risk_score_sum'] / data['risk_score_count']
            else:
                data['risk_score'] = None
            
            # Calculate rates
            data['avg_amount'] = data['volume'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
            data['decline_rate'] = (data['declined_count'] / data['transaction_count']) * 100 if data['transaction_count'] > 0 else 0
            data['cross_border_rate'] = (data['cross_border_count'] / data['transaction_count']) * 100 if data['transaction_count'] > 0 else 0
            
            # Calculate transaction frequency (transactions per day)
            days_active = min(date_range, 30)  # Assume at least active for a month
            data['transaction_frequency'] = data['transaction_count'] / days_active if days_active > 0 else 0
            
            # Simulate velocity (in a real system, this would be calculated from transaction timestamps)
            data['velocity'] = random.uniform(0.5, 3.0)
            
            # Remove temporary fields
            del data['risk_score_sum']
            del data['risk_score_count']
            
            user_data.append(data)
    
    # Sort users by risk score (descending)
    user_data = sorted(user_data, key=lambda x: x['risk_score'] if x['risk_score'] is not None else 0, reverse=True)
    
    # Get top users (for display in table)
    top_users = user_data[:10]
    
    # Prepare data for charts
    merchant_labels = [m['merchant_id'] for m in top_merchants]
    merchant_risk_scores = [float(m['risk_score']) if m['risk_score'] is not None else 0 for m in top_merchants]
    
    user_labels = [u['user_id'] for u in top_users]
    user_risk_scores = [float(u['risk_score']) if u['risk_score'] is not None else 0 for u in top_users]
    
    # Risk distribution for merchants
    merchant_high_risk = len([m for m in merchant_data if m['risk_score'] is not None and m['risk_score'] > 70])
    merchant_medium_risk = len([m for m in merchant_data if m['risk_score'] is not None and 50 <= m['risk_score'] <= 70])
    merchant_low_risk = len([m for m in merchant_data if m['risk_score'] is not None and m['risk_score'] < 50])
    merchant_risk_distribution = [merchant_high_risk, merchant_medium_risk, merchant_low_risk]
    
    # Risk distribution for users
    user_high_risk = len([u for u in user_data if u['risk_score'] is not None and u['risk_score'] > 70])
    user_medium_risk = len([u for u in user_data if u['risk_score'] is not None and 50 <= u['risk_score'] <= 70])
    user_low_risk = len([u for u in user_data if u['risk_score'] is not None and u['risk_score'] < 50])
    user_risk_distribution = [user_high_risk, user_medium_risk, user_low_risk]
    
    # Risk factors for high-risk vs low-risk merchants
    high_risk_merchants = [m for m in merchant_data if m['risk_score'] is not None and m['risk_score'] > risk_threshold]
    low_risk_merchants = [m for m in merchant_data if m['risk_score'] is not None and m['risk_score'] <= risk_threshold]
    
    merchant_high_risk_factors = [0, 0, 0, 0, 0]
    merchant_low_risk_factors = [0, 0, 0, 0, 0]
    
    if high_risk_merchants:
        merchant_high_risk_factors = [
            sum(m['decline_rate'] for m in high_risk_merchants) / len(high_risk_merchants),
            sum(m['high_risk_rate'] for m in high_risk_merchants) / len(high_risk_merchants),
            sum(m['cross_border_rate'] for m in high_risk_merchants) / len(high_risk_merchants),
            sum(m['chargeback_rate'] for m in high_risk_merchants) / len(high_risk_merchants) * 50,  # Scale to 0-100
            sum(m['velocity'] for m in high_risk_merchants) / len(high_risk_merchants) * 33.3  # Scale to 0-100
        ]
    
    if low_risk_merchants:
        merchant_low_risk_factors = [
            sum(m['decline_rate'] for m in low_risk_merchants) / len(low_risk_merchants),
            sum(m['high_risk_rate'] for m in low_risk_merchants) / len(low_risk_merchants),
            sum(m['cross_border_rate'] for m in low_risk_merchants) / len(low_risk_merchants),
            sum(m['chargeback_rate'] for m in low_risk_merchants) / len(low_risk_merchants) * 50,  # Scale to 0-100
            sum(m['velocity'] for m in low_risk_merchants) / len(low_risk_merchants) * 33.3  # Scale to 0-100
        ]
    
    # Risk factors for high-risk vs low-risk users
    high_risk_users = [u for u in user_data if u['risk_score'] is not None and u['risk_score'] > risk_threshold]
    low_risk_users = [u for u in user_data if u['risk_score'] is not None and u['risk_score'] <= risk_threshold]
    
    user_high_risk_factors = [0, 0, 0, 0, 0]
    user_low_risk_factors = [0, 0, 0, 0, 0]
    
    if high_risk_users:
        user_high_risk_factors = [
            sum(u['transaction_frequency'] for u in high_risk_users) / len(high_risk_users) * 50,  # Scale to 0-100
            sum(u['avg_amount'] for u in high_risk_users) / len(high_risk_users) / 2,  # Scale to 0-100 ($200 = 100)
            sum(u['decline_rate'] for u in high_risk_users) / len(high_risk_users),
            sum(u['velocity'] for u in high_risk_users) / len(high_risk_users) * 33.3,  # Scale to 0-100
            sum(u['cross_border_rate'] for u in high_risk_users) / len(high_risk_users)
        ]
    
    if low_risk_users:
        user_low_risk_factors = [
            sum(u['transaction_frequency'] for u in low_risk_users) / len(low_risk_users) * 50,  # Scale to 0-100
            sum(u['avg_amount'] for u in low_risk_users) / len(low_risk_users) / 2,  # Scale to 0-100 ($200 = 100)
            sum(u['decline_rate'] for u in low_risk_users) / len(low_risk_users),
            sum(u['velocity'] for u in low_risk_users) / len(low_risk_users) * 33.3,  # Scale to 0-100
            sum(u['cross_border_rate'] for u in low_risk_users) / len(low_risk_users)
        ]
    
    # Risk trends over time (simulated data)
    trend_dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(date_range, 0, -5)]
    merchant_risk_trend = [random.uniform(50, 70) for _ in trend_dates]
    user_risk_trend = [random.uniform(45, 65) for _ in trend_dates]
    
    context = {
        'date_range': date_range,
        'min_transactions': min_transactions,
        'risk_threshold': risk_threshold,
        'merchant_count': len(merchant_data),
        'user_count': len(user_data),
        'top_merchants': top_merchants,
        'top_users': top_users,
        'merchant_labels': json.dumps(merchant_labels),
        'merchant_risk_scores': json.dumps(merchant_risk_scores),
        'user_labels': json.dumps(user_labels),
        'user_risk_scores': json.dumps(user_risk_scores),
        'merchant_risk_distribution': json.dumps(merchant_risk_distribution),
        'user_risk_distribution': json.dumps(user_risk_distribution),
        'merchant_high_risk_factors': json.dumps(merchant_high_risk_factors),
        'merchant_low_risk_factors': json.dumps(merchant_low_risk_factors),
        'user_high_risk_factors': json.dumps(user_high_risk_factors),
        'user_low_risk_factors': json.dumps(user_low_risk_factors),
        'trend_dates': json.dumps(trend_dates),
        'merchant_risk_trend': json.dumps(merchant_risk_trend),
        'user_risk_trend': json.dumps(user_risk_trend),
    }
    
    return render(request, 'analytics/risk_rankings.html', context)
