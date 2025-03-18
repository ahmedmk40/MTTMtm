"""
Management command to initialize fraud detection rules.
"""

from django.core.management.base import BaseCommand
from apps.rule_engine.rules.amount_rules import create_amount_rules
from apps.rule_engine.rules.geographic_rules import create_geographic_rules
from apps.rule_engine.rules.card_rules import create_card_rules
from apps.rule_engine.rules.aml_rules import create_aml_rules


class Command(BaseCommand):
    """
    Command to initialize fraud detection rules.
    """
    
    help = 'Initialize fraud detection rules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--created-by',
            type=str,
            default='system',
            help='Username of the creator'
        )
    
    def handle(self, *args, **options):
        created_by = options['created_by']
        
        self.stdout.write(self.style.NOTICE('Initializing fraud detection rules...'))
        
        # Create amount rules
        self.stdout.write('Creating amount rules...')
        create_amount_rules(created_by)
        
        # Create geographic rules
        self.stdout.write('Creating geographic rules...')
        create_geographic_rules(created_by)
        
        # Create card rules
        self.stdout.write('Creating card rules...')
        create_card_rules(created_by)
        
        # Create AML rules
        self.stdout.write('Creating AML rules...')
        create_aml_rules(created_by)
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized fraud detection rules'))