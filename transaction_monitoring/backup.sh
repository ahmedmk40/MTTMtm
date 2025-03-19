#!/bin/bash

# Exit on error
set -e

# Default values
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
KEEP_DAYS=30
COMPRESS=true

# Function to display help
show_help() {
    echo "Transaction Monitoring System Backup Script"
    echo ""
    echo "Usage: ./backup.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -d, --backup-dir DIR       Specify the backup directory (default: ./backups)"
    echo "  -k, --keep-days DAYS       Number of days to keep backups (default: 30)"
    echo "  -n, --no-compress          Do not compress the backup files"
    echo ""
    echo "Examples:"
    echo "  ./backup.sh                Create a backup with default settings"
    echo "  ./backup.sh -d /mnt/backups -k 60  Create a backup in /mnt/backups and keep for 60 days"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -k|--keep-days)
            KEEP_DAYS="$2"
            shift 2
            ;;
        -n|--no-compress)
            COMPRESS=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting backup process..."
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
if [ -f .env ]; then
    source .env
fi

DB_NAME=${DB_NAME:-transaction_monitoring}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

# Check if we're running in Docker
if docker-compose ps | grep -q db; then
    echo "Using Docker Compose for database backup..."
    docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
else
    echo "Using direct PostgreSQL connection for database backup..."
    export PGPASSWORD="$DB_PASSWORD"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
fi

# Backup media files
echo "Backing up media files..."
if [ -d "media" ]; then
    if [ "$COMPRESS" = true ]; then
        tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C media .
    else
        mkdir -p "$BACKUP_DIR/media_backup_$TIMESTAMP"
        cp -r media/* "$BACKUP_DIR/media_backup_$TIMESTAMP/"
    fi
else
    echo "Media directory not found, skipping media backup."
fi

# Backup static files
echo "Backing up static files..."
if [ -d "staticfiles" ]; then
    if [ "$COMPRESS" = true ]; then
        tar -czf "$BACKUP_DIR/static_backup_$TIMESTAMP.tar.gz" -C staticfiles .
    else
        mkdir -p "$BACKUP_DIR/static_backup_$TIMESTAMP"
        cp -r staticfiles/* "$BACKUP_DIR/static_backup_$TIMESTAMP/"
    fi
else
    echo "Static files directory not found, skipping static files backup."
fi

# Remove old backups
echo "Removing backups older than $KEEP_DAYS days..."
find "$BACKUP_DIR" -name "db_backup_*.sql" -type f -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name "media_backup_*.tar.gz" -type f -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name "static_backup_*.tar.gz" -type f -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name "media_backup_*" -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} \; 2>/dev/null || true
find "$BACKUP_DIR" -name "static_backup_*" -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} \; 2>/dev/null || true

echo "Backup completed successfully!"
echo "Backup files:"
ls -la "$BACKUP_DIR" | grep "$TIMESTAMP"