"""
Models for the notifications app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class Notification(models.Model):
    """
    Model for storing user notifications.
    """
    
    NOTIFICATION_TYPES = (
        ('info', _('Information')),
        ('success', _('Success')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('system', _('System')),
        ('fraud_alert', _('Fraud Alert')),
        ('aml_alert', _('AML Alert')),
        ('rule_trigger', _('Rule Trigger')),
        ('case_update', _('Case Update')),
    )
    
    PRIORITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User')
    )
    
    notification_type = models.CharField(
        _('Notification Type'),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )
    
    title = models.CharField(_('Title'), max_length=255)
    message = models.TextField(_('Message'))
    
    link_url = models.CharField(_('Link URL'), max_length=255, blank=True, null=True)
    link_text = models.CharField(_('Link Text'), max_length=100, blank=True, null=True)
    
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    is_read = models.BooleanField(_('Is Read'), default=False)
    is_deleted = models.BooleanField(_('Is Deleted'), default=False)
    read_at = models.DateTimeField(_('Read At'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    related_object_type = models.CharField(_('Related Object Type'), max_length=100, blank=True, null=True)
    related_object_id = models.CharField(_('Related Object ID'), max_length=100, blank=True, null=True)
    
    extra_data = models.JSONField(_('Extra Data'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['related_object_type', 'related_object_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        self.is_read = False
        self.read_at = None
        self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def soft_delete(self):
        """Soft delete the notification."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
    
    def get_absolute_url(self):
        """Return the URL for the notification."""
        if self.link_url:
            return self.link_url
        
        return reverse('notifications:detail', kwargs={'pk': self.pk})
    
    @property
    def bootstrap_class(self):
        """Return the Bootstrap class for the notification type."""
        type_map = {
            'info': 'info',
            'success': 'success',
            'warning': 'warning',
            'error': 'danger',
            'system': 'dark',
            'fraud_alert': 'danger',
            'aml_alert': 'warning',
            'rule_trigger': 'primary',
            'case_update': 'info',
        }
        
        return type_map.get(self.notification_type, 'info')
    
    @property
    def icon_class(self):
        """Return the Font Awesome icon class for the notification type."""
        type_map = {
            'info': 'fa-info-circle',
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-times-circle',
            'system': 'fa-cog',
            'fraud_alert': 'fa-shield-alt',
            'aml_alert': 'fa-money-bill-wave',
            'rule_trigger': 'fa-bolt',
            'case_update': 'fa-folder-open',
        }
        
        return type_map.get(self.notification_type, 'fa-bell')


class NotificationPreference(models.Model):
    """
    Model for notification preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('User')
    )
    
    # Email notifications
    email_fraud_alerts = models.BooleanField(_('Email Fraud Alerts'), default=True)
    email_aml_alerts = models.BooleanField(_('Email AML Alerts'), default=True)
    email_case_updates = models.BooleanField(_('Email Case Updates'), default=True)
    email_system_notifications = models.BooleanField(_('Email System Notifications'), default=True)
    
    # In-app notifications
    in_app_fraud_alerts = models.BooleanField(_('In-App Fraud Alerts'), default=True)
    in_app_aml_alerts = models.BooleanField(_('In-App AML Alerts'), default=True)
    in_app_case_updates = models.BooleanField(_('In-App Case Updates'), default=True)
    in_app_rule_triggers = models.BooleanField(_('In-App Rule Triggers'), default=True)
    in_app_system_notifications = models.BooleanField(_('In-App System Notifications'), default=True)
    
    # SMS notifications
    sms_fraud_alerts = models.BooleanField(_('SMS Fraud Alerts'), default=False)
    sms_aml_alerts = models.BooleanField(_('SMS AML Alerts'), default=False)
    sms_case_updates = models.BooleanField(_('SMS Case Updates'), default=False)
    
    # Notification thresholds
    min_priority_for_email = models.CharField(_('Min Priority for Email'), max_length=10, choices=Notification.PRIORITY_CHOICES, default='medium')
    min_priority_for_sms = models.CharField(_('Min Priority for SMS'), max_length=10, choices=Notification.PRIORITY_CHOICES, default='high')
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"Notification Preferences for {self.user.username}"