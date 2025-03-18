#!/bin/bash

# Start Redis in the background
echo "Starting Redis..."
./start_redis.sh > redis.log 2>&1 &
REDIS_PID=$!

# Wait for Redis to start
sleep 2

# Start Celery worker in the background
echo "Starting Celery worker..."
./start_celery.sh > celery.log 2>&1 &
CELERY_PID=$!

# Wait for Celery to start
sleep 2

# Start Django server
echo "Starting Django server..."
./start_django.sh

# When Django server is stopped, kill Redis and Celery
echo "Stopping Redis and Celery..."
kill $REDIS_PID
kill $CELERY_PID