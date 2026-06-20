#!/bin/bash
# MedNova ERP - Production Setup Script
# Automates Phase 1-3 of deployment

set -e  # Exit on error

echo "🏥 MedNova ERP - Production Setup"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ─────────────────────────────────────────────────────
# Phase 1: Install Dependencies
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 1] Installing Dependencies...${NC}"

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3 found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Install from python.org${NC}"
    exit 1
fi

echo "Installing Python packages..."
pip install -r requirements.txt -q

echo -e "${GREEN}✓ Dependencies installed${NC}"

# ─────────────────────────────────────────────────────
# Phase 2: Check Redis
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 2] Checking Redis...${NC}"

if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✓ Redis found${NC}"
    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
    
    if redis-cli ping | grep -q "PONG"; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Redis not found. Install with:${NC}"
    echo "   - Ubuntu: sudo apt-get install redis-server"
    echo "   - macOS: brew install redis"
    echo "   - Windows: Use Docker: docker run -d -p 6379:6379 redis:latest"
fi

# ─────────────────────────────────────────────────────
# Phase 3: PostgreSQL Check
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 3] Checking PostgreSQL...${NC}"

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL not found. Install from:${NC}"
    echo "   https://www.postgresql.org/download/"
    echo "   Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15"
fi

# ─────────────────────────────────────────────────────
# Phase 4: Environment Setup
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 4] Checking Environment Configuration...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
    
    # Check required env vars
    if grep -q "SMTP_HOST" .env; then
        echo -e "${GREEN}✓ Email (SMTP) configured${NC}"
    else
        echo -e "${YELLOW}⚠ Email (SMTP) not configured in .env${NC}"
    fi
    
    if grep -q "DATABASE_URL" .env; then
        echo -e "${GREEN}✓ Database URL configured${NC}"
    else
        echo -e "${YELLOW}⚠ Database URL not configured in .env${NC}"
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo "Creating .env from template..."
    cp .env.example .env 2>/dev/null || echo "Create .env manually"
fi

# ─────────────────────────────────────────────────────
# Phase 5: Database Setup
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 5] Database Setup...${NC}"

echo "Running database migrations..."
python -c "
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✓ Database tables created')
" 2>/dev/null || echo "Database already initialized or connection failed"

# ─────────────────────────────────────────────────────
# Phase 6: Test Email Service
# ─────────────────────────────────────────────────────

echo -e "${BLUE}[Phase 6] Testing Email Service...${NC}"

python -c "
from app.services.email_service import EmailConfig
if EmailConfig.is_configured():
    print('✓ Email (SMTP) is configured')
else:
    print('⚠ Email (SMTP) not configured - update .env with SMTP details')
" || echo "Email service check skipped"

# ─────────────────────────────────────────────────────
# Final Summary
# ─────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo ""
echo "Next Steps:"
echo "1. Update .env with your configuration:"
echo "   - SMTP credentials (Gmail, SendGrid, etc.)"
echo "   - Database URL (if not using defaults)"
echo "   - SECRET_KEY (generate a secure key)"
echo ""
echo "2. Start Redis server:"
echo "   redis-server"
echo ""
echo "3. Start the application:"
echo "   python run.py"
echo ""
echo "4. In another terminal, start Celery worker:"
echo "   celery -A app.tasks.celery_config worker --loglevel=info"
echo ""
echo "5. In another terminal, start Celery beat:"
echo "   celery -A app.tasks.celery_config beat --loglevel=info"
echo ""
echo "6. Access the app at:"
echo "   http://localhost:3000"
echo ""
echo "Documentation:"
echo "- Production Guide: docs/PRODUCTION_DEPLOYMENT_GUIDE.md"
echo "- Architecture Report: docs/ARCHITECTURE_COMPLETION_REPORT.md"
echo "- API Docs: http://localhost:3000/docs"
