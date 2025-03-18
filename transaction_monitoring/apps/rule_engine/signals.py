"""
Signal handlers for the rule engine app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Rule, RuleSet