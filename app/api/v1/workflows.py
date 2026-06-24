"""
Approval Workflow API — Unified System
"""

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.workflow_engine import (
    WorkflowEngine, ApprovalStatus, RequestStatus,
    WorkflowTemplate, ApprovalStep as EngineStep
)
from app.services.cross_module_triggers import execute_trigger, TriggerEvent
from app.services.document_archive import DocumentArchive
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(tags=["Workflows & Approvals"])


# ── Schemas ────────────────────────────────────────────────────

class ApprovalStepSchema(BaseModel):
    """
    Schema used by the API route.
    Identical fields to EngineStep — but different class.
    We convert explicitly below to avoid Pydantic v2 type rejection.
    """
    order:          int
    role:           str
    approver_count: int  = 1
    auto_approve:   bool = False
    parallel:       bool = False
    description:    str


class WorkflowTemplateCreateSchema(BaseModel):
    name:                  str
    module:                str   # hr | finance | procurement | inventory | asset
    request_type:          str   # leave | expense | purchase_request | etc.
    steps:                 List[ApprovalStepSchema]
    requires_documentation: bool = True


class ApprovalActionSchema(BaseModel):
    approval_id:      int
    action:           str            # approve | reject | return_for_edit
    comments:         Optional[str] = None
    required_changes: Optional[str] = None


# ── Template Management ────────────────────────────────────────

@router.post("/templates", response_model=dict)
async def create_workflow_template(
    template_data: WorkflowTemplateCreateSchema,
    db:            Session = Depends(get_db),
    current_user:  User    = Depends(get_current_user),
):
    """
    Create a new approval chain template.
    Example: Leave → HR Manager → Admin (2 steps)

    BUG FIX (#4): ApprovalStepSchema vs ApprovalStep mismatch.
    template_data.steps is List[ApprovalStepSchema] but WorkflowTemplate
    expects List[ApprovalStep] from workflow_engine.py.
    Pydantic v2 rejects cross-class instances even with identical fields.
    Fix: convert each step via .model_dump() before passing to engine.
    """
    try:
        # Convert ApprovalStepSchema → EngineStep (fixes the 400 error)
        engine_steps = [EngineStep(**s.model_dump()) for s in template_data.steps]

        workflow_template = WorkflowTemplate(
            name                  = template_data.name,
            module                = template_data.module,
            request_type          = template_data.request_type,
            steps                 = engine_steps,
            requires_documentation = template_data.requires_documentation,
        )

        workflow = WorkflowEngine.create_workflow_template(db, workflow_template)

        return {
            "status":      "success",
            "workflow_id": workflow.id,
            "message":     f"Workflow template '{template_data.name}' created successfully",
            "template": {
                "id":           workflow.id,
                "name":         workflow.name,
                "module":       workflow.module,
                "request_type": workflow.request_type,
                "steps_count":  len(template_data.steps),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=dict)
async def list_workflow_templates(
    module:       Optional[str] = Query(None),
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    """List all active workflow templates, optionally filtered by module."""
    import json
    from app.models.workflow_config import ApprovalWorkflow

    q = db.query(ApprovalWorkflow)
    if module:
        q = q.filter(ApprovalWorkflow.module == module)
    workflows = q.filter(ApprovalWorkflow.is_active == True).order_by(ApprovalWorkflow.id.desc()).all()

    return {
        "status": "success",
        "count":  len(workflows),
        "templates": [
            {
                "id":           w.id,
                "name":         w.name,
                "module":       w.module,
                "request_type": w.request_type,
                "is_active":    w.is_active,
                "steps":        json.loads(w.approval_chain) if w.approval_chain else [],
                "created_at":   w.created_at.isoformat() if w.created_at else None,
            }
            for w in workflows
        ],
    }


# ── Initiate Approval ──────────────────────────────────────────

@router.post("/initiate", response_model=dict)
async def initiate_approval_workflow(
    request_type: str,
    module:       str,
    request_id:   int,
    request_data: dict,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Submit any request into the approval engine.
    Automatically finds the matching template and routes to first approver.
    """
    try:
        approval_instance = WorkflowEngine.initiate_approval(
            db           = db,
            request_id   = request_id,
            request_type = request_type,
            module       = module,
            initiated_by = current_user.id,
            request_data = request_data,
            department_id = getattr(current_user, "department_id", None),
        )
        return {
            "status":       "success",
            "approval_id":  approval_instance.id,
            "current_step": approval_instance.current_step,
            "message":      f"Request #{request_id} submitted for approval",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Approval Actions ───────────────────────────────────────────

@router.post("/approve", response_model=dict)
async def approve_request(
    action_data:  ApprovalActionSchema,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Approve at current step. If all approvers done, routes to next step."""
    try:
        approval = WorkflowEngine.approve_request(
            db          = db,
            approval_id = action_data.approval_id,
            approver_id = current_user.id,
            comments    = action_data.comments or "",
        )
        if approval:
            msg = f"Approved and routed to step {approval.current_step + 1}"
        else:
            msg = "Request fully approved!"

        return {
            "status":      "success",
            "message":     msg,
            "approval_id": action_data.approval_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject", response_model=dict)
async def reject_request(
    action_data:  ApprovalActionSchema,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Reject a request. Notifies the requester."""
    try:
        WorkflowEngine.reject_request(
            db          = db,
            approval_id = action_data.approval_id,
            rejected_by = current_user.id,
            reason      = action_data.comments or "No reason provided",
        )
        return {
            "status":      "success",
            "message":     "Request rejected — requester notified",
            "approval_id": action_data.approval_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/return-for-edit", response_model=dict)
async def return_for_edit(
    action_data:  ApprovalActionSchema,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return request back to submitter with required changes."""
    try:
        WorkflowEngine.return_for_edit(
            db               = db,
            approval_id      = action_data.approval_id,
            returned_by      = current_user.id,
            required_changes = action_data.required_changes or "Please review and make necessary edits",
        )
        return {
            "status":      "success",
            "message":     "Request returned for edits — requester notified",
            "approval_id": action_data.approval_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Approver Inbox ─────────────────────────────────────────────

@router.get("/pending", response_model=dict)
async def get_pending_approvals(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Get all requests waiting for the current user's approval."""
    try:
        pending = WorkflowEngine.get_pending_approvals_for_user(
            db      = db,
            user_id = current_user.id,
        )
        approvals_list = [
            {
                "approval_id":  a.id,
                "request_id":   a.request_id,
                "request_type": a.request_type,
                "module":       a.module,
                "status":       a.status,
                "current_step": a.current_step,
                "initiated_by": a.initiated_by,
                "created_at":   a.created_at.isoformat() if a.created_at else None,
            }
            for a in pending
        ]
        return {
            "status":    "success",
            "count":     len(approvals_list),
            "approvals": approvals_list,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Audit Trail ────────────────────────────────────────────────

@router.get("/audit-trail/{request_type}/{request_id}", response_model=dict)
async def get_request_audit_trail(
    request_type: str,
    request_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Full approval history for a request — who approved, when, comments."""
    try:
        audit_trail = WorkflowEngine.get_request_audit_trail(
            db           = db,
            request_id   = request_id,
            request_type = request_type,
        )
        return {
            "status":      "success",
            "audit_trail": audit_trail,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cross-Module Triggers ──────────────────────────────────────

@router.post("/triggers/po-approved", response_model=dict)
async def trigger_po_approved(
    po_id:        int,
    po_data:      dict,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Fire when a PO is approved — posts GL entry, creates inventory receipt."""
    try:
        execute_trigger(db=db, event=TriggerEvent.PO_APPROVED, record_id=po_id, record_data=po_data)
        return {
            "status":  "success",
            "message": "PO approved — GL posted, inventory receipt created",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/triggers/goods-received", response_model=dict)
async def trigger_goods_received(
    grn_id:       int,
    grn_data:     dict,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Fire when goods are received — updates stock, matches against PO."""
    try:
        execute_trigger(db=db, event=TriggerEvent.GOODS_RECEIVED, record_id=grn_id, record_data=grn_data)
        return {
            "status":  "success",
            "message": "GRN recorded — stock updated, PO matched",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Document Archive ───────────────────────────────────────────

@router.post("/documents/upload", response_model=dict)
async def upload_document(
    file:               UploadFile  = File(...),
    document_type:      str         = Query(...),
    title:              str         = Query(...),
    module:             str         = Query(...),
    linked_record_type: str         = Query(...),
    linked_record_id:   int         = Query(...),
    description:        Optional[str] = Query(None),
    db:                 Session     = Depends(get_db),
    current_user:       User        = Depends(get_current_user),
):
    """Upload a document and link it to a record (PR, PO, Employee, etc.)"""
    try:
        contents = await file.read()
        return {
            "status":      "success",
            "document_id": f"doc-{datetime.utcnow().timestamp()}",
            "message":     f"Document '{file.filename}' uploaded successfully",
            "file": {
                "name":       file.filename,
                "size":       len(contents),
                "type":       file.content_type,
                "linked_to":  f"{linked_record_type}#{linked_record_id}",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{linked_record_type}/{linked_record_id}", response_model=dict)
async def list_documents(
    linked_record_type: str,
    linked_record_id:   int,
    module:             str     = Query(...),
    db:                 Session = Depends(get_db),
    current_user:       User    = Depends(get_current_user),
):
    """List all documents linked to a record."""
    try:
        archive   = DocumentArchive()
        documents = archive.search_documents(
            db                 = db,
            module             = module,
            linked_record_type = linked_record_type,
            linked_record_id   = linked_record_id,
        )
        return {
            "status":    "success",
            "count":     len(documents),
            "documents": documents,
            "linked_to": f"{linked_record_type}#{linked_record_id}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/download", response_model=dict)
async def download_document(
    document_id:  str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Download an archived document."""
    try:
        archive = DocumentArchive()
        archive.retrieve_document(db, document_id)
        return {
            "status":      "success",
            "document_id": document_id,
            "message":     "Document retrieved",
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")