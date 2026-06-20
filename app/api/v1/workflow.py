from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_finance, get_admin
from app.models.workflow import Request, ApprovalHistory
from app.schemas.workflow import RequestCreate, RequestOut, ApprovalIn
from app.models.user import User
from datetime import datetime

# import advance helper (avoid circular imports at top-level)
from app.api.v1.workflow_config import trigger_advance_for_request

router = APIRouter()

@router.post("/requests", response_model=RequestOut)
def create_request(payload: RequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = Request(
        request_type=payload.request_type,
        title=payload.title,
        description=payload.description,
        department=payload.department,
        amount=payload.amount,
        status="pending",
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@router.get("/requests/{request_id}", response_model=RequestOut)
def get_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@router.get("/requests", response_model=List[RequestOut])
def list_requests(status: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Request)
    if status:
        q = q.filter(Request.status == status)
    return q.order_by(Request.created_at.desc()).all()

@router.get("/requests/pending", response_model=List[RequestOut])
def pending_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple policy: admins see all, others see their department or requests they created
    if current_user.role == "admin":
        return db.query(Request).filter(Request.status.in_(["pending", "in_progress"])) .order_by(Request.created_at.desc()).all()
    # try to fetch employee.department if exists
    emp = None
    try:
        from app.models.employee import Employee
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    except Exception:
        emp = None
    if emp and emp.department:
        return db.query(Request).filter(Request.department == emp.department, Request.status.in_(["pending", "in_progress"])) .order_by(Request.created_at.desc()).all()
    # fallback: return requests created by user
    return db.query(Request).filter(Request.created_by == current_user.id).order_by(Request.created_at.desc()).all()

@router.post("/requests/{request_id}/action")
def take_action(request_id: int, payload: ApprovalIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    # create history entry
    h = ApprovalHistory(
        request_id=request_id,
        approver_id=current_user.id,
        action=payload.action,
        comment=payload.comment,
        step=payload.step,
        acted_at=datetime.utcnow()
    )
    db.add(h)
    # update request status
    if payload.next_status:
        req.status = payload.next_status
    else:
        if payload.action.lower() == "approved":
            req.status = "approved"
        elif payload.action.lower() == "rejected":
            req.status = "rejected"
        else:
            req.status = "in_progress"
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    # attempt to auto-advance workflow (if configured)
    try:
        trigger_advance_for_request(req.id, db)
    except Exception:
        pass

    return {"message": "Action recorded", "request": req}
