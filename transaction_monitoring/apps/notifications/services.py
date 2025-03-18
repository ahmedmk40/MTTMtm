"""
Services for the notifications app.
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = 'medium',
    related_object_type: str = None,
    related_object_id: str = None,
    metadata: Dict[str, Any] = None
) -> Notification:
    """
    Create a notification for a user.
    
    Args:
        user_id: The user ID to notify
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        priority: Notification priority
        related_object_type: Type of related object
        related_object_id: ID of related object
        metadata: Additional metadata
        
    Returns:
        The created Notification instance
    """
    if metadata is None:
        metadata = {}
    
    # Create notification
    notification = Notification.objects.create(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        metadata=metadata
    )
    
    logger.info(f"Created {priority} priority {notification_type} notification for user {user_id}")
    
    # Check if we should send email or SMS
    should_send_email = should_send_email_notification(user_id, notification_type, priority)
    should_send_sms = should_send_sms_notification(user_id, notification_type, priority)
    
    # Send email if needed
    if should_send_email:
        send_email_notification(notification)
    
    # Send SMS if needed
    if should_send_sms:
        send_sms_notification(notification)
    
    return notification


def should_send_email_notification(user_id: str, notification_type: str, priority: str) -> bool:
    """
    Check if an email notification should be sent.
    
    Args:
        user_id: The user ID
        notification_type: Type of notification
        priority: Notification priority
        
    Returns:
        True if email should be sent, False otherwise
    """
    try:
        # Get user preferences
        preferences, created = NotificationPreference.objects.get_or_create(user_id=user_id)
        
        # Check priority threshold
        priority_values = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        min_priority = preferences.min_priority_for_email
        
        if priority_values.get(priority, 0) < priority_values.get(min_priority, 0):
            return False
        
        # Check notification type preference
        if notification_type == 'fraud_alert' and not preferences.email_fraud_alerts:
            return False
        elif notification_type == 'aml_alert' and not preferences.email_aml_alerts:
            return False
        elif notification_type in ['case_assigned', 'case_updated'] and not preferences.email_case_updates:
            return False
        elif notification_type == 'system' and not preferences.email_system_notifications:
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking email notification preferences: {str(e)}", exc_info=True)
        return True  # Default to sending if there's an error


def should_send_sms_notification(user_id: str, notification_type: str, priority: str) -> bool:
    """
    Check if an SMS notification should be sent.
    
    Args:
        user_id: The user ID
        notification_type: Type of notification
        priority: Notification priority
        
    Returns:
        True if SMS should be sent, False otherwise
    """
    try:
        # Get user preferences
        preferences, created = NotificationPreference.objects.get_or_create(user_id=user_id)
        
        # Check priority threshold
        priority_values = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        min_priority = preferences.min_priority_for_sms
        
        if priority_values.get(priority, 0) < priority_values.get(min_priority, 0):
            return False
        
        # Check notification type preference
        if notification_type == 'fraud_alert' and not preferences.sms_fraud_alerts:
            return False
        elif notification_type == 'aml_alert' and not preferences.sms_aml_alerts:
            return False
        elif notification_type in ['case_assigned', 'case_updated'] and not preferences.sms_case_updates:
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking SMS notification preferences: {str(e)}", exc_info=True)
        return False  # Default to not sending if there's an error


def send_email_notification(notification: Notification) -> bool:
    """
    Send an email notification.
    
    Args:
        notification: The Notification instance
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # In a real system, this would send an actual email
        # For now, we'll just log it
        logger.info(
            f"SENDING EMAIL: {notification.notification_type} notification to user {notification.user_id}: "
            f"{notification.title}"
        )
        return True
    
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}", exc_info=True)
        return False


def send_sms_notification(notification: Notification) -> bool:
    """
    Send an SMS notification.
    
    Args:
        notification: The Notification instance
        
    Returns:
        True if SMS was sent successfully, False otherwise
    """
    try:
        # In a real system, this would send an actual SMS
        # For now, we'll just log it
        logger.info(
            f"SENDING SMS: {notification.notification_type} notification to user {notification.user_id}: "
            f"{notification.title}"
        )
        return True
    
    except Exception as e:
        logger.error(f"Error sending SMS notification: {str(e)}", exc_info=True)
        return False


def mark_notification_as_read(notification_id: int) -> bool:
    """
    Mark a notification as read.
    
    Args:
        notification_id: The notification ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return True
    
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return False
    
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
        return False


def mark_all_notifications_as_read(user_id: str) -> int:
    """
    Mark all notifications for a user as read.
    
    Args:
        user_id: The user ID
        
    Returns:
        Number of notifications marked as read
    """
    try:
        count = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return count
    
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}", exc_info=True)
        return 0