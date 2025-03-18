"""
Management command to initialize velocity rules.
"""

from django.core.management.base import BaseCommand
from apps.velocity_engine.models import VelocityRule
from apps.core.constants import (
    TIME_WINDOW_5_MIN,
    TIME_WINDOW_15_MIN,
    TIME_WINDOW_1_HOUR,
    TIME_WINDOW_6_HOURS,
    TIME_WINDOW_24_HOURS,
)


class Command(BaseCommand):
    """
    Command to initialize velocity rules.
    """
    
    help = 'Initialize velocity rules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--created-by',
            type=str,
            default='system',
            help='Username of the creator'
        )
    
    def handle(self, *args, **options):
        created_by = options['created_by']
        
        self.stdout.write(self.style.NOTICE('Initializing velocity rules...'))
        
        # Define default velocity rules
        default_rules = [
            # User velocity rules
            {
                'name': 'User High Frequency 5m',
                'description': 'Flag users with high transaction frequency in 5 minutes',
                'entity_type': 'user_id',
                'time_window': TIME_WINDOW_5_MIN,
                'threshold': 5,
                'action': 'review',
                'risk_score': 70.0,
            },
            {
                'name': 'User High Frequency 1h',
                'description': 'Flag users with high transaction frequency in 1 hour',
                'entity_type': 'user_id',
                'time_window': TIME_WINDOW_1_HOUR,
                'threshold': 15,
                'action': 'review',
                'risk_score': 65.0,
            },
            {
                'name': 'User High Frequency 24h',
                'description': 'Flag users with high transaction frequency in 24 hours',
                'entity_type': 'user_id',
                'time_window': TIME_WINDOW_24_HOURS,
                'threshold': 50,
                'action': 'review',
                'risk_score': 60.0,
            },
            
            # Card velocity rules
            {
                'name': 'Card High Frequency 5m',
                'description': 'Flag cards with high transaction frequency in 5 minutes',
                'entity_type': 'card_number',
                'time_window': TIME_WINDOW_5_MIN,
                'threshold': 3,
                'action': 'review',
                'risk_score': 75.0,
            },
            {
                'name': 'Card High Frequency 15m',
                'description': 'Flag cards with high transaction frequency in 15 minutes',
                'entity_type': 'card_number',
                'time_window': TIME_WINDOW_15_MIN,
                'threshold': 5,
                'action': 'review',
                'risk_score': 70.0,
            },
            {
                'name': 'Card High Frequency 1h',
                'description': 'Flag cards with high transaction frequency in 1 hour',
                'entity_type': 'card_number',
                'time_window': TIME_WINDOW_1_HOUR,
                'threshold': 10,
                'action': 'review',
                'risk_score': 65.0,
            },
            
            # Device velocity rules
            {
                'name': 'Device High Frequency 5m',
                'description': 'Flag devices with high transaction frequency in 5 minutes',
                'entity_type': 'device_id',
                'time_window': TIME_WINDOW_5_MIN,
                'threshold': 3,
                'action': 'review',
                'risk_score': 75.0,
            },
            {
                'name': 'Device High Frequency 1h',
                'description': 'Flag devices with high transaction frequency in 1 hour',
                'entity_type': 'device_id',
                'time_window': TIME_WINDOW_1_HOUR,
                'threshold': 10,
                'action': 'review',
                'risk_score': 70.0,
            },
            
            # IP address velocity rules
            {
                'name': 'IP High Frequency 5m',
                'description': 'Flag IP addresses with high transaction frequency in 5 minutes',
                'entity_type': 'ip_address',
                'time_window': TIME_WINDOW_5_MIN,
                'threshold': 5,
                'action': 'review',
                'risk_score': 70.0,
            },
            {
                'name': 'IP High Frequency 1h',
                'description': 'Flag IP addresses with high transaction frequency in 1 hour',
                'entity_type': 'ip_address',
                'time_window': TIME_WINDOW_1_HOUR,
                'threshold': 20,
                'action': 'review',
                'risk_score': 65.0,
            },
            
            # Email velocity rules
            {
                'name': 'Email High Frequency 1h',
                'description': 'Flag emails with high transaction frequency in 1 hour',
                'entity_type': 'email',
                'time_window': TIME_WINDOW_1_HOUR,
                'threshold': 5,
                'action': 'review',
                'risk_score': 65.0,
            },
            {
                'name': 'Email High Frequency 6h',
                'description': 'Flag emails with high transaction frequency in 6 hours',
                'entity_type': 'email',
                'time_window': TIME_WINDOW_6_HOURS,
                'threshold': 10,
                'action': 'review',
                'risk_score': 60.0,
            },
        ]
        
        # Create velocity rules
        for rule_data in default_rules:
            rule, created = VelocityRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    'description': rule_data['description'],
                    'entity_type': rule_data['entity_type'],
                    'time_window': rule_data['time_window'],
                    'threshold': rule_data['threshold'],
                    'action': rule_data['action'],
                    'risk_score': rule_data['risk_score'],
                }
            )
            
            if created:
                self.stdout.write(f"Created rule: {rule.name}")
            else:
                self.stdout.write(f"Rule already exists: {rule.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized velocity rules'))