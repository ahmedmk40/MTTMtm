"""
Models for the accounts app.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model with additional fields.
    """
    ROLE_CHOICES = (
        ('compliance_officer', _('Compliance Officer')),
        ('fraud_analyst', _('Fraud Analyst')),
        ('risk_manager', _('Risk Manager')),
        ('system_admin', _('System Administrator')),
        ('data_analyst', _('Data Analyst')),
        ('executive', _('Executive')),
    )
    
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    department = models.CharField(_('Department'), max_length=100, null=True, blank=True)
    phone_number = models.CharField(_('Phone Number'), max_length=20, null=True, blank=True)
    
    # Profile settings
    profile_picture = models.ImageField(_('Profile Picture'), upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(_('Bio'), null=True, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(_('Email Notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS Notifications'), default=False)
    
    # Security settings
    two_factor_enabled = models.BooleanField(_('Two-Factor Authentication'), default=False)
    last_password_change = models.DateTimeField(_('Last Password Change'), null=True, blank=True)
    
    # Audit fields
    created_by = models.CharField(_('Created By'), max_length=100, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(_('Last Login IP'), null=True, blank=True)
    last_login_device_id = models.CharField(_('Last Login Device ID'), max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def save(self, *args, **kwargs):
        """Override save method to handle role-based group assignments."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # If this is a new user or the role has changed, update group membership
        if is_new or self._role_changed:
            self.update_role_groups()
    
    def update_role_groups(self):
        """Update the user's group membership based on their role."""
        from django.contrib.auth.models import Group
        
        # Remove user from all role groups
        role_groups = Group.objects.filter(name__in=[role[1] for role in self.ROLE_CHOICES])
        for group in role_groups:
            self.groups.remove(group)
        
        # Add user to the appropriate role group
        if self.role:
            role_display = dict(self.ROLE_CHOICES).get(self.role)
            if role_display:
                group, created = Group.objects.get_or_create(name=role_display)
                self.groups.add(group)
    
    @property
    def _role_changed(self):
        """Check if the role has changed."""
        if not self.pk:
            return True
        
        try:
            old_instance = self.__class__.objects.get(pk=self.pk)
            return old_instance.role != self.role
        except self.__class__.DoesNotExist:
            return True
    
    def is_compliance_officer(self):
        """Check if the user is a compliance officer."""
        return self.role == 'compliance_officer'
    
    def is_fraud_analyst(self):
        """Check if the user is a fraud analyst."""
        return self.role == 'fraud_analyst'
    
    def is_risk_manager(self):
        """Check if the user is a risk manager."""
        return self.role == 'risk_manager'
    
    def is_system_admin(self):
        """Check if the user is a system administrator."""
        return self.role == 'system_admin'
    
    def is_data_analyst(self):
        """Check if the user is a data analyst."""
        return self.role == 'data_analyst'
    
    def is_executive(self):
        """Check if the user is an executive."""
        return self.role == 'executive'