# Generated by Django 5.1.7 on 2025-03-17 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AMLAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('alert_id', models.CharField(max_length=50, unique=True, verbose_name='Alert ID')),
                ('user_id', models.CharField(max_length=100, verbose_name='User ID')),
                ('alert_type', models.CharField(choices=[('structuring', 'Structuring'), ('rapid_movement', 'Rapid Movement'), ('high_risk_jurisdiction', 'High Risk Jurisdiction'), ('round_amount', 'Round Amount'), ('multiple_transfers', 'Multiple Transfers'), ('circular_flow', 'Circular Flow'), ('party_connection', 'Party Connection'), ('other', 'Other')], max_length=30, verbose_name='Alert Type')),
                ('description', models.TextField(verbose_name='Description')),
                ('status', models.CharField(choices=[('open', 'Open'), ('investigating', 'Investigating'), ('closed_false_positive', 'Closed - False Positive'), ('closed_sar_filed', 'Closed - SAR Filed'), ('closed_other', 'Closed - Other')], default='open', max_length=30, verbose_name='Status')),
                ('risk_score', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Risk Score')),
                ('related_transactions', models.JSONField(default=list, verbose_name='Related Transactions')),
                ('related_entities', models.JSONField(default=list, verbose_name='Related Entities')),
                ('detection_data', models.JSONField(default=dict, verbose_name='Detection Data')),
                ('assigned_to', models.CharField(blank=True, max_length=100, null=True, verbose_name='Assigned To')),
                ('investigation_notes', models.TextField(blank=True, verbose_name='Investigation Notes')),
                ('resolution_notes', models.TextField(blank=True, verbose_name='Resolution Notes')),
                ('closed_at', models.DateTimeField(blank=True, null=True, verbose_name='Closed At')),
                ('closed_by', models.CharField(blank=True, max_length=100, null=True, verbose_name='Closed By')),
            ],
            options={
                'verbose_name': 'AML Alert',
                'verbose_name_plural': 'AML Alerts',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['alert_id'], name='aml_amlaler_alert_i_1ba7e2_idx'), models.Index(fields=['user_id'], name='aml_amlaler_user_id_271c56_idx'), models.Index(fields=['alert_type'], name='aml_amlaler_alert_t_d745bb_idx'), models.Index(fields=['status'], name='aml_amlaler_status_bc61c4_idx'), models.Index(fields=['created_at'], name='aml_amlaler_created_564c94_idx')],
            },
        ),
        migrations.CreateModel(
            name='AMLRiskProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('user_id', models.CharField(max_length=100, unique=True, verbose_name='User ID')),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', max_length=20, verbose_name='Risk Level')),
                ('risk_score', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Risk Score')),
                ('last_assessment', models.DateTimeField(auto_now=True, verbose_name='Last Assessment')),
                ('transaction_volume', models.DecimalField(decimal_places=2, default=0.0, max_digits=15, verbose_name='Transaction Volume')),
                ('transaction_count', models.IntegerField(default=0, verbose_name='Transaction Count')),
                ('high_risk_transactions', models.IntegerField(default=0, verbose_name='High Risk Transactions')),
                ('suspicious_patterns', models.IntegerField(default=0, verbose_name='Suspicious Patterns')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('risk_factors', models.JSONField(default=list, verbose_name='Risk Factors')),
            ],
            options={
                'verbose_name': 'AML Risk Profile',
                'verbose_name_plural': 'AML Risk Profiles',
                'indexes': [models.Index(fields=['user_id'], name='aml_amlrisk_user_id_30e9c0_idx'), models.Index(fields=['risk_level'], name='aml_amlrisk_risk_le_4287f9_idx'), models.Index(fields=['last_assessment'], name='aml_amlrisk_last_as_fdfa17_idx')],
            },
        ),
        migrations.CreateModel(
            name='SuspiciousActivityReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('sar_id', models.CharField(max_length=50, unique=True, verbose_name='SAR ID')),
                ('user_id', models.CharField(max_length=100, verbose_name='User ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending_approval', 'Pending Approval'), ('approved', 'Approved'), ('filed', 'Filed'), ('rejected', 'Rejected')], default='draft', max_length=20, verbose_name='Status')),
                ('related_alerts', models.JSONField(default=list, verbose_name='Related Alerts')),
                ('related_transactions', models.JSONField(default=list, verbose_name='Related Transactions')),
                ('supporting_evidence', models.JSONField(default=list, verbose_name='Supporting Evidence')),
                ('prepared_by', models.CharField(max_length=100, verbose_name='Prepared By')),
                ('approved_by', models.CharField(blank=True, max_length=100, null=True, verbose_name='Approved By')),
                ('filed_by', models.CharField(blank=True, max_length=100, null=True, verbose_name='Filed By')),
                ('filed_at', models.DateTimeField(blank=True, null=True, verbose_name='Filed At')),
                ('filing_reference', models.CharField(blank=True, max_length=100, null=True, verbose_name='Filing Reference')),
            ],
            options={
                'verbose_name': 'Suspicious Activity Report',
                'verbose_name_plural': 'Suspicious Activity Reports',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['sar_id'], name='aml_suspici_sar_id_5aa7a9_idx'), models.Index(fields=['user_id'], name='aml_suspici_user_id_30ebc6_idx'), models.Index(fields=['status'], name='aml_suspici_status_1cb3f9_idx'), models.Index(fields=['created_at'], name='aml_suspici_created_8e9fd8_idx')],
            },
        ),
        migrations.CreateModel(
            name='TransactionPattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('user_id', models.CharField(max_length=100, verbose_name='User ID')),
                ('pattern_type', models.CharField(choices=[('structuring', 'Structuring'), ('round_amount', 'Round Amount'), ('rapid_movement', 'Rapid Movement'), ('circular_flow', 'Circular Flow'), ('cross_border', 'Cross Border'), ('high_risk_mcc', 'High Risk MCC'), ('other', 'Other')], max_length=30, verbose_name='Pattern Type')),
                ('pattern_data', models.JSONField(default=dict, verbose_name='Pattern Data')),
                ('first_detected', models.DateTimeField(auto_now_add=True, verbose_name='First Detected')),
                ('last_detected', models.DateTimeField(auto_now=True, verbose_name='Last Detected')),
                ('occurrence_count', models.IntegerField(default=1, verbose_name='Occurrence Count')),
                ('risk_score', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Risk Score')),
                ('is_suspicious', models.BooleanField(default=False, verbose_name='Is Suspicious')),
            ],
            options={
                'verbose_name': 'Transaction Pattern',
                'verbose_name_plural': 'Transaction Patterns',
                'ordering': ['-last_detected'],
                'indexes': [models.Index(fields=['user_id'], name='aml_transac_user_id_6e208e_idx'), models.Index(fields=['pattern_type'], name='aml_transac_pattern_842e62_idx'), models.Index(fields=['is_suspicious'], name='aml_transac_is_susp_17b878_idx'), models.Index(fields=['last_detected'], name='aml_transac_last_de_5a0929_idx')],
            },
        ),
    ]
