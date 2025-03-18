FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings.development

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run migrations
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]