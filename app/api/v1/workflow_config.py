from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_admin, get_current_user
from app.models.workflow_config import WorkflowTemplate, WorkflowStep
from app.models.workflow import Request, ApprovalHistory
from app.schemas.workflow_config import TemplateCreate, TemplateOut, StepCreate
from datetime import datetime

router = APIRouter()

@router.post("/templates", response_model=TemplateOut)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    tpl = WorkflowTemplate(name=payload.name, description=payload.description, created_by=current_user.id, created_at=datetime.utcnow())
    db.add(tpl)
    db.commit()
    # add steps
    for s in payload.steps:
        step = WorkflowStep(template_id=tpl.id, name=s.name, sequence=s.sequence, approver_role=s.approver_role, approver_user_id=s.approver_user_id, auto_approve=s.auto_approve or False, is_final=s.is_final or False)
        db.add(step)
    db.commit()
    db.refresh(tpl)
    return tpl

@router.get("/templates", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(WorkflowTemplate).order_by(WorkflowTemplate.id.desc()).all()

@router.get("/templates/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tpl = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl

@router.post("/templates/{template_id}/assign")
def assign_template(template_id: int, request_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    tpl = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    # set template and initial step
    first_step = db.query(WorkflowStep).filter(WorkflowStep.template_id == tpl.id).order_by(asc(WorkflowStep.sequence)).first()
    req.template_id = tpl.id
    req.current_step_id = first_step.id if first_step else None
    req.status = 'in_progress' if first_step else 'approved'
    db.commit()
    db.refresh(req)
    # auto advance if first step auto_approve
    if first_step and first_step.auto_approve:
        # create history entry and move forward
        h = ApprovalHistory(request_id=req.id, approver_id=req.created_by, action='auto_approved', comment='Auto-approved step', step=first_step.name, acted_at=datetime.utcnow())
        db.add(h)
        db.commit()
        db.refresh(req)
        _ = advance_workflow(req, db)
    return {"message": "Template assigned", "request": req}


# core helper: advance workflow to next step; returns new step or None
def advance_workflow(req: Request, db: Session):
    # load template steps
    if not req.template_id:
        return None
    steps = db.query(WorkflowStep).filter(WorkflowStep.template_id == req.template_id).order_by(asc(WorkflowStep.sequence)).all()
    if not steps:
        return None
    # find current index
    cur_idx = -1
    for i, s in enumerate(steps):
        if req.current_step_id == s.id:
            cur_idx = i
            break
    next_idx = cur_idx + 1
    if next_idx >= len(steps):
        # no more steps -> finalize
        req.status = 'approved'
        req.current_step_id = None
        db.commit()
        return None
    next_step = steps[next_idx]
    req.current_step_id = next_step.id
    req.status = 'in_progress'
    db.commit()
    # if next step auto_approve then create history and recurse
    if next_step.auto_approve:
        h = ApprovalHistory(request_id=req.id, approver_id=req.created_by, action='auto_approved', comment='Auto-approved step', step=next_step.name, acted_at=datetime.utcnow())
        db.add(h)
        db.commit()
        return advance_workflow(req, db)
    return next_step

# expose helper for other modules
def trigger_advance_for_request(request_id: int, db: Session):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        return None
    return advance_workflow(req, db)
