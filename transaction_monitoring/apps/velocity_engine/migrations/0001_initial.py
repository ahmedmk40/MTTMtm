# Generated by Django 5.1.7 on 2025-03-17 18:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VelocityCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('entity_type', models.CharField(max_length=20, verbose_name='Entity Type')),
                ('entity_value', models.CharField(max_length=255, verbose_name='Entity Value')),
                ('count_5m', models.IntegerField(default=0, verbose_name='Count (5 min)')),
                ('count_15m', models.IntegerField(default=0, verbose_name='Count (15 min)')),
                ('count_1h', models.IntegerField(default=0, verbose_name='Count (1 hour)')),
                ('count_6h', models.IntegerField(default=0, verbose_name='Count (6 hours)')),
                ('count_24h', models.IntegerField(default=0, verbose_name='Count (24 hours)')),
                ('count_7d', models.IntegerField(default=0, verbose_name='Count (7 days)')),
                ('count_30d', models.IntegerField(default=0, verbose_name='Count (30 days)')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
            ],
            options={
                'verbose_name': 'Velocity Counter',
                'verbose_name_plural': 'Velocity Counters',
                'indexes': [models.Index(fields=['entity_type', 'entity_value'], name='velocity_en_entity__8de708_idx'), models.Index(fields=['last_updated'], name='velocity_en_last_up_7fd264_idx')],
                'unique_together': {('entity_type', 'entity_value')},
            },
        ),
        migrations.CreateModel(
            name='VelocityRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('name', models.CharField(max_length=100, verbose_name='Rule Name')),
                ('description', models.TextField(verbose_name='Description')),
                ('entity_type', models.CharField(choices=[('user_id', 'User ID'), ('card_number', 'Card Number'), ('device_id', 'Device ID'), ('ip_address', 'IP Address'), ('merchant_id', 'Merchant ID'), ('email', 'Email')], max_length=20, verbose_name='Entity Type')),
                ('time_window', models.IntegerField(choices=[(300, '5 Minutes'), (900, '15 Minutes'), (3600, '1 Hour'), (21600, '6 Hours'), (86400, '24 Hours'), (604800, '7 Days'), (2592000, '30 Days')], verbose_name='Time Window (seconds)')),
                ('threshold', models.IntegerField(verbose_name='Threshold')),
                ('action', models.CharField(choices=[('approve', 'Approve'), ('reject', 'Reject'), ('review', 'Flag for Review'), ('notify', 'Notify Only')], max_length=20, verbose_name='Action')),
                ('risk_score', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Risk Score')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('applies_to_pos', models.BooleanField(default=True, verbose_name='Applies to POS')),
                ('applies_to_ecommerce', models.BooleanField(default=True, verbose_name='Applies to E-commerce')),
                ('applies_to_wallet', models.BooleanField(default=True, verbose_name='Applies to Wallet')),
                ('min_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Min Amount')),
                ('max_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Max Amount')),
                ('hit_count', models.IntegerField(default=0, verbose_name='Hit Count')),
                ('false_positive_count', models.IntegerField(default=0, verbose_name='False Positive Count')),
                ('last_triggered', models.DateTimeField(blank=True, null=True, verbose_name='Last Triggered')),
            ],
            options={
                'verbose_name': 'Velocity Rule',
                'verbose_name_plural': 'Velocity Rules',
                'ordering': ['entity_type', 'time_window'],
                'indexes': [models.Index(fields=['entity_type'], name='velocity_en_entity__f2c242_idx'), models.Index(fields=['is_active'], name='velocity_en_is_acti_0ee28c_idx')],
            },
        ),
        migrations.CreateModel(
            name='VelocityAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('transaction_id', models.CharField(max_length=100, verbose_name='Transaction ID')),
                ('entity_type', models.CharField(max_length=20, verbose_name='Entity Type')),
                ('entity_value', models.CharField(max_length=255, verbose_name='Entity Value')),
                ('count', models.IntegerField(verbose_name='Count')),
                ('threshold', models.IntegerField(verbose_name='Threshold')),
                ('time_window', models.IntegerField(verbose_name='Time Window (seconds)')),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='velocity_engine.velocityrule')),
            ],
            options={
                'verbose_name': 'Velocity Alert',
                'verbose_name_plural': 'Velocity Alerts',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['transaction_id'], name='velocity_en_transac_8136b7_idx'), models.Index(fields=['entity_type', 'entity_value'], name='velocity_en_entity__00fd8e_idx'), models.Index(fields=['created_at'], name='velocity_en_created_8be6f9_idx')],
            },
        ),
    ]
