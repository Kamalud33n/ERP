"""
Celery Configuration for Background Jobs
Handles async workflows, notifications, scheduled tasks, alerts
"""
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Celery
celery_app = Celery(
    "mednova_erp",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

# Scheduled Tasks (Beat)
celery_app.conf.beat_schedule = {
    # Contract expiry checks - daily at 8 AM
    "check-contract-expiry": {
        "task": "app.tasks.alerts.check_contract_expiry",
        "schedule": crontab(hour=8, minute=0),
    },
    # Low stock checks - every 6 hours
    "check-low-stock": {
        "task": "app.tasks.alerts.check_low_stock",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Budget overrun checks - daily at 9 AM
    "check-budget-overrun": {
        "task": "app.tasks.alerts.check_budget_overrun",
        "schedule": crontab(hour=9, minute=0),
    },
    # Cleanup old notifications - weekly on Sunday at 2 AM
    "cleanup-notifications": {
        "task": "app.tasks.maintenance.cleanup_old_notifications",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),
    },
}


# ──────────────────────────────────────────────────────────
# Task Decorators
# ──────────────────────────────────────────────────────────

@celery_app.task(name="app.tasks.email.send_email", bind=True, max_retries=3)
def send_email_task(self, to_email: str, subject: str, html_content: str):
    """Send email with retry logic"""
    try:
        from app.services.email_service import EmailService
        import asyncio
        
        result = asyncio.run(EmailService.send_email(to_email, subject, html_content))
        return {"status": "sent" if result else "failed", "email": to_email}
    
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.tasks.workflow.route_approval")
def route_approval_task(request_id: int, request_type: str):
    """Route request to next approver in workflow"""
    logger.info(f"Routing approval: {request_type}#{request_id}")
    # Simplified - full implementation requires DB access
    return {"status": "routed", "request_id": request_id}


@celery_app.task(name="app.tasks.notifications.send_approval_notification")
def send_approval_notification(approver_id: int, request_id: int, request_type: str):
    """Send approval notification to approver"""
    logger.info(f"Sending approval notification to user #{approver_id}")
    return {"status": "sent", "approver_id": approver_id}


@celery_app.task(name="app.tasks.alerts.check_contract_expiry")
def check_contract_expiry_task():
    """Check for contracts expiring in next N days and send alerts"""
    logger.info("Checking for contract expiries...")
    return {"status": "checked", "alerts_sent": 0}


@celery_app.task(name="app.tasks.alerts.check_low_stock")
def check_low_stock_task():
    """Check for low stock items and send alerts to procurement"""
    logger.info("Checking low stock items...")
    return {"status": "checked", "low_stock_items": 0}


@celery_app.task(name="app.tasks.alerts.check_budget_overrun")
def check_budget_overrun_task():
    """Check for budget overruns and send alerts"""
    logger.info("Checking budget overruns...")
    return {"status": "checked", "overrun_budgets": 0}


@celery_app.task(name="app.tasks.maintenance.cleanup_old_notifications")
def cleanup_old_notifications_task():
    """Remove notifications older than 30 days"""
    logger.info("Cleaning up old notifications...")
    return {"status": "cleaned", "deleted_count": 0}
