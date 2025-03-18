"""
Views for the notifications app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from .models import Notification, NotificationPreference
from .utils import add_success_message, add_info_message, add_warning_message, add_error_message
from . import services


@login_required
def notification_list(request):
    """
    View for listing notifications.
    """
    # Get filter parameters
    notification_type = request.GET.get('type')
    is_read = request.GET.get('is_read')
    priority = request.GET.get('priority')
    
    # Build the query
    query = Q(user=request.user, is_deleted=False)
    
    if notification_type:
        query &= Q(notification_type=notification_type)
    
    if is_read == 'true':
        query &= Q(is_read=True)
    elif is_read == 'false':
        query &= Q(is_read=False)
    
    if priority:
        query &= Q(priority=priority)
    
    # Get notifications
    notifications = Notification.objects.filter(query).order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get notification stats
    stats = services.mark_all_notifications_as_read(request.user.id)
    
    context = {
        'page_obj': page_obj,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'priority_choices': Notification.PRIORITY_CHOICES,
        'selected_type': notification_type,
        'selected_is_read': is_read,
        'selected_priority': priority,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
def notification_detail(request, pk):
    """
    View for displaying a notification.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # Mark as read if not already
    if not notification.is_read:
        services.mark_notification_as_read(notification.id)
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/detail.html', context)


@login_required
@require_POST
def mark_as_read(request, pk):
    """
    View for marking a notification as read.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if services.mark_notification_as_read(notification.id):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            add_success_message(request, 'Notification marked as read.')
            return redirect('notifications:list')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False}, status=400)
        else:
            add_error_message(request, 'Failed to mark notification as read.')
            return redirect('notifications:list')


@login_required
@require_POST
def mark_all_as_read(request):
    """
    View for marking all notifications as read.
    """
    count = services.mark_all_notifications_as_read(request.user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': count})
    else:
        add_success_message(request, f'{count} notifications marked as read.')
        return redirect('notifications:list')


@login_required
@require_POST
def delete_notification(request, pk):
    """
    View for deleting a notification.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.soft_delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    else:
        add_success_message(request, 'Notification deleted.')
        return redirect('notifications:list')


@login_required
def preferences(request):
    """
    View for managing notification preferences.
    """
    # Get or create preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update email preferences
        preferences.email_fraud_alerts = request.POST.get('email_fraud_alerts') == 'on'
        preferences.email_aml_alerts = request.POST.get('email_aml_alerts') == 'on'
        preferences.email_case_updates = request.POST.get('email_case_updates') == 'on'
        preferences.email_system_notifications = request.POST.get('email_system_notifications') == 'on'
        
        # Update in-app preferences
        preferences.in_app_fraud_alerts = request.POST.get('in_app_fraud_alerts') == 'on'
        preferences.in_app_aml_alerts = request.POST.get('in_app_aml_alerts') == 'on'
        preferences.in_app_case_updates = request.POST.get('in_app_case_updates') == 'on'
        preferences.in_app_rule_triggers = request.POST.get('in_app_rule_triggers') == 'on'
        preferences.in_app_system_notifications = request.POST.get('in_app_system_notifications') == 'on'
        
        # Update SMS preferences
        preferences.sms_fraud_alerts = request.POST.get('sms_fraud_alerts') == 'on'
        preferences.sms_aml_alerts = request.POST.get('sms_aml_alerts') == 'on'
        preferences.sms_case_updates = request.POST.get('sms_case_updates') == 'on'
        
        # Update thresholds
        preferences.min_priority_for_email = request.POST.get('min_priority_for_email')
        preferences.min_priority_for_sms = request.POST.get('min_priority_for_sms')
        
        # Save preferences
        preferences.save()
        
        add_success_message(request, 'Notification preferences updated.')
        return redirect('notifications:preferences')
    
    context = {
        'preferences': preferences,
        'priority_choices': Notification.PRIORITY_CHOICES,
    }
    
    return render(request, 'notifications/preferences.html', context)


@login_required
def notification_badge(request):
    """
    View for getting the notification badge count.
    """
    count = Notification.objects.filter(user=request.user, is_read=False, is_deleted=False).count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'count': count})
    else:
        return HttpResponse(str(count))