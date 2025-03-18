"""
Management command to run performance tests on the application.
"""

import time
import json
import statistics
from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection, reset_queries
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    """
    Command to run performance tests on the application.
    """
    
    help = 'Run performance tests on the application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of iterations to run each test'
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
        iterations = options['iterations']
        output_file = options.get('output')
        verbose = options.get('verbose')
        
        self.stdout.write(self.style.NOTICE(f"Running performance tests with {iterations} iterations"))
        
        # Enable query logging
        settings.DEBUG = True
        
        # Create a test user if needed
        user = self.get_or_create_test_user()
        
        # Run the performance tests
        results = self.run_performance_tests(user, iterations, verbose)
        
        # Print results
        self.print_results(results)
        
        # Save results to file if specified
        if output_file:
            self.save_results(results, output_file)
    
    def get_or_create_test_user(self):
        """Get or create a test user for performance testing."""
        username = 'performance_test_user'
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='performance@example.com',
                password='testpassword123',
                first_name='Performance',
                last_name='Test',
                role='compliance_officer'
            )
        
        return user
    
    def run_performance_tests(self, user, iterations, verbose):
        """Run performance tests on various endpoints."""
        client = Client()
        client.force_login(user)
        
        # Define test cases
        test_cases = [
            {
                'name': 'Dashboard',
                'url': reverse('dashboard:index'),
                'method': 'GET',
                'data': None,
            },
            {
                'name': 'Transaction List',
                'url': reverse('transactions:list'),
                'method': 'GET',
                'data': None,
            },
            {
                'name': 'Notification List',
                'url': reverse('notifications:list'),
                'method': 'GET',
                'data': None,
            },
            {
                'name': 'Report List',
                'url': reverse('reporting:list'),
                'method': 'GET',
                'data': None,
            },
            {
                'name': 'API Health Check',
                'url': reverse('api:health_check'),
                'method': 'GET',
                'data': None,
            },
        ]
        
        results = {}
        
        for test_case in test_cases:
            self.stdout.write(f"Testing {test_case['name']}...")
            
            test_results = self.run_test_case(client, test_case, iterations, verbose)
            results[test_case['name']] = test_results
        
        return results
    
    def run_test_case(self, client, test_case, iterations, verbose):
        """Run a single test case multiple times and collect metrics."""
        name = test_case['name']
        url = test_case['url']
        method = test_case['method']
        data = test_case['data']
        
        response_times = []
        query_counts = []
        status_codes = []
        
        for i in range(iterations):
            # Reset query log
            reset_queries()
            
            # Make the request and measure time
            start_time = time.time()
            
            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url, data=data or {})
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Collect metrics
            response_times.append(response_time)
            query_counts.append(len(connection.queries))
            status_codes.append(response.status_code)
            
            if verbose:
                self.stdout.write(f"  Iteration {i+1}: {response_time:.2f} ms, {len(connection.queries)} queries, status {response.status_code}")
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        median_response_time = statistics.median(response_times)
        
        avg_query_count = statistics.mean(query_counts)
        min_query_count = min(query_counts)
        max_query_count = max(query_counts)
        
        # Get slow queries
        slow_queries = []
        for query in connection.queries:
            query_time = float(query.get('time', 0))
            if query_time > 0.1:  # Queries taking more than 100ms
                slow_queries.append({
                    'sql': query.get('sql', ''),
                    'time': query_time,
                })
        
        return {
            'response_times': {
                'avg': avg_response_time,
                'min': min_response_time,
                'max': max_response_time,
                'median': median_response_time,
                'all': response_times,
            },
            'query_counts': {
                'avg': avg_query_count,
                'min': min_query_count,
                'max': max_query_count,
                'all': query_counts,
            },
            'status_codes': status_codes,
            'slow_queries': slow_queries,
        }
    
    def print_results(self, results):
        """Print the performance test results."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("PERFORMANCE TEST RESULTS"))
        self.stdout.write("=" * 50)
        
        for name, result in results.items():
            self.stdout.write(f"\n{name}:")
            
            self.stdout.write("  Response Time:")
            self.stdout.write(f"    Average: {result['response_times']['avg']:.2f} ms")
            self.stdout.write(f"    Minimum: {result['response_times']['min']:.2f} ms")
            self.stdout.write(f"    Maximum: {result['response_times']['max']:.2f} ms")
            self.stdout.write(f"    Median: {result['response_times']['median']:.2f} ms")
            
            self.stdout.write("  Query Count:")
            self.stdout.write(f"    Average: {result['query_counts']['avg']:.2f}")
            self.stdout.write(f"    Minimum: {result['query_counts']['min']}")
            self.stdout.write(f"    Maximum: {result['query_counts']['max']}")
            
            if result['slow_queries']:
                self.stdout.write("  Slow Queries:")
                for i, query in enumerate(result['slow_queries'][:5]):  # Show only first 5 slow queries
                    self.stdout.write(f"    {i+1}. {query['time']:.2f}s: {query['sql'][:100]}...")
                
                if len(result['slow_queries']) > 5:
                    self.stdout.write(f"    ... and {len(result['slow_queries']) - 5} more slow queries")
        
        self.stdout.write("\n" + "=" * 50)
    
    def save_results(self, results, output_file):
        """Save the performance test results to a file."""
        from django.utils import timezone
        
        # Add timestamp to results
        data = {
            'timestamp': timezone.now().isoformat(),
            'results': results,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Results saved to {output_file}"))