"""
Management command to analyze database performance.
"""

import time
import statistics
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings
from django.apps import apps
from django.db.models import Count, Avg, Max, Min, Sum


class Command(BaseCommand):
    """
    Command to analyze database performance.
    """
    
    help = 'Analyze database performance and identify optimization opportunities'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to analyze (format: app_label.model_name)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Limit the number of records to analyze per model'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed query information'
        )
    
    def handle(self, *args, **options):
        # Enable query logging
        original_debug = settings.DEBUG
        settings.DEBUG = True
        
        try:
            model_name = options.get('model')
            limit = options.get('limit')
            verbose = options.get('verbose')
            
            if model_name:
                app_label, model_name = model_name.split('.')
                model = apps.get_model(app_label, model_name)
                self.analyze_model(model, limit, verbose)
            else:
                self.analyze_all_models(limit, verbose)
            
            self.analyze_database_stats()
        finally:
            # Restore original debug setting
            settings.DEBUG = original_debug
    
    def analyze_model(self, model, limit, verbose):
        """Analyze a specific model."""
        self.stdout.write(self.style.NOTICE(f"\nAnalyzing model: {model._meta.label}"))
        
        # Get model statistics
        count = model.objects.count()
        self.stdout.write(f"Total records: {count}")
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No records to analyze"))
            return
        
        # Analyze query performance
        reset_queries()
        
        # Test basic queries
        self.stdout.write("\nBasic query performance:")
        
        # Test .all() query
        start_time = time.time()
        records = list(model.objects.all()[:limit])
        duration = time.time() - start_time
        query_count = len(connection.queries)
        
        self.stdout.write(f"  .all()[:limit] - Time: {duration:.4f}s, Queries: {query_count}")
        
        if verbose and query_count > 0:
            self.stdout.write("\n  Queries executed:")
            for i, query in enumerate(connection.queries[:5]):
                self.stdout.write(f"    {i+1}. {query['sql']}")
            
            if query_count > 5:
                self.stdout.write(f"    ... and {query_count - 5} more queries")
        
        reset_queries()
        
        # Test with select_related if the model has foreign keys
        foreign_keys = [f for f in model._meta.fields if f.is_relation and f.many_to_one]
        if foreign_keys:
            fk_names = [f.name for f in foreign_keys]
            self.stdout.write(f"\n  Foreign keys detected: {', '.join(fk_names)}")
            
            # Test with select_related
            start_time = time.time()
            records = list(model.objects.select_related(*fk_names)[:limit])
            duration = time.time() - start_time
            query_count = len(connection.queries)
            
            self.stdout.write(f"  .select_related() - Time: {duration:.4f}s, Queries: {query_count}")
            
            if verbose and query_count > 0:
                self.stdout.write("\n  Queries executed:")
                for i, query in enumerate(connection.queries[:5]):
                    self.stdout.write(f"    {i+1}. {query['sql']}")
        
        reset_queries()
        
        # Test with prefetch_related if the model has many-to-many or reverse relations
        m2m_fields = [f.name for f in model._meta.many_to_many]
        if m2m_fields:
            self.stdout.write(f"\n  Many-to-many fields detected: {', '.join(m2m_fields)}")
            
            # Test with prefetch_related
            start_time = time.time()
            records = list(model.objects.prefetch_related(*m2m_fields)[:limit])
            duration = time.time() - start_time
            query_count = len(connection.queries)
            
            self.stdout.write(f"  .prefetch_related() - Time: {duration:.4f}s, Queries: {query_count}")
            
            if verbose and query_count > 0:
                self.stdout.write("\n  Queries executed:")
                for i, query in enumerate(connection.queries[:5]):
                    self.stdout.write(f"    {i+1}. {query['sql']}")
        
        # Check for missing indexes
        self.check_missing_indexes(model)
    
    def analyze_all_models(self, limit, verbose):
        """Analyze all models in the project."""
        self.stdout.write(self.style.NOTICE("\nAnalyzing all models:"))
        
        # Get all models
        all_models = apps.get_models()
        
        for model in all_models:
            self.analyze_model(model, limit, verbose)
    
    def check_missing_indexes(self, model):
        """Check for potential missing indexes."""
        self.stdout.write("\nChecking for potential missing indexes:")
        
        # Check fields that might benefit from an index
        potential_index_fields = []
        
        # Check for fields used in filtering
        for field in model._meta.fields:
            if field.db_index or field.unique:
                continue  # Already indexed
            
            # Fields that often benefit from indexes
            if field.name.endswith('_id') or field.name in [
                'status', 'type', 'category', 'user_id', 'merchant_id',
                'transaction_id', 'created_at', 'updated_at', 'timestamp'
            ]:
                potential_index_fields.append(field.name)
        
        if potential_index_fields:
            self.stdout.write(self.style.WARNING(
                f"  Potential missing indexes: {', '.join(potential_index_fields)}"
            ))
            self.stdout.write("  Consider adding indexes to these fields if they are frequently used in queries.")
        else:
            self.stdout.write(self.style.SUCCESS("  No potential missing indexes detected."))
    
    def analyze_database_stats(self):
        """Analyze overall database statistics."""
        self.stdout.write(self.style.NOTICE("\nDatabase Statistics:"))
        
        # Get all models
        all_models = apps.get_models()
        
        # Collect statistics
        total_records = 0
        model_counts = []
        
        for model in all_models:
            count = model.objects.count()
            total_records += count
            model_counts.append((model._meta.label, count))
        
        # Sort by count (descending)
        model_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Display statistics
        self.stdout.write(f"Total records in database: {total_records}")
        self.stdout.write("\nTop 10 largest tables:")
        
        for i, (model_label, count) in enumerate(model_counts[:10]):
            self.stdout.write(f"  {i+1}. {model_label}: {count} records")
        
        # Analyze query patterns
        self.stdout.write("\nRecommendations:")
        
        if any(count > 10000 for _, count in model_counts):
            self.stdout.write(self.style.WARNING(
                "  - Some tables have a large number of records. Consider implementing pagination "
                "and optimizing queries that access these tables."
            ))
        
        if any(count > 100000 for _, count in model_counts):
            self.stdout.write(self.style.WARNING(
                "  - Very large tables detected. Consider implementing database partitioning "
                "or archiving old data to improve performance."
            ))
        
        self.stdout.write(self.style.SUCCESS(
            "  - Use Django Debug Toolbar to identify slow queries in your application."
        ))
        self.stdout.write(self.style.SUCCESS(
            "  - Consider adding caching for frequently accessed data."
        ))
        self.stdout.write(self.style.SUCCESS(
            "  - Use select_related() and prefetch_related() to reduce the number of database queries."
        ))