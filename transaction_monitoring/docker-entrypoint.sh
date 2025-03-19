#!/bin/bash

set -e

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done
  echo "PostgreSQL started"
}

# Function to wait for Redis to be ready
wait_for_redis() {
  echo "Waiting for Redis..."
  REDIS_HOST=$(echo $REDIS_URL | cut -d/ -f3 | cut -d: -f1)
  REDIS_PORT=$(echo $REDIS_URL | cut -d/ -f3 | cut -d: -f2)
  while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.1
  done
  echo "Redis started"
}

# Wait for services to be ready
if [ "$DB_HOST" != "localhost" ]; then
  wait_for_postgres
fi

if [ "$REDIS_URL" != "redis://localhost:6379/0" ]; then
  wait_for_redis
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser --noinput
fi

# Initialize rules if needed
if [ "$INITIALIZE_RULES" = "true" ]; then
  echo "Initializing rules..."
  python manage.py initialize_rules
fi

# Initialize ML models if needed
if [ "$INITIALIZE_ML_MODELS" = "true" ]; then
  echo "Initializing ML models..."
  python manage.py initialize_ml_models
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers $GUNICORN_WORKERS \
  --worker-class $GUNICORN_WORKER_CLASS \
  --timeout $GUNICORN_TIMEOUT \
  --access-logfile - \
  --error-logfile - \
  --log-level info