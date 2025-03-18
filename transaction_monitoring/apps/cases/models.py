"""
Models for the cases app.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Case(models.Model):
    """
    Model for fraud investigation cases.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Review'),
        ('closed', 'Closed'),
    ]
    
    RESOLUTION_CHOICES = [
        ('confirmed_fraud', 'Confirmed Fraud'),
        ('false_positive', 'False Positive'),
        ('inconclusive', 'Inconclusive'),
        ('legitimate', 'Legitimate'),
    ]
    
    case_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cases')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    
    # Metrics
    financial_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    risk_score = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.case_id} - {self.title}"
    
    def close_case(self, resolution, user=None):
        """
        Close the case with the specified resolution.
        """
        self.status = 'closed'
        self.resolution = resolution
        self.closed_at = timezone.now()
        if user:
            self.updated_by = user
        self.save()
    
    class Meta:
        ordering = ['-created_at']


class CaseTransaction(models.Model):
    """
    Model for linking transactions to cases.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('case', 'transaction_id')
        ordering = ['-added_at']


class CaseNote(models.Model):
    """
    Model for case notes.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']


class CaseAttachment(models.Model):
    """
    Model for case attachments.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='case_attachments/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']


class CaseActivity(models.Model):
    """
    Model for tracking case activity.
    """
    ACTIVITY_TYPES = [
        ('create', 'Case Created'),
        ('update', 'Case Updated'),
        ('assign', 'Case Assigned'),
        ('status_change', 'Status Changed'),
        ('add_transaction', 'Transaction Added'),
        ('add_note', 'Note Added'),
        ('add_attachment', 'Attachment Added'),
        ('close', 'Case Closed'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    performed_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-performed_at']
        verbose_name_plural = 'Case activities'
