#!/bin/bash
# Automated Backup Script for MedNova ERP
# Backs up PostgreSQL database, Redis, and documents
# Schedule with cron: 0 2 * * * /app/scripts/backup.sh

set -e

# Configuration
BACKUP_DIR="/app/backups"
BACKUP_RETENTION_DAYS=30
DATABASE_HOST="${DATABASE_HOST:-postgres}"
DATABASE_USER="${DATABASE_USER:-mednova}"
DATABASE_NAME="${DATABASE_NAME:-mednova_erp}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔄 Starting MedNova ERP Backup (${TIMESTAMP})..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# ─────────────────────────────────────────────────────────────
# 1. PostgreSQL Backup
# ─────────────────────────────────────────────────────────────

echo "Backing up PostgreSQL database..."
BACKUP_FILE="$BACKUP_DIR/mednova_db_${TIMESTAMP}.sql.gz"

if pg_dump -h "$DATABASE_HOST" -U "$DATABASE_USER" "$DATABASE_NAME" | gzip > "$BACKUP_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ PostgreSQL backed up: $BACKUP_FILE ($SIZE)${NC}"
else
    echo -e "${RED}✗ PostgreSQL backup failed${NC}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# 2. Redis Backup
# ─────────────────────────────────────────────────────────────

echo "Backing up Redis..."
REDIS_BACKUP="$BACKUP_DIR/redis_${TIMESTAMP}.rdb"

if redis-cli --rdb "$REDIS_BACKUP" > /dev/null 2>&1; then
    SIZE=$(du -h "$REDIS_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Redis backed up: $REDIS_BACKUP ($SIZE)${NC}"
else
    echo -e "${RED}✗ Redis backup failed${NC}"
fi

# ─────────────────────────────────────────────────────────────
# 3. Documents Backup
# ─────────────────────────────────────────────────────────────

echo "Backing up document archive..."
DOCS_BACKUP="$BACKUP_DIR/documents_${TIMESTAMP}.tar.gz"

if tar -czf "$DOCS_BACKUP" /app/documents_archive/ 2>/dev/null; then
    SIZE=$(du -h "$DOCS_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Documents backed up: $DOCS_BACKUP ($SIZE)${NC}"
else
    echo -e "${RED}✗ Documents backup failed (continuing...)${NC}"
fi

# ─────────────────────────────────────────────────────────────
# 4. Cleanup Old Backups
# ─────────────────────────────────────────────────────────────

echo "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS} days)..."
CUTOFF_DATE=$(date -d "${BACKUP_RETENTION_DAYS} days ago" +%Y%m%d)

OLD_BACKUPS=$(find "$BACKUP_DIR" -maxdepth 1 -type f \( -name "*.gz" -o -name "*.rdb" \) | while read file; do
    DATE=$(echo $(basename "$file") | grep -oE '[0-9]{8}' | head -1)
    if [[ $DATE -lt $CUTOFF_DATE ]]; then
        echo "$file"
    fi
done)

if [ -z "$OLD_BACKUPS" ]; then
    echo -e "${GREEN}✓ No old backups to delete${NC}"
else
    echo "$OLD_BACKUPS" | xargs rm -f
    DELETED_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
    echo -e "${GREEN}✓ Deleted $DELETED_COUNT old backups${NC}"
fi

# ─────────────────────────────────────────────────────────────
# 5. Upload to Cloud (Optional)
# ─────────────────────────────────────────────────────────────

if [ -n "$AWS_S3_BUCKET" ]; then
    echo "Uploading backups to S3..."
    
    for backup_file in "$BACKUP_DIR"/*_${TIMESTAMP}*; do
        if [ -f "$backup_file" ]; then
            aws s3 cp "$backup_file" "s3://${AWS_S3_BUCKET}/backups/$(basename "$backup_file")" \
                --region "${AWS_REGION:-us-east-1}" \
                --sse AES256
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Uploaded $(basename "$backup_file")${NC}"
            else
                echo -e "${RED}✗ Failed to upload $(basename "$backup_file")${NC}"
            fi
        fi
    done
fi

# ─────────────────────────────────────────────────────────────
# 6. Backup Summary
# ─────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✓ Backup completed successfully!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Backup Summary:"
echo "  Database:    $BACKUP_FILE"
echo "  Redis:       $REDIS_BACKUP"
echo "  Documents:   $DOCS_BACKUP"
echo "  Location:    $BACKUP_DIR"
echo "  Retention:   $BACKUP_RETENTION_DAYS days"
echo ""

# ─────────────────────────────────────────────────────────────
# 7. Send Notification (Optional)
# ─────────────────────────────────────────────────────────────

if [ -n "$BACKUP_EMAIL" ]; then
    echo "Sending backup notification email..."
    
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    
    cat << EOF | mail -s "MedNova ERP Backup - ${TIMESTAMP}" "$BACKUP_EMAIL"
MedNova ERP Backup Report

Timestamp: ${TIMESTAMP}
Status: SUCCESS

Backups:
- Database: $(du -h "$BACKUP_FILE" | cut -f1)
- Redis: $(du -h "$REDIS_BACKUP" | cut -f1)
- Documents: $(du -h "$DOCS_BACKUP" | cut -f1)

Total Backup Size: $BACKUP_SIZE
Location: $BACKUP_DIR

Retention Policy: $BACKUP_RETENTION_DAYS days
Next Backup: $(date -d "+1 day" '+%Y-%m-%d 02:00:00')

---
Automated Backup System
MedNova ERP
EOF

    echo -e "${GREEN}✓ Notification email sent${NC}"
fi

echo "Backup script completed at $(date '+%Y-%m-%d %H:%M:%S')"
