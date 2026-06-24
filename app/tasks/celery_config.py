"""
Celery Configuration — Background Jobs
"""
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
import os, logging

load_dotenv()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "mednova_erp",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
)

celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="UTC", enable_utc=True, task_track_started=True,
    task_time_limit=30*60, task_soft_time_limit=25*60,
    worker_prefetch_multiplier=1, broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "check-contract-expiry": {"task": "app.tasks.alerts.check_contract_expiry",  "schedule": crontab(hour=8, minute=0)},
    "check-low-stock":       {"task": "app.tasks.alerts.check_low_stock",         "schedule": crontab(minute=0, hour="*/6")},
    "check-budget-overrun":  {"task": "app.tasks.alerts.check_budget_overrun",    "schedule": crontab(hour=9, minute=0)},
    "cleanup-notifications": {"task": "app.tasks.maintenance.cleanup_old_notifications", "schedule": crontab(day_of_week=0, hour=2, minute=0)},
}


@celery_app.task(name="app.tasks.email.send_email", bind=True, max_retries=3)
def send_email_task(self, to_email: str, subject: str, html_content: str):
    try:
        from app.services.email_service import EmailService
        import asyncio
        result = asyncio.run(EmailService.send_email(to_email, subject, html_content))
        return {"status": "sent" if result else "failed", "email": to_email}
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.tasks.workflow.route_approval")
def route_approval_task(request_id: int, request_type: str):
    logger.info(f"Routing approval: {request_type}#{request_id}")
    return {"status": "routed", "request_id": request_id}


@celery_app.task(name="app.tasks.notifications.send_approval_notification")
def send_approval_notification(approver_id: int, request_id: int, request_type: str):
    logger.info(f"Sending approval notification to user #{approver_id}")
    return {"status": "sent", "approver_id": approver_id}


@celery_app.task(name="app.tasks.alerts.check_contract_expiry")
def check_contract_expiry_task():
    """Daily 8 AM — find contracts expiring in 30 days, notify HR/admin."""
    try:
        from app.core.database import SessionLocal
        from app.services.hr_service import get_expiring_contracts
        from app.models.user import User
        from app.services.notification_service import create_notifications_bulk
        import datetime

        db = SessionLocal()
        try:
            expiring = get_expiring_contracts(db, days=30)
            if not expiring:
                return {"status": "checked", "alerts_sent": 0}
            user_ids = [u.id for u in db.query(User).filter(
                User.role.in_(["admin", "hr_manager"]), User.is_active == True).all()]
            alerts_sent = 0
            for contract in expiring:
                days_left = (contract.end_date - datetime.date.today()).days
                alerts_sent += create_notifications_bulk(
                    db=db, user_ids=user_ids,
                    title="Contract Expiring Soon",
                    message=(f"Contract for Employee #{contract.employee_id} "
                             f"({contract.position} / {contract.department}) expires in "
                             f"{days_left} day(s) on {contract.end_date}."),
                    module="hr",
                    notif_type="warning" if days_left > 7 else "alert",
                )
            return {"status": "checked", "expiring_contracts": len(expiring), "alerts_sent": alerts_sent}
        finally:
            db.close()
    except Exception as exc:
        logger.error("check_contract_expiry_task failed: %s", exc)
        return {"status": "error", "message": str(exc)}


@celery_app.task(name="app.tasks.alerts.check_low_stock")
def check_low_stock_task():
    """Every 6 hours — find items at/below min_stock, notify admin/hr."""
    try:
        from app.core.database import SessionLocal
        from app.services.inventory_service import get_low_stock_items
        from app.models.user import User
        from app.services.notification_service import create_notifications_bulk

        db = SessionLocal()
        try:
            low_items = get_low_stock_items(db)
            if not low_items:
                return {"status": "checked", "low_stock_items": 0}
            user_ids = [u.id for u in db.query(User).filter(
                User.role.in_(["admin", "hr_manager"]), User.is_active == True).all()]
            alerts_sent = 0
            for item in low_items:
                level = "OUT OF STOCK" if item.current_stock == 0 else "LOW STOCK"
                alerts_sent += create_notifications_bulk(
                    db=db, user_ids=user_ids,
                    title=f"Inventory Alert: {level}",
                    message=(f"Item '{item.name}' (SKU: {item.sku}) is {level.lower()}. "
                             f"Current: {item.current_stock} {item.unit}, Min: {item.min_stock} {item.unit}."),
                    module="inventory",
                    notif_type="alert" if item.current_stock == 0 else "warning",
                )
            return {"status": "checked", "low_stock_items": len(low_items), "alerts_sent": alerts_sent}
        finally:
            db.close()
    except Exception as exc:
        logger.error("check_low_stock_task failed: %s", exc)
        return {"status": "error", "message": str(exc)}


@celery_app.task(name="app.tasks.alerts.check_budget_overrun")
def check_budget_overrun_task():
    """Daily 9 AM — find budgets where spent > allocated, notify finance/admin."""
    try:
        from app.core.database import SessionLocal
        from app.services.finance_service import get_over_budget_alerts
        from app.models.user import User
        from app.services.notification_service import create_notifications_bulk

        db = SessionLocal()
        try:
            overrun = get_over_budget_alerts(db)
            if not overrun:
                return {"status": "checked", "overrun_budgets": 0}
            user_ids = [u.id for u in db.query(User).filter(
                User.role.in_(["admin", "finance"]), User.is_active == True).all()]
            alerts_sent = 0
            for budget in overrun:
                over_by = round(budget.spent - budget.amount, 2)
                alerts_sent += create_notifications_bulk(
                    db=db, user_ids=user_ids,
                    title="Budget Overrun Alert",
                    message=(f"Dept '{budget.department}' / cat '{budget.category}' is over budget "
                             f"by {over_by:.2f} for {budget.month}. "
                             f"Spent {budget.spent:.2f} of {budget.amount:.2f}."),
                    module="finance", notif_type="warning",
                )
            return {"status": "checked", "overrun_budgets": len(overrun), "alerts_sent": alerts_sent}
        finally:
            db.close()
    except Exception as exc:
        logger.error("check_budget_overrun_task failed: %s", exc)
        return {"status": "error", "message": str(exc)}


@celery_app.task(name="app.tasks.maintenance.cleanup_old_notifications")
def cleanup_old_notifications_task():
    """Weekly Sunday 2 AM — delete notifications older than 30 days."""
    try:
        from app.core.database import SessionLocal
        from app.models.hr import Notification
        import datetime

        db = SessionLocal()
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
            deleted = db.query(Notification).filter(
                Notification.created_at < cutoff
            ).delete(synchronize_session=False)
            db.commit()
            logger.info("Cleaned up %d old notifications", deleted)
            return {"status": "cleaned", "deleted_count": deleted}
        finally:
            db.close()
    except Exception as exc:
        logger.error("cleanup_old_notifications_task failed: %s", exc)
        return {"status": "error", "message": str(exc)}