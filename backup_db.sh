#!/bin/bash

# Configuration (.env)
# CONTAINER_NAME - PostgreSQL container name (dcps => NAME)
# DB_NAME
# DB_USER
# BACKUP_DIR - Directory where backups will be stored

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql"
ARCHIVE_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.tgz"

# Ensure the backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup for database: $DB_NAME"

# Run pg_dump inside the PostgreSQL container
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f "/tmp/${DB_NAME}_backup.sql"

if [ $? -eq 0 ]; then
    echo "Backup created inside container at /tmp/${DB_NAME}_backup.sql"
else
    echo "Error: Failed to create backup inside container"
    exit 1
fi

# Copy the backup file from the container to the host
docker cp "$CONTAINER_NAME:/tmp/${DB_NAME}_backup.sql" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successfully copied to host: $BACKUP_FILE"
else
    echo "Error: Failed to copy backup to host"
    exit 1
fi

# Archive the backup file
tar -czf "$ARCHIVE_FILE" -C "$BACKUP_DIR" "$(basename "$BACKUP_FILE")"

if [ $? -eq 0 ]; then
    echo "Backup successfully archived: $ARCHIVE_FILE"
    rm "$BACKUP_FILE"  # Remove the original SQL file after archiving
else
    echo "Error: Failed to archive backup"
    exit 1
fi

# (Optional) Remove the backup file inside the container
docker exec "$CONTAINER_NAME" rm "/tmp/${DB_NAME}_backup.sql"

echo "Backup completed successfully."
