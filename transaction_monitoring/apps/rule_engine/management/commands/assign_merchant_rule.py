"""
Management command to assign a rule to a specific merchant.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.rule_engine.models import Rule


class Command(BaseCommand):
    """
    Command to assign a rule to a specific merchant.
    """
    
    help = 'Assign a rule to a specific merchant'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'rule_id',
            type=int,
            help='ID of the rule to assign'
        )
        
        parser.add_argument(
            'merchant_id',
            type=str,
            help='Merchant ID to assign the rule to'
        )
        
        parser.add_argument(
            '--exclude',
            action='store_true',
            help='Exclude this merchant from the rule instead of including it'
        )
        
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove this merchant from the included/excluded list'
        )
    
    def handle(self, *args, **options):
        rule_id = options['rule_id']
        merchant_id = options['merchant_id']
        exclude = options['exclude']
        remove = options['remove']
        
        try:
            rule = Rule.objects.get(id=rule_id)
        except Rule.DoesNotExist:
            raise CommandError(f"Rule with ID {rule_id} does not exist")
        
        if remove:
            # Remove merchant from included/excluded list
            if merchant_id in rule.included_merchants:
                rule.included_merchants.remove(merchant_id)
                self.stdout.write(self.style.SUCCESS(
                    f"Removed merchant {merchant_id} from included merchants for rule '{rule.name}'"
                ))
            
            if merchant_id in rule.excluded_merchants:
                rule.excluded_merchants.remove(merchant_id)
                self.stdout.write(self.style.SUCCESS(
                    f"Removed merchant {merchant_id} from excluded merchants for rule '{rule.name}'"
                ))
            
            # If no merchants are left in the lists, disable merchant-specific flag
            if not rule.included_merchants and not rule.excluded_merchants:
                rule.merchant_specific = False
                self.stdout.write(self.style.NOTICE(
                    f"Disabled merchant-specific flag for rule '{rule.name}' as no merchants are specified"
                ))
        
        elif exclude:
            # Add merchant to excluded list
            if merchant_id not in rule.excluded_merchants:
                rule.excluded_merchants.append(merchant_id)
                self.stdout.write(self.style.SUCCESS(
                    f"Added merchant {merchant_id} to excluded merchants for rule '{rule.name}'"
                ))
            
            # Remove from included list if present
            if merchant_id in rule.included_merchants:
                rule.included_merchants.remove(merchant_id)
                self.stdout.write(self.style.NOTICE(
                    f"Removed merchant {merchant_id} from included merchants for rule '{rule.name}'"
                ))
        
        else:
            # Add merchant to included list
            if merchant_id not in rule.included_merchants:
                rule.included_merchants.append(merchant_id)
                self.stdout.write(self.style.SUCCESS(
                    f"Added merchant {merchant_id} to included merchants for rule '{rule.name}'"
                ))
            
            # Remove from excluded list if present
            if merchant_id in rule.excluded_merchants:
                rule.excluded_merchants.remove(merchant_id)
                self.stdout.write(self.style.NOTICE(
                    f"Removed merchant {merchant_id} from excluded merchants for rule '{rule.name}'"
                ))
            
            # Enable merchant-specific flag
            if not rule.merchant_specific:
                rule.merchant_specific = True
                self.stdout.write(self.style.NOTICE(
                    f"Enabled merchant-specific flag for rule '{rule.name}'"
                ))
        
        # Save the rule
        rule.save()
        
        # Display current status
        if rule.merchant_specific:
            if rule.included_merchants:
                self.stdout.write(f"Rule '{rule.name}' now applies to these merchants: {', '.join(rule.included_merchants)}")
            else:
                self.stdout.write(f"Rule '{rule.name}' now applies to all merchants except: {', '.join(rule.excluded_merchants)}")
        else:
            self.stdout.write(f"Rule '{rule.name}' now applies to all merchants")