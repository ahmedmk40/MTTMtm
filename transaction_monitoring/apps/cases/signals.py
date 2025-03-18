"""
Signal handlers for the cases app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Case, CaseTransaction, CaseNote, CaseAttachment, CaseActivity


@receiver(post_save, sender=Case)
def create_case_activity_on_create(sender, instance, created, **kwargs):
    """
    Create a case activity when a case is created.
    """
    if created:
        CaseActivity.objects.create(
            case=instance,
            activity_type='create',
            description=f"Case {instance.case_id} was created.",
            performed_by=instance.created_by
        )


@receiver(pre_save, sender=Case)
def track_case_changes(sender, instance, **kwargs):
    """
    Track changes to a case.
    """
    if instance.pk:
        try:
            old_instance = Case.objects.get(pk=instance.pk)
            
            # Check for status change
            if old_instance.status != instance.status:
                CaseActivity.objects.create(
                    case=instance,
                    activity_type='status_change',
                    description=f"Case status changed from {old_instance.get_status_display()} to {instance.get_status_display()}.",
                    performed_by=instance.assigned_to
                )
            
            # Check for assignment change
            if old_instance.assigned_to != instance.assigned_to and instance.assigned_to:
                CaseActivity.objects.create(
                    case=instance,
                    activity_type='assign',
                    description=f"Case assigned to {instance.assigned_to}.",
                    performed_by=instance.assigned_to
                )
            
            # Check for case closure
            if old_instance.status != 'closed' and instance.status == 'closed':
                instance.closed_at = timezone.now()
                CaseActivity.objects.create(
                    case=instance,
                    activity_type='close',
                    description=f"Case closed with resolution: {instance.get_resolution_display()}.",
                    performed_by=instance.assigned_to
                )
        except Case.DoesNotExist:
            pass


@receiver(post_save, sender=CaseTransaction)
def create_transaction_activity(sender, instance, created, **kwargs):
    """
    Create an activity when a transaction is added to a case.
    """
    if created:
        CaseActivity.objects.create(
            case=instance.case,
            activity_type='add_transaction',
            description=f"Transaction {instance.transaction_id} added to the case.",
            performed_by=instance.added_by
        )


@receiver(post_save, sender=CaseNote)
def create_note_activity(sender, instance, created, **kwargs):
    """
    Create an activity when a note is added to a case.
    """
    if created:
        CaseActivity.objects.create(
            case=instance.case,
            activity_type='add_note',
            description=f"Note added to the case.",
            performed_by=instance.created_by
        )


@receiver(post_save, sender=CaseAttachment)
def create_attachment_activity(sender, instance, created, **kwargs):
    """
    Create an activity when an attachment is added to a case.
    """
    if created:
        CaseActivity.objects.create(
            case=instance.case,
            activity_type='add_attachment',
            description=f"File '{instance.filename}' attached to the case.",
            performed_by=instance.uploaded_by
        )