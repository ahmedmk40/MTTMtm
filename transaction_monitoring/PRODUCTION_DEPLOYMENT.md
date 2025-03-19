# Production Deployment Guide

This guide provides instructions for deploying the Transaction Monitoring System in a production environment using Docker and Docker Compose.

## Prerequisites

- Ubuntu Server 20.04 LTS or newer
- Docker Engine (version 20.10 or newer)
- Docker Compose (version 2.0 or newer)
- Domain name (optional, but recommended for production)

## Installation Steps

### 1. Install Docker and Docker Compose

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
sudo apt-get update

# Install Docker Engine
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to the docker group to run Docker without sudo
sudo usermod -aG docker $USER
```

Log out and log back in for the group changes to take effect.

### 2. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/transaction-monitoring.git
cd transaction-monitoring
```

### 3. Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file with your production settings
nano .env
```

Make sure to update the following variables:
- `SECRET_KEY`: Use a strong, random string
- `ALLOWED_HOSTS`: Add your domain name
- `DB_PASSWORD`: Use a strong password
- `EMAIL_*`: Configure your email settings
- `DJANGO_SUPERUSER_*`: Set secure credentials for the admin user

### 4. SSL Certificates

For production, you should use proper SSL certificates. You can use Let's Encrypt to get free certificates:

```bash
# Install certbot
sudo apt-get install -y certbot

# Get certificates (replace example.com with your domain)
sudo certbot certonly --standalone -d example.com -d www.example.com

# Create the SSL directory
mkdir -p nginx/ssl

# Copy the certificates
sudo cp /etc/letsencrypt/live/example.com/fullchain.pem nginx/ssl/server.crt
sudo cp /etc/letsencrypt/live/example.com/privkey.pem nginx/ssl/server.key

# Set proper permissions
sudo chmod 644 nginx/ssl/server.crt
sudo chmod 600 nginx/ssl/server.key
```

Alternatively, for testing or internal deployments, you can generate self-signed certificates:

```bash
# Run the certificate generation script
./nginx/generate-ssl-certs.sh
```

### 5. Update Nginx Configuration

Edit the Nginx configuration file to use your domain name:

```bash
# Edit the Nginx configuration
nano nginx/conf.d/default.conf
```

Replace `server_name localhost;` with `server_name your-domain.com www.your-domain.com;`.

### 6. Build and Start the Services

```bash
# Build and start all services in detached mode
docker-compose up -d
```

### 7. Monitor the Deployment

```bash
# Check the status of all containers
docker-compose ps

# View logs from all services
docker-compose logs

# View logs from a specific service
docker-compose logs web
```

### 8. Backup Strategy

Set up regular backups of your database:

```bash
# Create a backup script
cat > backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/path/to/backups"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
docker-compose exec -T db pg_dump -U postgres transaction_monitoring > $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz -C /path/to/transaction-monitoring/media .

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql" -type f -mtime +30 -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -type f -mtime +30 -delete
EOF

# Make the script executable
chmod +x backup.sh

# Add to crontab to run daily at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/transaction-monitoring/backup.sh") | crontab -
```

### 9. Updating the Application

To update the application with new code:

```bash
# Pull the latest changes
git pull

# Rebuild and restart the services
docker-compose down
docker-compose build
docker-compose up -d

# Apply any new migrations
docker-compose exec web python manage.py migrate
```

## Troubleshooting

### Database Connection Issues

If the web service can't connect to the database:

```bash
# Check if the database container is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Try to connect to the database manually
docker-compose exec db psql -U postgres -d transaction_monitoring
```

### Nginx Configuration Issues

If Nginx is not serving the application correctly:

```bash
# Check Nginx logs
docker-compose logs nginx

# Verify Nginx configuration
docker-compose exec nginx nginx -t
```

### Static Files Not Loading

If static files are not being served correctly:

```bash
# Manually collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check permissions on static files directory
docker-compose exec nginx ls -la /var/www/html/static
```

## Security Considerations

1. **Firewall Configuration**: Configure your server's firewall to only allow necessary ports (80, 443).

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Regular Updates**: Keep your system and Docker images updated.

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

3. **Monitoring**: Set up monitoring for your application.

```bash
# Install and configure Prometheus and Grafana for monitoring
# (This is beyond the scope of this guide)
```

4. **Logging**: Configure centralized logging.

```bash
# Install and configure ELK stack or similar for log management
# (This is beyond the scope of this guide)
```

## Performance Tuning

1. **Gunicorn Workers**: Adjust the number of Gunicorn workers based on your server's CPU cores.

```bash
# Edit .env file
# Set GUNICORN_WORKERS to (2 * CPU cores) + 1
```

2. **Database Optimization**: Tune PostgreSQL for better performance.

```bash
# Create a custom PostgreSQL configuration
mkdir -p postgres/conf
nano postgres/conf/postgresql.conf
```

Add the following to the configuration file:

```
# Memory settings
shared_buffers = 256MB
work_mem = 8MB
maintenance_work_mem = 64MB

# Query planner
effective_cache_size = 768MB

# Write-ahead log
wal_buffers = 8MB
```

Update the docker-compose.yml file to use this configuration:

```yaml
db:
  volumes:
    - ./postgres/conf/postgresql.conf:/etc/postgresql/postgresql.conf
  command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

3. **Redis Cache**: Optimize Redis configuration.

```bash
# Create a custom Redis configuration
mkdir -p redis/conf
nano redis/conf/redis.conf
```

Add the following to the configuration file:

```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

Update the docker-compose.yml file to use this configuration:

```yaml
redis:
  volumes:
    - ./redis/conf/redis.conf:/usr/local/etc/redis/redis.conf
  command: redis-server /usr/local/etc/redis/redis.conf
```