"""
Signal handlers for the transactions app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction


@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=POSTransaction)
@receiver(post_save, sender=EcommerceTransaction)
@receiver(post_save, sender=WalletTransaction)
def transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for transaction post-save.
    
    This will trigger fraud detection processes when a transaction is created.
    """
    if created:
        # Import here to avoid circular imports
        from apps.fraud_engine.tasks import process_transaction
        
        # Queue the transaction for fraud detection processing using Celery
        try:
            process_transaction.delay(
                transaction_id=instance.transaction_id,
                transaction_type=instance.transaction_type,
                channel=instance.channel
            )
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the transaction creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error queuing transaction {instance.transaction_id} for processing: {str(e)}", exc_info=True)