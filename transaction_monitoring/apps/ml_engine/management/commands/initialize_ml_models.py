"""
Management command to initialize ML models.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.ml_engine.models import MLModel
from apps.ml_engine.ml_models.classification_model import save_dummy_model
from apps.ml_engine.ml_models.behavioral_model import save_dummy_behavioral_model
from apps.ml_engine.ml_models.network_model import save_dummy_network_model
from apps.ml_engine.ml_models.velocity_model import save_dummy_velocity_model


class Command(BaseCommand):
    """
    Command to initialize ML models.
    """
    
    help = 'Initialize ML models'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Initializing ML models...'))
        
        # Save dummy classification model
        self.stdout.write('Creating dummy classification model...')
        file_path = save_dummy_model(settings.BASE_DIR)
        
        # Create MLModel entry for classification model
        model, created = MLModel.objects.get_or_create(
            name='Fraud Classification',
            version='1.0',
            defaults={
                'description': 'Random Forest classifier for fraud detection',
                'model_type': 'classification',
                'file_path': file_path,
                'is_active': True,
                'accuracy': 0.95,
                'precision': 0.92,
                'recall': 0.88,
                'f1_score': 0.90,
                'auc_roc': 0.96,
                'training_date': timezone.now(),
                'training_data_size': 10000,
                'training_parameters': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42
                },
                'feature_importance': {
                    'amount': 0.25,
                    'is_new_card': 0.15,
                    'is_high_risk_country': 0.12,
                    'is_night': 0.10,
                    'is_suspicious_mcc': 0.08
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created model: {model.name} v{model.version}'))
        else:
            self.stdout.write(f'Model already exists: {model.name} v{model.version}')
        
        # Save dummy behavioral model
        self.stdout.write('Creating dummy behavioral model...')
        behavioral_file_path = save_dummy_behavioral_model(settings.BASE_DIR)
        
        # Create MLModel entry for behavioral model
        behavioral_model, created = MLModel.objects.get_or_create(
            name='Behavioral Analysis',
            version='1.0',
            defaults={
                'description': 'Isolation Forest model for behavioral anomaly detection',
                'model_type': 'behavioral',
                'file_path': behavioral_file_path,
                'is_active': True,
                'precision': 0.88,
                'recall': 0.82,
                'f1_score': 0.85,
                'training_date': timezone.now(),
                'training_data_size': 10000,
                'training_parameters': {
                    'n_estimators': 100,
                    'contamination': 0.05,
                    'random_state': 42
                },
                'feature_importance': {
                    'transaction_count_1d': 0.20,
                    'velocity_amount_1d': 0.18,
                    'distinct_countries_30d': 0.15,
                    'device_count_30d': 0.12,
                    'failed_attempts_24h': 0.10,
                    'time_since_last_transaction': 0.08,
                    'avg_amount_1d': 0.07,
                    'location_count_30d': 0.05,
                    'distinct_merchants_7d': 0.05
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created model: {behavioral_model.name} v{behavioral_model.version}'))
        else:
            self.stdout.write(f'Model already exists: {behavioral_model.name} v{behavioral_model.version}')
        
        # Save dummy network model
        self.stdout.write('Creating dummy network model...')
        network_file_path = save_dummy_network_model(settings.BASE_DIR)
        
        # Create MLModel entry for network model
        network_model, created = MLModel.objects.get_or_create(
            name='Network Analysis',
            version='1.0',
            defaults={
                'description': 'Random Forest model for network pattern analysis',
                'model_type': 'network',
                'file_path': network_file_path,
                'is_active': True,
                'precision': 0.90,
                'recall': 0.85,
                'f1_score': 0.87,
                'training_date': timezone.now(),
                'training_data_size': 5000,
                'training_parameters': {
                    'n_estimators': 100,
                    'max_depth': 8,
                    'random_state': 42
                },
                'feature_importance': {
                    'user_weighted_degree': 0.22,
                    'merchant_weighted_degree': 0.18,
                    'user_avg_transaction': 0.15,
                    'merchant_avg_transaction': 0.12,
                    'amount': 0.10,
                    'user_degree': 0.08,
                    'merchant_degree': 0.08,
                    'channel_ecommerce': 0.07
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created model: {network_model.name} v{network_model.version}'))
        else:
            self.stdout.write(f'Model already exists: {network_model.name} v{network_model.version}')
        
        # Save dummy velocity model
        self.stdout.write('Creating dummy velocity model...')
        velocity_file_path = save_dummy_velocity_model(settings.BASE_DIR)
        
        # Create MLModel entry for velocity model
        velocity_model, created = MLModel.objects.get_or_create(
            name='Velocity Anomaly Detection',
            version='1.0',
            defaults={
                'description': 'Isolation Forest model for velocity-based anomaly detection',
                'model_type': 'anomaly',
                'file_path': velocity_file_path,
                'is_active': True,
                'precision': 0.85,
                'recall': 0.80,
                'f1_score': 0.82,
                'training_date': timezone.now(),
                'training_data_size': 5000,
                'training_parameters': {
                    'n_estimators': 100,
                    'contamination': 0.05,
                    'random_state': 42
                },
                'feature_importance': {
                    'tx_count_1min': 0.25,
                    'tx_count_5min': 0.20,
                    'amount_1min': 0.18,
                    'amount_5min': 0.15,
                    'merchant_count_1hour': 0.12,
                    'location_count_1hour': 0.10,
                    'device_count_1hour': 0.08,
                    'ip_count_1hour': 0.07,
                    'failed_tx_count_1hour': 0.05
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created model: {velocity_model.name} v{velocity_model.version}'))
        else:
            self.stdout.write(f'Model already exists: {velocity_model.name} v{velocity_model.version}')
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized ML models'))