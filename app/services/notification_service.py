"""
Notification Service
====================
Central helper for writing in-app Notification rows and sending emails.

Design rules:
  • Fire-and-forget: errors logged, never re-raised.
  • Notification failure must never roll back a business transaction.
  • Email is best-effort — if SMTP not configured, silently skipped.
  • notify_user / notify_users_by_role = used by hr/finance/procurement/inventory services
  • create_notification / create_notifications_bulk = lower-level helpers
"""

from __future__ import annotations
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.hr import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Core Write Helpers ─────────────────────────────────────────────────────────

def create_notification(
    db:         Session,
    user_id:    int,
    title:      str,
    message:    str,
    module:     str = "system",
    notif_type: str = "info",
) -> Notification | None:
    """Write one Notification row. Never raises."""
    try:
        notif = Notification(
            user_id = user_id,
            title   = title,
            message = message,
            type    = notif_type,
            module  = module,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as exc:
        logger.error("create_notification failed for user %s: %s", user_id, exc)
        db.rollback()
        return None


def create_notifications_bulk(
    db:         Session,
    user_ids:   list[int],
    title:      str,
    message:    str,
    module:     str = "system",
    notif_type: str = "info",
) -> int:
    """Write notifications for multiple users in one commit. Never raises."""
    if not user_ids:
        return 0
    try:
        rows = [
            Notification(
                user_id = uid,
                title   = title,
                message = message,
                type    = notif_type,
                module  = module,
            )
            for uid in set(user_ids)
        ]
        db.add_all(rows)
        db.commit()
        return len(rows)
    except Exception as exc:
        logger.error("create_notifications_bulk failed: %s", exc)
        db.rollback()
        return 0


# ── Email (best-effort, never crashes) ────────────────────────────────────────

def _send_email_safely(to_email: str, subject: str, html_content: str) -> bool:
    """
    Best-effort email send.
    Uses nest_asyncio to safely run async email inside FastAPI's sync routes.
    If SMTP is not configured or anything fails — just logs and returns False.
    Never raises.
    """
    try:
        import asyncio
        import nest_asyncio
        from app.services.email_service import EmailService
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            EmailService.send_email(to_email, subject, html_content)
        )
    except Exception as e:
        logger.error("email send failed for %s: %s", to_email, e)
        return False


# ── High-level Wrappers (used by hr/finance/procurement/inventory) ─────────────

def notify_user(
    db:            Session,
    user_id:       int,
    title:         str,
    message:       str,
    type:          str = "info",
    module:        str = "system",
    email_subject: Optional[str] = None,
    email_html:    Optional[str] = None,
) -> Notification | None:
    """
    Create one in-app notification + optionally send email.
    Used by all service files for single-user notifications.
    """
    notif = create_notification(
        db, user_id=user_id, title=title,
        message=message, module=module, notif_type=type
    )

    if email_subject and email_html:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.email:
            _send_email_safely(user.email, email_subject, email_html)
        else:
            logger.warning("notify_user: no email on file for user_id=%s", user_id)

    return notif


def notify_users_by_role(
    db:            Session,
    roles:         list,
    title:         str,
    message:       str,
    type:          str = "info",
    module:        str = "system",
    email_subject: Optional[str] = None,
    email_html:    Optional[str] = None,
) -> int:
    """
    Notify every active user holding any of the given roles.
    Returns count of notifications created.
    Used by service files for team-wide alerts (e.g. HR team, Finance team).
    """
    users = db.query(User).filter(
        User.role.in_(roles),
        User.is_active == True
    ).all()

    count = 0
    for user in users:
        notif = notify_user(
            db, user_id=user.id,
            title=title, message=message,
            type=type, module=module,
            email_subject=email_subject,
            email_html=email_html,
        )
        if notif:
            count += 1
    return count


# ── Query Helpers (used by notifications router) ───────────────────────────────

def get_notifications_for_user(
    db:          Session,
    user_id:     int,
    unread_only: bool = False,
    limit:       int  = 50,
) -> list[Notification]:
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()


def mark_read(db: Session, notif_id: int, user_id: int) -> bool:
    notif = db.query(Notification).filter(
        Notification.id      == notif_id,
        Notification.user_id == user_id,
    ).first()
    if not notif:
        return False
    notif.is_read = True
    db.commit()
    return True


def mark_all_read(db: Session, user_id: int) -> int:
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return count