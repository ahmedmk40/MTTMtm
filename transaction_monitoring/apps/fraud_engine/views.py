"""
Views for the Fraud Engine app.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

from .models import BlockList, FraudCase, FraudDetectionResult
from .services.block_service import add_to_blocklist

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    Fraud Engine dashboard.
    """
    # Get statistics
    total_blocks = BlockList.objects.filter(is_active=True).count()
    active_blocks = BlockList.objects.filter(
        is_active=True
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).count()
    
    # Get recent fraud cases
    recent_cases = FraudCase.objects.order_by('-created_at')[:5]
    
    # Get recent fraud detection results
    recent_results = FraudDetectionResult.objects.order_by('-created_at')[:10]
    
    # Get block list statistics by type
    block_stats = {}
    for entity_type, _ in BlockList.ENTITY_TYPE_CHOICES:
        block_stats[entity_type] = BlockList.objects.filter(
            entity_type=entity_type, 
            is_active=True
        ).count()
    
    context = {
        'total_blocks': total_blocks,
        'active_blocks': active_blocks,
        'recent_cases': recent_cases,
        'recent_results': recent_results,
        'block_stats': block_stats,
    }
    
    return render(request, 'fraud_engine/dashboard.html', context)


@login_required
def blocklist(request):
    """
    List all blocklist entries.
    """
    # Get filter parameters
    entity_type = request.GET.get('entity_type', '')
    is_active = request.GET.get('is_active', '')
    search_query = request.GET.get('q', '')
    
    # Start with all entries
    entries = BlockList.objects.all()
    
    # Apply filters
    if entity_type:
        entries = entries.filter(entity_type=entity_type)
    
    if is_active:
        is_active_bool = is_active.lower() == 'true'
        entries = entries.filter(is_active=is_active_bool)
    
    if search_query:
        entries = entries.filter(
            Q(entity_value__icontains=search_query) | 
            Q(reason__icontains=search_query) |
            Q(added_by__icontains=search_query)
        )
    
    # Order by most recent first
    entries = entries.order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(entries, 20)  # 20 entries per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'entity_types': BlockList.ENTITY_TYPE_CHOICES,
        'filter_entity_type': entity_type,
        'filter_is_active': is_active,
        'search_query': search_query,
    }
    
    return render(request, 'fraud_engine/blocklist.html', context)


@login_required
@permission_required('fraud_engine.add_blocklist')
def blocklist_add(request):
    """
    Add a new blocklist entry.
    """
    if request.method == 'POST':
        entity_type = request.POST.get('entity_type')
        entity_value = request.POST.get('entity_value')
        reason = request.POST.get('reason')
        expires_at = request.POST.get('expires_at') or None
        
        if not entity_type or not entity_value or not reason:
            messages.error(request, "All fields are required.")
            return redirect('fraud_engine:blocklist_add')
        
        try:
            # Add to blocklist
            blocklist_entry = add_to_blocklist(
                entity_type=entity_type,
                entity_value=entity_value,
                reason=reason,
                added_by=request.user.username,
                expires_at=expires_at
            )
            
            messages.success(request, f"Added {entity_type} to blocklist successfully.")
            return redirect('fraud_engine:blocklist')
        
        except Exception as e:
            logger.error(f"Error adding to blocklist: {str(e)}", exc_info=True)
            messages.error(request, f"Error adding to blocklist: {str(e)}")
            return redirect('fraud_engine:blocklist_add')
    
    context = {
        'entity_types': BlockList.ENTITY_TYPE_CHOICES,
    }
    
    return render(request, 'fraud_engine/blocklist_add.html', context)


@login_required
@permission_required('fraud_engine.change_blocklist')
def blocklist_edit(request, blocklist_id):
    """
    Edit a blocklist entry.
    """
    blocklist_entry = get_object_or_404(BlockList, id=blocklist_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        is_active = request.POST.get('is_active') == 'on'
        expires_at = request.POST.get('expires_at') or None
        
        if not reason:
            messages.error(request, "Reason is required.")
            return redirect('fraud_engine:blocklist_edit', blocklist_id=blocklist_id)
        
        try:
            # Update blocklist entry
            blocklist_entry.reason = reason
            blocklist_entry.is_active = is_active
            blocklist_entry.expires_at = expires_at
            blocklist_entry.save()
            
            messages.success(request, "Blocklist entry updated successfully.")
            return redirect('fraud_engine:blocklist')
        
        except Exception as e:
            logger.error(f"Error updating blocklist entry: {str(e)}", exc_info=True)
            messages.error(request, f"Error updating blocklist entry: {str(e)}")
            return redirect('fraud_engine:blocklist_edit', blocklist_id=blocklist_id)
    
    context = {
        'entry': blocklist_entry,
    }
    
    return render(request, 'fraud_engine/blocklist_edit.html', context)


@login_required
@permission_required('fraud_engine.delete_blocklist')
def blocklist_delete(request, blocklist_id):
    """
    Delete a blocklist entry.
    """
    blocklist_entry = get_object_or_404(BlockList, id=blocklist_id)
    
    if request.method == 'POST':
        try:
            # Delete blocklist entry
            entity_type = blocklist_entry.get_entity_type_display()
            entity_value = blocklist_entry.entity_value
            
            blocklist_entry.delete()
            
            messages.success(request, f"Deleted {entity_type}: {entity_value} from blocklist.")
            return redirect('fraud_engine:blocklist')
        
        except Exception as e:
            logger.error(f"Error deleting blocklist entry: {str(e)}", exc_info=True)
            messages.error(request, f"Error deleting blocklist entry: {str(e)}")
            return redirect('fraud_engine:blocklist')
    
    context = {
        'entry': blocklist_entry,
    }
    
    return render(request, 'fraud_engine/blocklist_delete.html', context)


@login_required
def fraud_cases(request):
    """
    List all fraud cases.
    """
    # Get filter parameters
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    search_query = request.GET.get('q', '')
    
    # Start with all cases
    cases = FraudCase.objects.all()
    
    # Apply filters
    if status:
        cases = cases.filter(status=status)
    
    if priority:
        cases = cases.filter(priority=priority)
    
    if search_query:
        cases = cases.filter(
            Q(case_id__icontains=search_query) | 
            Q(user_id__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(assigned_to__icontains=search_query)
        )
    
    # Order by most recent first
    cases = cases.order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(cases, 20)  # 20 cases per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': FraudCase.CASE_STATUS_CHOICES,
        'priority_choices': FraudCase.CASE_PRIORITY_CHOICES,
        'filter_status': status,
        'filter_priority': priority,
        'search_query': search_query,
    }
    
    return render(request, 'fraud_engine/cases.html', context)


@login_required
def fraud_case_detail(request, case_id):
    """
    Display details of a specific fraud case.
    """
    case = get_object_or_404(FraudCase, case_id=case_id)
    
    context = {
        'case': case,
    }
    
    return render(request, 'fraud_engine/case_detail.html', context)


@login_required
def detection_results(request):
    """
    List all fraud detection results.
    """
    # Get filter parameters
    decision = request.GET.get('decision', '')
    is_fraudulent = request.GET.get('is_fraudulent', '')
    search_query = request.GET.get('q', '')
    
    # Start with all results
    results = FraudDetectionResult.objects.all()
    
    # Apply filters
    if decision:
        results = results.filter(decision=decision)
    
    if is_fraudulent:
        is_fraudulent_bool = is_fraudulent.lower() == 'true'
        results = results.filter(is_fraudulent=is_fraudulent_bool)
    
    if search_query:
        results = results.filter(transaction_id__icontains=search_query)
    
    # Order by most recent first
    results = results.order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(results, 20)  # 20 results per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'decision_choices': (
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('review', 'Review'),
        ),
        'filter_decision': decision,
        'filter_is_fraudulent': is_fraudulent,
        'search_query': search_query,
    }
    
    return render(request, 'fraud_engine/results.html', context)


@login_required
def detection_result_detail(request, transaction_id):
    """
    Display details of a specific fraud detection result.
    """
    result = get_object_or_404(FraudDetectionResult, transaction_id=transaction_id)
    
    context = {
        'result': result,
    }
    
    return render(request, 'fraud_engine/result_detail.html', context)