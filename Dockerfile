FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create log directory
RUN mkdir -p /var/log/transaction_monitoring

# Collect static files
RUN python transaction_monitoring/manage.py collectstatic --noinput

# Run gunicorn
CMD gunicorn --chdir transaction_monitoring config.wsgi:application --bind 0.0.0.0:$PORT