import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Database tables:")
    for table in sorted(tables):
        print(f"- {table[0]}")
        
    # Check if velocity_engine_velocityrule table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='velocity_engine_velocityrule';")
    velocity_rule_table = cursor.fetchone()
    
    if velocity_rule_table:
        print("\nvelocity_engine_velocityrule table exists.")
    else:
        print("\nvelocity_engine_velocityrule table does NOT exist.")