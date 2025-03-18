#!/bin/bash

# Start Celery worker
celery -A transaction_monitoring worker --loglevel=info