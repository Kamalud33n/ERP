"""
Workflow — Legacy Compatibility Layer
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.workflow import Request, ApprovalHistory
from app.schemas.workflow import RequestCreate, RequestOut, ApprovalIn
from app.models.user import User

router = APIRouter()


@router.post("/requests", response_model=RequestOut)
def create_request(
    payload:      RequestCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Legacy: create a generic workflow request.
    New code: use POST /api/v1/workflows/initiate instead.
    """
    req = Request(
        request_type = payload.request_type,
        title        = payload.title,
        description  = payload.description,
        department   = payload.department,
        amount       = payload.amount,
        status       = "pending",
        created_by   = current_user.id,
        created_at   = datetime.utcnow(),
        updated_at   = datetime.utcnow(),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/requests", response_model=List[RequestOut])
def list_requests(
    status:       Optional[str] = None,
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    q = db.query(Request)
    if status:
        q = q.filter(Request.status == status)
    return q.order_by(Request.created_at.desc()).all()


@router.get("/requests/{request_id}", response_model=RequestOut)
def get_request(
    request_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests/{request_id}/action")
def take_action(
    request_id:   int,
    payload:      ApprovalIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    db.add(ApprovalHistory(
        request_id  = request_id,
        approver_id = current_user.id,
        action      = payload.action,
        comment     = payload.comment,
        step        = payload.step,
        acted_at    = datetime.utcnow(),
    ))

    if payload.next_status:
        req.status = payload.next_status
    elif payload.action.lower() == "approved":
        req.status = "approved"
    elif payload.action.lower() == "rejected":
        req.status = "rejected"
    else:
        req.status = "in_progress"

    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    # Fire step-advance if request has a WorkflowTemplate assigned
    try:
        from app.api.v1.workflow_config import trigger_advance_for_request
        trigger_advance_for_request(req.id, db)
    except Exception:
        pass

    return {"message": "Action recorded", "request_id": req.id, "status": req.status}

