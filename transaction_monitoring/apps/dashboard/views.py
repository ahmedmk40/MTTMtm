"""
Views for the dashboard app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from apps.transactions.models import Transaction
from apps.fraud_engine.models import FraudDetectionResult, FraudCase
from apps.aml.models import AMLAlert
from apps.cases.models import Case


@login_required
def dashboard(request):
    """
    Main dashboard view that redirects to the appropriate role-specific dashboard.
    """
    user = request.user
    
    if not hasattr(user, 'role') or not user.role:
        # Default to analyst dashboard if no role is set
        return redirect('dashboard:analyst')
    
    if user.role == 'compliance_officer':
        return redirect('dashboard:compliance')
    elif user.role == 'fraud_analyst':
        return redirect('dashboard:analyst')
    elif user.role == 'risk_manager':
        return redirect('dashboard:risk')
    elif user.role == 'executive':
        return redirect('dashboard:executive')
    else:
        # Default to analyst dashboard for other roles
        return redirect('dashboard:analyst')


@login_required
def compliance_dashboard(request):
    """
    Dashboard for compliance officers.
    """
    # Get date range for filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get AML alerts
    aml_alerts = AMLAlert.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get alert counts by status
    alert_status_counts = aml_alerts.values('status').annotate(count=Count('id'))
    
    # Get alert counts by type
    alert_type_counts = aml_alerts.values('alert_type').annotate(count=Count('id'))
    
    # Get recent alerts
    recent_alerts = aml_alerts.order_by('-created_at')[:10]
    
    context = {
        'alert_count': aml_alerts.count(),
        'open_alert_count': aml_alerts.filter(status='open').count(),
        'alert_status_counts': alert_status_counts,
        'alert_type_counts': alert_type_counts,
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'dashboard/compliance/index.html', context)


@login_required
def analyst_dashboard(request):
    """
    Dashboard for fraud analysts.
    """
    # Get date range for filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get fraud cases from the cases app
    fraud_cases = Case.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get transaction counts by status
    transaction_status_counts = transactions.values('status').annotate(count=Count('id'))
    
    # Get transaction counts by channel
    transaction_channel_counts = transactions.values('channel').annotate(count=Count('id'))
    
    # Get flagged transactions
    flagged_transactions = transactions.filter(is_flagged=True).order_by('-timestamp')[:10]
    
    # Get recent fraud cases
    recent_cases = fraud_cases.order_by('-created_at')[:10]
    
    context = {
        'transaction_count': transactions.count(),
        'flagged_count': transactions.filter(is_flagged=True).count(),
        'case_count': fraud_cases.count(),
        'transaction_status_counts': transaction_status_counts,
        'transaction_channel_counts': transaction_channel_counts,
        'flagged_transactions': flagged_transactions,
        'recent_cases': recent_cases,
    }
    
    return render(request, 'dashboard/analyst/index.html', context)


@login_required
def risk_dashboard(request):
    """
    Dashboard for risk managers.
    """
    # Get date range for filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get average risk score
    avg_risk_score = fraud_results.aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0
    
    # Get decision counts
    decision_counts = fraud_results.values('decision').annotate(count=Count('id'))
    
    # Get transaction volume by day
    from django.db.models.functions import TruncDay
    
    daily_volume = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('day')
    
    context = {
        'transaction_count': transactions.count(),
        'transaction_volume': transactions.aggregate(total=Sum('amount'))['total'] or 0,
        'avg_risk_score': avg_risk_score,
        'decision_counts': decision_counts,
        'daily_volume': daily_volume,
    }
    
    return render(request, 'dashboard/risk/index.html', context)


@login_required
def executive_dashboard(request):
    """
    Dashboard for executives.
    """
    # Get date range for filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get transaction counts by channel
    transaction_channel_counts = transactions.values('channel').annotate(count=Count('id'))
    
    # Get transaction volume by channel
    transaction_channel_volume = transactions.values('channel').annotate(total=Sum('amount'))
    
    # Get fraud rate
    fraud_count = fraud_results.filter(is_fraudulent=True).count()
    fraud_rate = (fraud_count / transactions.count() * 100) if transactions.count() > 0 else 0
    
    # Get financial impact - we need to join with transactions
    # Since we don't have a direct relationship, we'll calculate this differently
    fraud_transaction_ids = fraud_results.filter(is_fraudulent=True).values_list('transaction_id', flat=True)
    financial_impact = transactions.filter(transaction_id__in=fraud_transaction_ids).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'transaction_count': transactions.count(),
        'transaction_volume': transactions.aggregate(total=Sum('amount'))['total'] or 0,
        'fraud_count': fraud_count,
        'fraud_rate': fraud_rate,
        'financial_impact': financial_impact,
        'transaction_channel_counts': transaction_channel_counts,
        'transaction_channel_volume': transaction_channel_volume,
    }
    
    return render(request, 'dashboard/executive/index.html', context)