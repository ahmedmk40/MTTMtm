"""
Views for the reporting app.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
import csv
import io
from datetime import timedelta
from apps.transactions.models import Transaction
from apps.fraud_engine.models import FraudDetectionResult, FraudCase
from apps.aml.models import AMLAlert
from .forms import ReportFilterForm


@login_required
def report_list(request):
    """
    View for listing available reports.
    """
    return render(request, 'reports/list.html')


@login_required
def transaction_report(request):
    """
    View for transaction reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        
        if data.get('channel'):
            transactions = transactions.filter(channel=data['channel'])
        
        if data.get('status'):
            transactions = transactions.filter(status=data['status'])
        
        if data.get('is_flagged') is not None:
            transactions = transactions.filter(is_flagged=data['is_flagged'])
    
    # Get transaction counts by status
    transaction_status_counts = transactions.values('status').annotate(count=Count('id'))
    
    # Get transaction counts by channel
    transaction_channel_counts = transactions.values('channel').annotate(count=Count('id'))
    
    # Get transaction counts by type
    transaction_type_counts = transactions.values('transaction_type').annotate(count=Count('id'))
    
    # Get transaction volume by day
    from django.db.models.functions import TruncDay
    
    daily_volume = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('day')
    
    context = {
        'form': form,
        'transaction_count': transactions.count(),
        'transaction_volume': transactions.aggregate(total=Sum('amount'))['total'] or 0,
        'transaction_status_counts': transaction_status_counts,
        'transaction_channel_counts': transaction_channel_counts,
        'transaction_type_counts': transaction_type_counts,
        'daily_volume': daily_volume,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/transaction.html', context)


@login_required
def fraud_report(request):
    """
    View for fraud reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get fraud cases
    fraud_cases = FraudCase.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get decision counts
    decision_counts = fraud_results.values('decision').annotate(count=Count('id'))
    
    # Get case status counts
    case_status_counts = fraud_cases.values('status').annotate(count=Count('id'))
    
    # Get case priority counts
    case_priority_counts = fraud_cases.values('priority').annotate(count=Count('id'))
    
    # Get fraud rate by day
    from django.db.models.functions import TruncDay
    
    daily_fraud_rate = fraud_results.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total=Count('id'),
        fraudulent=Count('id', filter=models.Q(is_fraudulent=True))
    ).order_by('day')
    
    # Calculate fraud rate
    for day in daily_fraud_rate:
        day['rate'] = (day['fraudulent'] / day['total'] * 100) if day['total'] > 0 else 0
    
    context = {
        'form': form,
        'fraud_result_count': fraud_results.count(),
        'fraud_count': fraud_results.filter(is_fraudulent=True).count(),
        'case_count': fraud_cases.count(),
        'avg_risk_score': fraud_results.aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0,
        'decision_counts': decision_counts,
        'case_status_counts': case_status_counts,
        'case_priority_counts': case_priority_counts,
        'daily_fraud_rate': daily_fraud_rate,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/fraud.html', context)


@login_required
def aml_report(request):
    """
    View for AML reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get AML alerts
    aml_alerts = AMLAlert.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get alert counts by status
    alert_status_counts = aml_alerts.values('status').annotate(count=Count('id'))
    
    # Get alert counts by type
    alert_type_counts = aml_alerts.values('alert_type').annotate(count=Count('id'))
    
    # Get alert counts by day
    from django.db.models.functions import TruncDay
    
    daily_alert_counts = aml_alerts.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    context = {
        'form': form,
        'alert_count': aml_alerts.count(),
        'open_alert_count': aml_alerts.filter(status='open').count(),
        'alert_status_counts': alert_status_counts,
        'alert_type_counts': alert_type_counts,
        'daily_alert_counts': daily_alert_counts,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/aml.html', context)


@login_required
def performance_report(request):
    """
    View for system performance reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get average processing time
    avg_processing_time = fraud_results.aggregate(avg_time=Avg('processing_time'))['avg_time'] or 0
    
    # Get processing time by day
    from django.db.models.functions import TruncDay
    
    daily_processing_time = fraud_results.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        avg_time=Avg('processing_time')
    ).order_by('day')
    
    context = {
        'form': form,
        'result_count': fraud_results.count(),
        'avg_processing_time': avg_processing_time,
        'daily_processing_time': daily_processing_time,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/performance.html', context)


@login_required
def export_report(request, report_type):
    """
    View for exporting reports as CSV.
    """
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    # Create CSV writer
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    if report_type == 'transaction':
        # Get transactions
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Apply additional filters
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('transaction_type'):
                transactions = transactions.filter(transaction_type=data['transaction_type'])
            
            if data.get('channel'):
                transactions = transactions.filter(channel=data['channel'])
            
            if data.get('status'):
                transactions = transactions.filter(status=data['status'])
            
            if data.get('is_flagged') is not None:
                transactions = transactions.filter(is_flagged=data['is_flagged'])
        
        # Write header
        writer.writerow([
            'Transaction ID',
            'Type',
            'Channel',
            'Amount',
            'Currency',
            'User ID',
            'Timestamp',
            'Status',
            'Is Flagged',
            'Risk Score',
        ])
        
        # Write data
        for tx in transactions:
            writer.writerow([
                tx.transaction_id,
                tx.transaction_type,
                tx.channel,
                tx.amount,
                tx.currency,
                tx.user_id,
                tx.timestamp,
                tx.status,
                tx.is_flagged,
                tx.risk_score,
            ])
    
    elif report_type == 'fraud':
        # Get fraud detection results
        fraud_results = FraudDetectionResult.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Write header
        writer.writerow([
            'Transaction ID',
            'Risk Score',
            'Is Fraudulent',
            'Decision',
            'Processing Time',
            'Created At',
        ])
        
        # Write data
        for result in fraud_results:
            writer.writerow([
                result.transaction_id,
                result.risk_score,
                result.is_fraudulent,
                result.decision,
                result.processing_time,
                result.created_at,
            ])
    
    elif report_type == 'aml':
        # Get AML alerts
        aml_alerts = AMLAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Write header
        writer.writerow([
            'Alert ID',
            'User ID',
            'Alert Type',
            'Status',
            'Risk Score',
            'Created At',
        ])
        
        # Write data
        for alert in aml_alerts:
            writer.writerow([
                alert.alert_id,
                alert.user_id,
                alert.alert_type,
                alert.status,
                alert.risk_score,
                alert.created_at,
            ])
    
    # Write CSV to response
    response.write(csv_buffer.getvalue())
    
    return response