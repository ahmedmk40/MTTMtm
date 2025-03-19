import os
import django
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.transactions.models import Transaction

# List of country codes to use
country_codes = [
    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'CN', 'BR', 'MX',
    'IN', 'RU', 'ZA', 'NG', 'EG', 'SA', 'AE', 'SG', 'KR', 'IT',
    'ES', 'NL', 'SE', 'CH', 'AT', 'BE', 'DK', 'FI', 'NO', 'IE',
    'NZ', 'AR', 'CL', 'CO', 'PE', 'VE', 'MY', 'TH', 'ID', 'PH',
    'VN', 'TR', 'IL', 'GR', 'PT', 'PL', 'CZ', 'HU', 'RO', 'UA'
]

# High risk countries
high_risk_countries = ['AF', 'KP', 'IR', 'SY', 'VE', 'RU', 'BY', 'CU', 'SD', 'MM']

# Add some high risk countries to the mix
country_codes.extend(high_risk_countries)

# Update transactions with random country codes
transactions = Transaction.objects.all()
print(f"Updating {transactions.count()} transactions with country codes...")

for tx in transactions:
    country = random.choice(country_codes)
    tx.country_code = country
    tx.is_high_risk_country = country in high_risk_countries
    tx.save()

print("Done updating country codes!")