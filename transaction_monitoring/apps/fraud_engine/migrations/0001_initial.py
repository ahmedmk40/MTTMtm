# Generated by Django 5.1.7 on 2025-03-17 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlockList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('entity_type', models.CharField(choices=[('user_id', 'User ID'), ('card_number', 'Card Number'), ('device_id', 'Device ID'), ('ip_address', 'IP Address'), ('merchant_id', 'Merchant ID'), ('email', 'Email')], max_length=20, verbose_name='Entity Type')),
                ('entity_value', models.CharField(max_length=255, verbose_name='Entity Value')),
                ('reason', models.TextField(verbose_name='Reason')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expires At')),
                ('added_by', models.CharField(max_length=100, verbose_name='Added By')),
            ],
            options={
                'verbose_name': 'Block List Entry',
                'verbose_name_plural': 'Block List Entries',
                'indexes': [models.Index(fields=['entity_type', 'entity_value'], name='fraud_engin_entity__c60955_idx'), models.Index(fields=['is_active'], name='fraud_engin_is_acti_ac10bf_idx')],
                'unique_together': {('entity_type', 'entity_value')},
            },
        ),
        migrations.CreateModel(
            name='FraudCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('case_id', models.CharField(max_length=50, unique=True, verbose_name='Case ID')),
                ('user_id', models.CharField(max_length=100, verbose_name='User ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description')),
                ('status', models.CharField(choices=[('open', 'Open'), ('investigating', 'Investigating'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='open', max_length=20, verbose_name='Status')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20, verbose_name='Priority')),
                ('assigned_to', models.CharField(blank=True, max_length=100, null=True, verbose_name='Assigned To')),
                ('related_transactions', models.JSONField(default=list, verbose_name='Related Transactions')),
                ('resolution_notes', models.TextField(blank=True, null=True, verbose_name='Resolution Notes')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Resolved At')),
                ('resolved_by', models.CharField(blank=True, max_length=100, null=True, verbose_name='Resolved By')),
            ],
            options={
                'verbose_name': 'Fraud Case',
                'verbose_name_plural': 'Fraud Cases',
                'indexes': [models.Index(fields=['case_id'], name='fraud_engin_case_id_c024e2_idx'), models.Index(fields=['user_id'], name='fraud_engin_user_id_0e7570_idx'), models.Index(fields=['status'], name='fraud_engin_status_b159d2_idx'), models.Index(fields=['priority'], name='fraud_engin_priorit_3836fb_idx'), models.Index(fields=['assigned_to'], name='fraud_engin_assigne_0c8495_idx')],
            },
        ),
        migrations.CreateModel(
            name='FraudDetectionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('transaction_id', models.CharField(max_length=100, unique=True, verbose_name='Transaction ID')),
                ('risk_score', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Risk Score')),
                ('is_fraudulent', models.BooleanField(default=False, verbose_name='Is Fraudulent')),
                ('decision', models.CharField(choices=[('approve', 'Approve'), ('reject', 'Reject'), ('review', 'Review')], max_length=20, verbose_name='Decision')),
                ('processing_time', models.FloatField(verbose_name='Processing Time (ms)')),
                ('block_check_result', models.JSONField(default=dict, verbose_name='Block Check Result')),
                ('rule_engine_result', models.JSONField(default=dict, verbose_name='Rule Engine Result')),
                ('velocity_engine_result', models.JSONField(default=dict, verbose_name='Velocity Engine Result')),
                ('ml_engine_result', models.JSONField(default=dict, verbose_name='ML Engine Result')),
                ('aml_engine_result', models.JSONField(default=dict, verbose_name='AML Engine Result')),
                ('triggered_rules', models.JSONField(default=list, verbose_name='Triggered Rules')),
            ],
            options={
                'verbose_name': 'Fraud Detection Result',
                'verbose_name_plural': 'Fraud Detection Results',
                'indexes': [models.Index(fields=['transaction_id'], name='fraud_engin_transac_5fdc19_idx'), models.Index(fields=['is_fraudulent'], name='fraud_engin_is_frau_3ada51_idx'), models.Index(fields=['decision'], name='fraud_engin_decisio_8b6bf4_idx'), models.Index(fields=['created_at'], name='fraud_engin_created_45c9e7_idx')],
            },
        ),
    ]
