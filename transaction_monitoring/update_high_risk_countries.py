import os
import django
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.transactions.models import Transaction

# High risk countries
high_risk_countries = ['AF', 'KP', 'IR', 'SY', 'VE', 'RU', 'BY', 'CU', 'SD', 'MM']

# Get all transactions with high risk countries
transactions = Transaction.objects.filter(country_code__in=high_risk_countries)
print(f"Found {transactions.count()} transactions with high risk countries")

# Update is_high_risk_country flag
for tx in transactions:
    tx.is_high_risk_country = True
    tx.save()

print("Done updating high risk country flags!")

# Let's also create some transactions with high decline rates for specific countries
# to make the country analysis more interesting
countries_to_update = ['RU', 'VE', 'IR', 'AF', 'KP']
response_codes = ['05', '14', '51', '41', '43', '55', '57', '61', '91', '96']

for country in countries_to_update:
    # Get transactions for this country
    country_txs = Transaction.objects.filter(country_code=country)
    print(f"Found {country_txs.count()} transactions for {country}")
    
    # Update at least 70% of them to have decline response codes
    update_count = int(country_txs.count() * 0.7)
    for tx in country_txs[:update_count]:
        tx.response_code = random.choice(response_codes)
        tx.status = 'rejected'
        tx.save()
    
    print(f"Updated {update_count} transactions for {country} with decline codes")

print("Done creating high decline rates for specific countries!")