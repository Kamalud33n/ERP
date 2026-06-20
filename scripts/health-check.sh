#!/bin/bash
# Health Check Script for MedNova ERP
# Monitors all critical services and reports status

set -e

# Configuration
HEALTH_CHECK_DIR="/app/health_checks"
APP_URL="${APP_URL:-http://localhost:3000}"
DATABASE_HOST="${DATABASE_HOST:-localhost}"
DATABASE_USER="${DATABASE_USER:-mednova}"
DATABASE_NAME="${DATABASE_NAME:-mednova_erp}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

mkdir -p "$HEALTH_CHECK_DIR"

# Functions
check_service() {
    local service_name=$1
    local check_command=$2
    local timeout=${3:-5}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking $service_name... "
    
    if timeout $timeout bash -c "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_threshold() {
    local name=$1
    local value=$2
    local threshold=$3
    local operator=$4
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking $name ($value / $threshold)... "
    
    if [[ "$operator" == "lt" ]] && (( $(echo "$value < $threshold" | bc -l) )); then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    elif [[ "$operator" == "gt" ]] && (( $(echo "$value > $threshold" | bc -l) )); then
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠${NC}"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    fi
}

# Header
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  MedNova ERP - Health Check Report                    ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────
# 1. Application Health
# ─────────────────────────────────────────────────────────────

echo -e "${BLUE}→ Application Services${NC}"

check_service "FastAPI App" "curl -sf $APP_URL/health"
check_service "API Endpoints" "curl -sf $APP_URL/api/v1/health"
check_service "Static Files" "curl -sf $APP_URL/static/index.html" 3

# ─────────────────────────────────────────────────────────────
# 2. Database Health
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Database Services${NC}"

check_service "PostgreSQL Connection" "pg_isready -h $DATABASE_HOST -U $DATABASE_USER"
check_service "Database Query" "PGPASSWORD='$DATABASE_PASSWORD' psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c 'SELECT 1' > /dev/null"

# Check database size
if PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" > /dev/null 2>&1; then
    DB_SIZE=$(PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DATABASE_NAME'))")
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo "Database Size: $DB_SIZE"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# ─────────────────────────────────────────────────────────────
# 3. Cache/Redis Health
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Cache Services${NC}"

check_service "Redis Connection" "redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null"
check_service "Redis Memory" "redis-cli -h $REDIS_HOST -p $REDIS_PORT info memory | grep -q 'used_memory'"

if command -v redis-cli > /dev/null 2>&1; then
    REDIS_MEMORY=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo "Redis Memory: $REDIS_MEMORY"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# ─────────────────────────────────────────────────────────────
# 4. Background Jobs (Celery)
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Background Job Services${NC}"

check_service "Celery Worker" "ps aux | grep -i 'celery worker' | grep -v grep > /dev/null"
check_service "Celery Beat" "ps aux | grep -i 'celery beat' | grep -v grep > /dev/null"

# ─────────────────────────────────────────────────────────────
# 5. Storage/MinIO Health
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Storage Services${NC}"

MINIO_HOST="${MINIO_HOST:-localhost}"
MINIO_PORT="${MINIO_PORT:-9000}"

check_service "MinIO S3 API" "curl -sf http://$MINIO_HOST:$MINIO_PORT/minio/health/live > /dev/null"
check_service "Document Archive" "[ -d /app/documents_archive ] && [ -w /app/documents_archive ]"

# ─────────────────────────────────────────────────────────────
# 6. System Resources
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ System Resources${NC}"

# Disk usage
DISK_USAGE=$(df /app | awk 'NR==2 {print $5}' | sed 's/%//')
check_threshold "Disk Usage" "$DISK_USAGE" 80 "lt"

# Memory usage
MEMORY_USAGE=$(free | awk 'NR==2 {printf("%.0f", $3/$2 * 100)}')
check_threshold "Memory Usage" "$MEMORY_USAGE" 85 "lt"

# CPU load
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | sed 's/ //g')
CORES=$(nproc)
LOAD_THRESHOLD=$CORES
check_threshold "CPU Load" "$LOAD" "$LOAD_THRESHOLD" "lt"

# ─────────────────────────────────────────────────────────────
# 7. Security Checks
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Security Checks${NC}"

# Check if SSL certificate exists
if [ -f "/etc/nginx/certs/cert.pem" ]; then
    check_service "SSL Certificate" "[ -f /etc/nginx/certs/cert.pem ]"
    # Check certificate expiry
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/nginx/certs/cert.pem | cut -d= -f2)
    DAYS_UNTIL_EXPIRY=$(( ($(date -d "$CERT_EXPIRY" +%s) - $(date +%s)) / 86400 ))
    if [ "$DAYS_UNTIL_EXPIRY" -gt 30 ]; then
        echo -e "SSL Certificate Expiry: ${GREEN}✓${NC} ($DAYS_UNTIL_EXPIRY days)"
    else
        echo -e "SSL Certificate Expiry: ${RED}✗${NC} ($DAYS_UNTIL_EXPIRY days - RENEW SOON!)"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ "$DAYS_UNTIL_EXPIRY" -gt 30 ]; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi

# ─────────────────────────────────────────────────────────────
# 8. Backup Status
# ─────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}→ Backup Status${NC}"

LATEST_BACKUP=$(ls -t /app/backups/mednova_db_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")))
    BACKUP_AGE_HOURS=$((BACKUP_AGE / 3600))
    
    if [ $BACKUP_AGE_HOURS -lt 25 ]; then
        echo -e "Latest Backup: ${GREEN}✓${NC} (${BACKUP_AGE_HOURS}h ago - $(basename "$LATEST_BACKUP"))"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "Latest Backup: ${RED}✗${NC} (${BACKUP_AGE_HOURS}h ago - OVERDUE!)"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi

# ─────────────────────────────────────────────────────────────
# 9. Summary Report
# ─────────────────────────────────────────────────────────────

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Health Check Summary                                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Total Checks:      $TOTAL_CHECKS"
echo -e "Passed:            ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Warnings:          ${YELLOW}$WARNING_CHECKS${NC}"
echo -e "Failed:            ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    HEALTH_STATUS="HEALTHY"
else
    echo -e "${RED}✗ Issues detected - see above${NC}"
    HEALTH_STATUS="UNHEALTHY"
fi

# Save report
REPORT_FILE="$HEALTH_CHECK_DIR/health_$(date +%Y%m%d_%H%M%S).txt"
cat > "$REPORT_FILE" << EOF
MedNova ERP Health Check Report
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Status: $HEALTH_STATUS

Summary:
- Total Checks: $TOTAL_CHECKS
- Passed: $PASSED_CHECKS
- Warnings: $WARNING_CHECKS
- Failed: $FAILED_CHECKS
EOF

echo ""
echo "Report saved to: $REPORT_FILE"
echo ""

# Exit code based on failed checks
[ $FAILED_CHECKS -eq 0 ] && exit 0 || exit 1
