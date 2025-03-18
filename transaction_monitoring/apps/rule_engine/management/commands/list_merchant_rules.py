"""
Management command to list merchant-specific rules.
"""

from django.core.management.base import BaseCommand
from apps.rule_engine.models import Rule
from django.db.models import Q


class Command(BaseCommand):
    """
    Command to list merchant-specific rules.
    """
    
    help = 'List merchant-specific rules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--merchant',
            type=str,
            help='Filter rules for a specific merchant ID'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all rules, including non-merchant-specific ones'
        )
    
    def handle(self, *args, **options):
        merchant_id = options.get('merchant')
        show_all = options.get('all')
        
        # Build query
        if show_all:
            rules = Rule.objects.all()
        else:
            rules = Rule.objects.filter(merchant_specific=True)
        
        # Filter by merchant if specified
        if merchant_id:
            rules = rules.filter(
                Q(merchant_specific=False) |  # Not merchant-specific (applies to all)
                Q(merchant_specific=True, included_merchants__contains=[merchant_id]) |  # Merchant-specific and includes this merchant
                Q(merchant_specific=True, included_merchants=[])  # Merchant-specific but no specific merchants listed (applies to all)
            ).exclude(
                excluded_merchants__contains=[merchant_id]  # Exclude rules where this merchant is explicitly excluded
            )
            
            self.stdout.write(self.style.NOTICE(f"Showing rules applicable to merchant {merchant_id}"))
        
        # Order by priority
        rules = rules.order_by('-priority', 'name')
        
        # Display rules
        if not rules.exists():
            self.stdout.write(self.style.WARNING("No rules found matching the criteria"))
            return
        
        self.stdout.write(f"Found {rules.count()} rules:")
        self.stdout.write("=" * 80)
        
        for rule in rules:
            self.stdout.write(f"ID: {rule.id} | Name: {rule.name} | Type: {rule.rule_type} | Priority: {rule.priority}")
            
            if rule.merchant_specific:
                if rule.included_merchants:
                    self.stdout.write(f"  Applies to merchants: {', '.join(rule.included_merchants)}")
                else:
                    self.stdout.write("  Applies to all merchants")
                
                if rule.excluded_merchants:
                    self.stdout.write(f"  Excluded merchants: {', '.join(rule.excluded_merchants)}")
            else:
                self.stdout.write("  Applies to all merchants")
            
            self.stdout.write(f"  Condition: {rule.condition}")
            self.stdout.write(f"  Action: {rule.action} | Risk Score: {rule.risk_score}")
            self.stdout.write("-" * 80)