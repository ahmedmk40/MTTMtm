"""
Management command to analyze database performance.
"""

import time
import json
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings
from django.apps import apps


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
            '--output',
            type=str,
            help='Output file for results'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        model_name = options.get('model')
        limit = options.get('limit')
        output_file = options.get('output')
        verbose = options.get('verbose')
        
        # Enable query logging
        settings.DEBUG = True
        
        results = {}
        
        if model_name:
            app_label, model_name = model_name.split('.')
            model = apps.get_model(app_label, model_name)
            results[model._meta.label] = self.analyze_model(model, limit, verbose)
        else:
            self.stdout.write(self.style.NOTICE("Analyzing all models..."))
            
            for model in apps.get_models():
                if model._meta.app_label.startswith('django'):
                    continue  # Skip Django's internal models
                
                results[model._meta.label] = self.analyze_model(model, limit, verbose)
        
        # Print summary
        self.print_summary(results)
        
        # Save results to file if specified
        if output_file:
            self.save_results(results, output_file)
    
    def analyze_model(self, model, limit, verbose):
        """Analyze a specific model."""
        self.stdout.write(f"Analyzing {model._meta.label}...")
        
        # Get model statistics
        count = model.objects.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING(f"  No records found for {model._meta.label}"))
            return {
                'count': 0,
                'queries': [],
                'indexes': [],
                'recommendations': [],
            }
        
        # Analyze query performance
        queries = []
        
        # Test .all() query
        reset_queries()
        start_time = time.time()
        list(model.objects.all()[:limit])
        duration = time.time() - start_time
        query_count = len(connection.queries)
        
        queries.append({
            'name': 'all',
            'duration': duration,
            'query_count': query_count,
            'sql': connection.queries[0]['sql'] if query_count > 0 else None,
        })
        
        if verbose:
            self.stdout.write(f"  .all()[:limit] - Time: {duration:.4f}s, Queries: {query_count}")
        
        # Test with select_related if the model has foreign keys
        foreign_keys = [f for f in model._meta.fields if f.is_relation and f.many_to_one]
        if foreign_keys:
            fk_names = [f.name for f in foreign_keys]
            
            reset_queries()
            start_time = time.time()
            list(model.objects.select_related(*fk_names)[:limit])
            duration = time.time() - start_time
            query_count = len(connection.queries)
            
            queries.append({
                'name': 'select_related',
                'duration': duration,
                'query_count': query_count,
                'sql': connection.queries[0]['sql'] if query_count > 0 else None,
            })
            
            if verbose:
                self.stdout.write(f"  .select_related() - Time: {duration:.4f}s, Queries: {query_count}")
        
        # Test with prefetch_related if the model has many-to-many or reverse relations
        m2m_fields = [f.name for f in model._meta.many_to_many]
        if m2m_fields:
            reset_queries()
            start_time = time.time()
            list(model.objects.prefetch_related(*m2m_fields)[:limit])
            duration = time.time() - start_time
            query_count = len(connection.queries)
            
            queries.append({
                'name': 'prefetch_related',
                'duration': duration,
                'query_count': query_count,
                'sql': connection.queries[0]['sql'] if query_count > 0 else None,
            })
            
            if verbose:
                self.stdout.write(f"  .prefetch_related() - Time: {duration:.4f}s, Queries: {query_count}")
        
        # Check for missing indexes
        indexes = []
        for field in model._meta.fields:
            indexes.append({
                'field': field.name,
                'db_index': field.db_index,
                'unique': field.unique,
                'primary_key': field.primary_key,
                'is_relation': field.is_relation,
            })
        
        # Generate recommendations
        recommendations = self.generate_recommendations(model, queries, indexes, count)
        
        return {
            'count': count,
            'queries': queries,
            'indexes': indexes,
            'recommendations': recommendations,
        }
    
    def generate_recommendations(self, model, queries, indexes, count):
        """Generate recommendations for optimizing the model."""
        recommendations = []
        
        # Check for missing indexes on fields that might benefit from them
        indexed_fields = [idx['field'] for idx in indexes if idx['db_index'] or idx['unique'] or idx['primary_key']]
        
        for field in model._meta.fields:
            if field.name in indexed_fields:
                continue  # Already indexed
            
            # Fields that often benefit from indexes
            if field.name.endswith('_id') or field.name in [
                'status', 'type', 'category', 'user_id', 'merchant_id',
                'transaction_id', 'created_at', 'updated_at', 'timestamp'
            ]:
                recommendations.append({
                    'type': 'missing_index',
                    'field': field.name,
                    'message': f"Consider adding an index to the '{field.name}' field if it's frequently used in queries.",
                })
        
        # Check for large tables that might benefit from partitioning
        if count > 1000000:
            recommendations.append({
                'type': 'large_table',
                'count': count,
                'message': f"Table has {count} records. Consider implementing table partitioning for better performance.",
            })
        elif count > 100000:
            recommendations.append({
                'type': 'large_table',
                'count': count,
                'message': f"Table has {count} records. Consider adding appropriate indexes and optimizing queries.",
            })
        
        # Check for query performance
        if len(queries) >= 2:
            all_query = next((q for q in queries if q['name'] == 'all'), None)
            select_related_query = next((q for q in queries if q['name'] == 'select_related'), None)
            
            if all_query and select_related_query:
                if select_related_query['duration'] < all_query['duration'] * 0.8:
                    recommendations.append({
                        'type': 'query_optimization',
                        'message': f"Using select_related() improved query performance by {(1 - select_related_query['duration'] / all_query['duration']) * 100:.1f}%. Consider using it in your views.",
                    })
        
        return recommendations
    
    def print_summary(self, results):
        """Print a summary of the analysis results."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("DATABASE PERFORMANCE ANALYSIS SUMMARY"))
        self.stdout.write("=" * 50)
        
        # Count total records
        total_records = sum(result['count'] for result in results.values())
        self.stdout.write(f"\nTotal records in database: {total_records}")
        
        # Show top 5 largest tables
        self.stdout.write("\nTop 5 largest tables:")
        sorted_models = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
        for i, (model_label, result) in enumerate(sorted_models[:5]):
            self.stdout.write(f"  {i+1}. {model_label}: {result['count']} records")
        
        # Show recommendations
        self.stdout.write("\nRecommendations:")
        
        for model_label, result in sorted_models:
            if result['recommendations']:
                self.stdout.write(f"\n{model_label}:")
                for recommendation in result['recommendations']:
                    message = recommendation['message']
                    
                    if recommendation['type'] == 'missing_index':
                        self.stdout.write(self.style.WARNING(f"  - {message}"))
                    elif recommendation['type'] == 'large_table':
                        self.stdout.write(self.style.ERROR(f"  - {message}"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"  - {message}"))
        
        self.stdout.write("\n" + "=" * 50)
    
    def save_results(self, results, output_file):
        """Save the analysis results to a file."""
        from django.utils import timezone
        
        # Add timestamp to results
        data = {
            'timestamp': timezone.now().isoformat(),
            'results': results,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Results saved to {output_file}"))