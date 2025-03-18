import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.aml.models import AMLAlert, TransactionPattern

# Update AMLAlert.ALERT_TYPE_CHOICES
if 'sequential_account_generation' not in [choice[0] for choice in AMLAlert.ALERT_TYPE_CHOICES]:
    print("Adding 'sequential_account_generation' to AMLAlert.ALERT_TYPE_CHOICES")
    
    # Create a new tuple with the additional choice
    new_choices = list(AMLAlert.ALERT_TYPE_CHOICES)
    # Insert before 'other'
    new_choices.insert(-1, ('sequential_account_generation', 'Sequential Account Generation Attack'))
    
    # Update the model's ALERT_TYPE_CHOICES
    AMLAlert.ALERT_TYPE_CHOICES = tuple(new_choices)
    
    print("Updated AMLAlert.ALERT_TYPE_CHOICES")
else:
    print("'sequential_account_generation' already exists in AMLAlert.ALERT_TYPE_CHOICES")

# Update TransactionPattern.PATTERN_TYPE_CHOICES
if 'sequential_account_generation' not in [choice[0] for choice in TransactionPattern.PATTERN_TYPE_CHOICES]:
    print("Adding 'sequential_account_generation' to TransactionPattern.PATTERN_TYPE_CHOICES")
    
    # Create a new tuple with the additional choice
    new_choices = list(TransactionPattern.PATTERN_TYPE_CHOICES)
    # Insert before 'other'
    new_choices.insert(-1, ('sequential_account_generation', 'Sequential Account Generation Attack'))
    
    # Update the model's PATTERN_TYPE_CHOICES
    TransactionPattern.PATTERN_TYPE_CHOICES = tuple(new_choices)
    
    print("Updated TransactionPattern.PATTERN_TYPE_CHOICES")
else:
    print("'sequential_account_generation' already exists in TransactionPattern.PATTERN_TYPE_CHOICES")

print("Done updating AML models")