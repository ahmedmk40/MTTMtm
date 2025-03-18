#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Database is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Initialize system
echo "Initializing system..."
python manage.py initialize_rules
python manage.py initialize_velocity_rules
python manage.py initialize_ml_models

# Start server
echo "Starting server..."
exec "$@"