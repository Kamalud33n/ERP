from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_admin
from app.models.hr import ActivityLog

router = APIRouter()

@router.get("/logs")
def get_all_logs(db: Session = Depends(get_db), current_user=Depends(get_admin)):
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()
    return [
        {
            "id":           l.id,
            "action":       l.action,
            "module":       l.module,
            "reference_id": l.reference_id,
            "done_by":      l.done_by,
            "done_by_role": l.done_by_role,
            "description":  l.description,
            "reversed":     l.reversed,
            "created_at":   l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ]

@router.get("/logs/module/{module}")
def get_logs_by_module(module: str, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    logs = db.query(ActivityLog).filter(
        ActivityLog.module == module
    ).order_by(ActivityLog.created_at.desc()).all()
    return [
        {
            "id":           l.id,
            "action":       l.action,
            "module":       l.module,
            "reference_id": l.reference_id,
            "done_by":      l.done_by,
            "done_by_role": l.done_by_role,
            "description":  l.description,
            "reversed":     l.reversed,
            "created_at":   l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ]