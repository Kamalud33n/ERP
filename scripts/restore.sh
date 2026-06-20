#!/bin/bash
# Restore Script for MedNova ERP Backups
# Restores PostgreSQL database from backup

set -e

# Configuration
BACKUP_DIR="/app/backups"
DATABASE_HOST="${DATABASE_HOST:-postgres}"
DATABASE_USER="${DATABASE_USER:-mednova}"
DATABASE_NAME="${DATABASE_NAME:-mednova_erp}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
print_header() {
    echo "═══════════════════════════════════════════════════════"
    echo "$1"
    echo "═══════════════════════════════════════════════════════"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Main script
print_header "🔄 MedNova ERP Backup Restore"

# Check for backup file argument
if [ -z "$1" ]; then
    echo ""
    echo "Usage: ./restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/mednova_db_*.sql.gz 2>/dev/null | awk '{print "  " $9}' || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Validate backup file
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "Backup Details:"
echo "  File:     $BACKUP_FILE"
echo "  Size:     $SIZE"
echo "  Modified: $(stat -c '%y' "$BACKUP_FILE")"
echo ""

# Confirm restore
print_warning "This will REPLACE the current database!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_warning "Restore cancelled"
    exit 0
fi

# Create backup of current database
print_header "Creating backup of current database..."
CURRENT_BACKUP="$BACKUP_DIR/mednova_db_$(date +%Y%m%d_%H%M%S)_pre_restore.sql.gz"

if pg_dump -h "$DATABASE_HOST" -U "$DATABASE_USER" "$DATABASE_NAME" | gzip > "$CURRENT_BACKUP"; then
    print_success "Current database backed up: $CURRENT_BACKUP"
else
    print_error "Failed to backup current database"
    exit 1
fi

# Drop existing database
print_header "Dropping existing database..."
if PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -c "DROP DATABASE IF EXISTS \"$DATABASE_NAME\"" postgres; then
    print_success "Database dropped"
else
    print_error "Failed to drop database"
    exit 1
fi

# Create new database
print_header "Creating new database..."
if PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -c "CREATE DATABASE \"$DATABASE_NAME\"" postgres; then
    print_success "Database created"
else
    print_error "Failed to create database"
    exit 1
fi

# Restore from backup
print_header "Restoring from backup..."
if gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME"; then
    print_success "Database restored successfully"
else
    print_error "Failed to restore database"
    print_warning "Pre-restore backup available at: $CURRENT_BACKUP"
    exit 1
fi

# Verify restoration
print_header "Verifying restoration..."
RESTORED_COUNT=$(PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")

if [ "$RESTORED_COUNT" -gt 0 ]; then
    print_success "Database restored with $RESTORED_COUNT tables"
else
    print_error "Database verification failed"
    exit 1
fi

# Final report
print_header "✓ Restore Completed Successfully!"
echo ""
echo "Restoration Details:"
echo "  Source Backup:     $BACKUP_FILE"
echo "  Target Database:   $DATABASE_NAME"
echo "  Pre-Restore Backup: $CURRENT_BACKUP"
echo "  Tables Restored:   $RESTORED_COUNT"
echo "  Timestamp:         $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
print_warning "Please verify data integrity and restart the application"
