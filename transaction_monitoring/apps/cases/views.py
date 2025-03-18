"""
Views for the cases app.
"""
import csv
import json
from datetime import datetime, timedelta

import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse

from .models import Case, CaseTransaction, CaseNote, CaseAttachment, CaseActivity
from .forms import CaseForm, CaseNoteForm, CaseAttachmentForm, CaseFilterForm, AddTransactionForm
from apps.transactions.models import Transaction
from apps.fraud_engine.models import FraudDetectionResult


@login_required
def case_list(request):
    """
    View for listing cases with filtering.
    """
    form = CaseFilterForm(request.GET)
    cases = Case.objects.all()
    
    if form.is_valid():
        # Apply filters
        data = form.cleaned_data
        
        if data.get('case_id'):
            cases = cases.filter(case_id__icontains=data['case_id'])
        
        if data.get('title'):
            cases = cases.filter(title__icontains=data['title'])
        
        if data.get('status'):
            cases = cases.filter(status=data['status'])
        
        if data.get('priority'):
            cases = cases.filter(priority=data['priority'])
        
        if data.get('assigned_to'):
            cases = cases.filter(assigned_to=data['assigned_to'])
        
        if data.get('created_from'):
            cases = cases.filter(created_at__gte=data['created_from'])
        
        if data.get('created_to'):
            cases = cases.filter(created_at__lte=data['created_to'])
    
    # Pagination
    paginator = Paginator(cases, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get case statistics
    total_cases = Case.objects.count()
    open_cases = Case.objects.filter(status='open').count()
    in_progress_cases = Case.objects.filter(status='in_progress').count()
    pending_review_cases = Case.objects.filter(status='pending_review').count()
    closed_cases = Case.objects.filter(status='closed').count()
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'pending_review_cases': pending_review_cases,
        'closed_cases': closed_cases,
    }
    
    return render(request, 'cases/list.html', context)


@login_required
def case_detail(request, case_id):
    """
    View for case details.
    """
    case = get_object_or_404(Case, case_id=case_id)
    
    # Get case transactions
    case_transactions = CaseTransaction.objects.filter(case=case)
    transaction_ids = [ct.transaction_id for ct in case_transactions]
    transactions = Transaction.objects.filter(transaction_id__in=transaction_ids)
    
    # Get fraud detection results for transactions
    fraud_results = {
        result.transaction_id: result 
        for result in FraudDetectionResult.objects.filter(transaction_id__in=transaction_ids)
    }
    
    # Add fraud results to transactions
    for transaction in transactions:
        transaction.fraud_result = fraud_results.get(transaction.transaction_id)
    
    # Get case notes
    notes = CaseNote.objects.filter(case=case)
    
    # Get case attachments
    attachments = CaseAttachment.objects.filter(case=case)
    
    # Get case activities
    activities = CaseActivity.objects.filter(case=case)
    
    # Forms
    note_form = CaseNoteForm()
    attachment_form = CaseAttachmentForm()
    add_transaction_form = AddTransactionForm()
    
    # Handle note form submission
    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = CaseNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.case = case
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note added successfully.')
            return redirect('cases:detail', case_id=case_id)
    
    # Handle attachment form submission
    if request.method == 'POST' and 'add_attachment' in request.POST:
        attachment_form = CaseAttachmentForm(request.POST, request.FILES)
        if attachment_form.is_valid():
            attachment = attachment_form.save(commit=False)
            attachment.case = case
            attachment.uploaded_by = request.user
            attachment.save()
            messages.success(request, 'Attachment added successfully.')
            return redirect('cases:detail', case_id=case_id)
    
    # Handle add transaction form submission
    if request.method == 'POST' and 'add_transaction' in request.POST:
        add_transaction_form = AddTransactionForm(request.POST)
        if add_transaction_form.is_valid():
            transaction_ids = add_transaction_form.cleaned_data['transaction_ids']
            added_count = 0
            for tid in transaction_ids:
                # Check if transaction exists
                if Transaction.objects.filter(transaction_id=tid).exists():
                    # Check if transaction is already linked to the case
                    if not CaseTransaction.objects.filter(case=case, transaction_id=tid).exists():
                        CaseTransaction.objects.create(
                            case=case,
                            transaction_id=tid,
                            added_by=request.user
                        )
                        added_count += 1
            
            if added_count > 0:
                messages.success(request, f'{added_count} transaction(s) added to the case.')
            else:
                messages.warning(request, 'No transactions were added. They may not exist or are already linked to the case.')
            
            return redirect('cases:detail', case_id=case_id)
    
    context = {
        'case': case,
        'transactions': transactions,
        'notes': notes,
        'attachments': attachments,
        'activities': activities,
        'note_form': note_form,
        'attachment_form': attachment_form,
        'add_transaction_form': add_transaction_form,
    }
    
    return render(request, 'cases/detail.html', context)


@login_required
def case_create(request):
    """
    View for creating a new case.
    """
    if request.method == 'POST':
        form = CaseForm(request.POST, user=request.user)
        if form.is_valid():
            case = form.save(commit=False)
            # Generate a unique case ID
            case.case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            case.created_by = request.user
            case.save()
            
            # Add initial transaction if provided
            transaction_id = request.POST.get('transaction_id')
            if transaction_id and Transaction.objects.filter(transaction_id=transaction_id).exists():
                CaseTransaction.objects.create(
                    case=case,
                    transaction_id=transaction_id,
                    added_by=request.user
                )
            
            messages.success(request, f'Case {case.case_id} created successfully.')
            return redirect('cases:detail', case_id=case.case_id)
    else:
        form = CaseForm(user=request.user)
        
        # Pre-fill with transaction ID if provided
        transaction_id = request.GET.get('transaction_id')
        if transaction_id:
            # Get transaction details for pre-filling
            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)
                fraud_result = FraudDetectionResult.objects.filter(transaction_id=transaction_id).first()
                
                # Pre-fill title with transaction ID
                form.initial['title'] = f"Investigation for {transaction_id}"
                
                # Pre-fill description with transaction details
                description = f"Investigation for transaction {transaction_id}.\n"
                description += f"Amount: {transaction.amount} {transaction.currency}\n"
                description += f"User ID: {transaction.user_id}\n"
                
                if fraud_result:
                    description += f"Risk Score: {fraud_result.risk_score}\n"
                    if fraud_result.triggered_rules:
                        description += f"Triggered Rules: {', '.join(fraud_result.triggered_rules)}\n"
                
                form.initial['description'] = description
                
                # Set priority based on risk score
                if fraud_result and fraud_result.risk_score:
                    if fraud_result.risk_score >= 80:
                        form.initial['priority'] = 'critical'
                    elif fraud_result.risk_score >= 60:
                        form.initial['priority'] = 'high'
                    elif fraud_result.risk_score >= 40:
                        form.initial['priority'] = 'medium'
                    else:
                        form.initial['priority'] = 'low'
            except Transaction.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'transaction_id': transaction_id if 'transaction_id' in request.GET else None,
    }
    
    return render(request, 'cases/create.html', context)


@login_required
def case_edit(request, case_id):
    """
    View for editing a case.
    """
    case = get_object_or_404(Case, case_id=case_id)
    
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Case {case.case_id} updated successfully.')
            return redirect('cases:detail', case_id=case_id)
    else:
        form = CaseForm(instance=case, user=request.user)
    
    context = {
        'form': form,
        'case': case,
    }
    
    return render(request, 'cases/edit.html', context)


@login_required
def case_close(request, case_id):
    """
    View for closing a case.
    """
    case = get_object_or_404(Case, case_id=case_id)
    
    if request.method == 'POST':
        resolution = request.POST.get('resolution')
        if resolution in dict(Case.RESOLUTION_CHOICES):
            case.close_case(resolution, request.user)
            messages.success(request, f'Case {case.case_id} closed successfully.')
        else:
            messages.error(request, 'Invalid resolution.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def case_reopen(request, case_id):
    """
    View for reopening a closed case.
    """
    case = get_object_or_404(Case, case_id=case_id)
    
    if case.status == 'closed':
        case.status = 'open'
        case.resolution = None
        case.closed_at = None
        case.save()
        
        CaseActivity.objects.create(
            case=case,
            activity_type='status_change',
            description=f"Case reopened.",
            performed_by=request.user
        )
        
        messages.success(request, f'Case {case.case_id} reopened successfully.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def remove_transaction(request, case_id, transaction_id):
    """
    View for removing a transaction from a case.
    """
    case = get_object_or_404(Case, case_id=case_id)
    case_transaction = get_object_or_404(CaseTransaction, case=case, transaction_id=transaction_id)
    
    if request.method == 'POST':
        case_transaction.delete()
        
        CaseActivity.objects.create(
            case=case,
            activity_type='update',
            description=f"Transaction {transaction_id} removed from the case.",
            performed_by=request.user
        )
        
        messages.success(request, f'Transaction {transaction_id} removed from the case.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def delete_note(request, case_id, note_id):
    """
    View for deleting a case note.
    """
    case = get_object_or_404(Case, case_id=case_id)
    note = get_object_or_404(CaseNote, id=note_id, case=case)
    
    if request.method == 'POST':
        note.delete()
        
        CaseActivity.objects.create(
            case=case,
            activity_type='update',
            description=f"Note deleted from the case.",
            performed_by=request.user
        )
        
        messages.success(request, 'Note deleted successfully.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def delete_attachment(request, case_id, attachment_id):
    """
    View for deleting a case attachment.
    """
    case = get_object_or_404(Case, case_id=case_id)
    attachment = get_object_or_404(CaseAttachment, id=attachment_id, case=case)
    
    if request.method == 'POST':
        filename = attachment.filename
        attachment.delete()
        
        CaseActivity.objects.create(
            case=case,
            activity_type='update',
            description=f"Attachment '{filename}' deleted from the case.",
            performed_by=request.user
        )
        
        messages.success(request, f'Attachment {filename} deleted successfully.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def assign_case(request, case_id):
    """
    View for assigning a case to a user.
    """
    case = get_object_or_404(Case, case_id=case_id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            case.assigned_to = user
            case.save()
            
            messages.success(request, f'Case assigned to {user.username} successfully.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid user.')
    
    return redirect('cases:detail', case_id=case_id)


@login_required
def search_transactions(request):
    """
    AJAX view for searching transactions to add to a case.
    """
    query = request.GET.get('q', '')
    results = []
    
    if query:
        transactions = Transaction.objects.filter(
            Q(transaction_id__icontains=query) |
            Q(user_id__icontains=query)
        )[:10]
        
        for transaction in transactions:
            results.append({
                'id': transaction.transaction_id,
                'text': f"{transaction.transaction_id} - {transaction.user_id} - {transaction.amount} {transaction.currency}"
            })
    
    return JsonResponse({'results': results})


@login_required
def case_reports(request):
    """
    View for case reports and analytics.
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get cases created in the date range
    cases = Case.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    
    # Calculate statistics
    total_cases = cases.count()
    open_cases = cases.filter(status='open').count()
    in_progress_cases = cases.filter(status='in_progress').count()
    closed_cases = cases.filter(status='closed').count()
    
    # Cases by priority
    low_priority = cases.filter(priority='low').count()
    medium_priority = cases.filter(priority='medium').count()
    high_priority = cases.filter(priority='high').count()
    critical_priority = cases.filter(priority='critical').count()
    
    # Cases by resolution (for closed cases)
    confirmed_fraud = cases.filter(status='closed', resolution='confirmed_fraud').count()
    false_positive = cases.filter(status='closed', resolution='false_positive').count()
    inconclusive = cases.filter(status='closed', resolution='inconclusive').count()
    legitimate = cases.filter(status='closed', resolution='legitimate').count()
    
    # Calculate average time to resolution for closed cases
    avg_resolution_time = 0
    closed_with_time = cases.filter(status='closed', closed_at__isnull=False)
    if closed_with_time.exists():
        total_time = sum((case.closed_at - case.created_at).total_seconds() for case in closed_with_time)
        avg_resolution_time = total_time / closed_with_time.count() / 3600  # Convert to hours
    
    # Prepare data for charts
    status_data = {
        'labels': ['Open', 'In Progress', 'Closed'],
        'data': [open_cases, in_progress_cases, closed_cases]
    }
    
    priority_data = {
        'labels': ['Low', 'Medium', 'High', 'Critical'],
        'data': [low_priority, medium_priority, high_priority, critical_priority]
    }
    
    resolution_data = {
        'labels': ['Confirmed Fraud', 'False Positive', 'Inconclusive', 'Legitimate'],
        'data': [confirmed_fraud, false_positive, inconclusive, legitimate]
    }
    
    # Get recent cases for the report
    recent_cases = cases.order_by('-created_at')[:10]
    
    context = {
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'closed_cases': closed_cases,
        'avg_resolution_time': round(avg_resolution_time, 2),
        'status_data': json.dumps(status_data),
        'priority_data': json.dumps(priority_data),
        'resolution_data': json.dumps(resolution_data),
        'recent_cases': recent_cases
    }
    
    return render(request, 'cases/reports.html', context)


@login_required
def export_cases_csv(request):
    """
    Export cases to CSV file.
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get cases created in the date range
    cases = Case.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cases_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow([
        'Case ID', 'Title', 'Status', 'Priority', 'Resolution', 
        'Created At', 'Closed At', 'Created By', 'Assigned To',
        'Transaction Count', 'Note Count', 'Financial Impact'
    ])
    
    # Add case data
    for case in cases:
        writer.writerow([
            case.case_id,
            case.title,
            case.get_status_display(),
            case.get_priority_display(),
            case.get_resolution_display() if case.resolution else 'N/A',
            case.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            case.closed_at.strftime('%Y-%m-%d %H:%M:%S') if case.closed_at else 'N/A',
            case.created_by.username if case.created_by else 'N/A',
            case.assigned_to.username if case.assigned_to else 'Unassigned',
            case.transactions.count(),
            case.notes.count(),
            case.financial_impact
        ])
    
    return response
