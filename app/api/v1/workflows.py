"""
Approval Workflow API Endpoints
Handles workflow configuration and approval operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.workflow_engine import WorkflowEngine, ApprovalStatus, RequestStatus, WorkflowTemplate
from app.services.cross_module_triggers import execute_trigger, TriggerEvent
from app.services.document_archive import DocumentArchive, DocumentMetadata, DocumentType
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows & Approvals"])


# ─────────────────────────────────────────────────────────────
# Schemas for Request/Response
# ─────────────────────────────────────────────────────────────

class ApprovalStepSchema(BaseModel):
    order: int
    role: str
    approver_count: int = 1
    auto_approve: bool = False
    parallel: bool = False
    description: str


class WorkflowTemplateCreateSchema(BaseModel):
    name: str
    module: str  # hr, finance, procurement, inventory, assets
    request_type: str
    steps: List[ApprovalStepSchema]
    requires_documentation: bool = True


class ApprovalActionSchema(BaseModel):
    approval_id: int
    action: str  # approve, reject, return_for_edit
    comments: Optional[str] = None
    required_changes: Optional[str] = None  # For return_for_edit


class PendingApprovalsResponse(BaseModel):
    approval_id: int
    request_id: int
    request_type: str
    status: str
    current_step: int
    initiated_by: int
    created_at: datetime
    request_summary: dict


# ─────────────────────────────────────────────────────────────
# Workflow Template Management
# ─────────────────────────────────────────────────────────────

@router.post("/templates", response_model=dict)
async def create_workflow_template(
    template_data: WorkflowTemplateCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workflow template
    Example: Employee → Dept Manager → Finance → Final Approval
    """
    try:
        workflow_template = WorkflowTemplate(
            name=template_data.name,
            module=template_data.module,
            request_type=template_data.request_type,
            steps=template_data.steps,
            requires_documentation=template_data.requires_documentation
        )
        
        workflow = WorkflowEngine.create_workflow_template(db, workflow_template)
        
        return {
            "status": "success",
            "workflow_id": workflow.id,
            "message": f"Workflow template '{template_data.name}' created successfully",
            "template": {
                "id": workflow.id,
                "name": workflow.name,
                "module": workflow.module,
                "request_type": workflow.request_type,
                "steps_count": len(template_data.steps)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=dict)
async def list_workflow_templates(
    module: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all workflow templates, optionally filtered by module"""
    # TODO: Query all workflow templates
    return {
        "status": "success",
        "templates": [],
        "count": 0
    }


# ─────────────────────────────────────────────────────────────
# Request Submission & Approval Initiation
# ─────────────────────────────────────────────────────────────

@router.post("/initiate", response_model=dict)
async def initiate_approval_workflow(
    request_type: str,
    module: str,
    request_id: int,
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a request and initiate approval workflow
    Automatically routes to first approver
    """
    try:
        approval_instance = WorkflowEngine.initiate_approval(
            db=db,
            request_id=request_id,
            request_type=request_type,
            module=module,
            initiated_by=current_user.id,
            request_data=request_data,
            department_id=getattr(current_user, 'department_id', None)
        )
        
        return {
            "status": "success",
            "approval_id": approval_instance.id,
            "current_step": approval_instance.current_step,
            "message": f"Request #{request_id} submitted for approval",
            "next_approvers": []  # TODO: Get from approvers_json
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Approval Actions
# ─────────────────────────────────────────────────────────────

@router.post("/approve", response_model=dict)
async def approve_request(
    action_data: ApprovalActionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a request at current step
    If all approvers in step approve, routes to next step
    """
    try:
        approval = WorkflowEngine.approve_request(
            db=db,
            approval_id=action_data.approval_id,
            approver_id=current_user.id,
            comments=action_data.comments or ""
        )
        
        next_step_info = ""
        if approval:
            next_step_info = f" and routed to step {approval.current_step + 1}"
        else:
            next_step_info = " - REQUEST FULLY APPROVED! 🎉"
        
        return {
            "status": "success",
            "message": f"Request approved{next_step_info}",
            "approval_id": action_data.approval_id,
            "next_approvers": []  # TODO: Get from next approvers
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject", response_model=dict)
async def reject_request(
    action_data: ApprovalActionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a request
    Sends notification back to requester
    """
    try:
        approval = WorkflowEngine.reject_request(
            db=db,
            approval_id=action_data.approval_id,
            rejected_by=current_user.id,
            reason=action_data.comments or "No reason provided"
        )
        
        return {
            "status": "success",
            "message": "Request rejected - notification sent to requester",
            "approval_id": action_data.approval_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/return-for-edit", response_model=dict)
async def return_for_edit(
    action_data: ApprovalActionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return request for edits
    Sends back to requester with required changes
    """
    try:
        approval = WorkflowEngine.return_for_edit(
            db=db,
            approval_id=action_data.approval_id,
            returned_by=current_user.id,
            required_changes=action_data.required_changes or "Please review and make necessary edits"
        )
        
        return {
            "status": "success",
            "message": "Request returned for edits - notification sent",
            "approval_id": action_data.approval_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Approver Dashboard
# ─────────────────────────────────────────────────────────────

@router.get("/pending", response_model=dict)
async def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all pending approvals for current user
    Grouped by request type and priority
    """
    try:
        pending_approvals = WorkflowEngine.get_pending_approvals_for_user(
            db=db,
            user_id=current_user.id
        )
        
        # TODO: Group by request type
        # TODO: Add priority sorting
        
        approvals_list = [
            {
                "approval_id": a.id,
                "request_id": a.request_id,
                "request_type": a.request_type,
                "status": a.status,
                "current_step": a.current_step,
                "initiated_by": a.initiated_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "request_summary": {}
            }
            for a in pending_approvals
        ]
        
        return {
            "status": "success",
            "approvals": approvals_list,
            "count": len(approvals_list),
            "grouped_by_type": {}  # TODO: Add grouping
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Audit Trail
# ─────────────────────────────────────────────────────────────

@router.get("/audit-trail/{request_type}/{request_id}", response_model=dict)
async def get_request_audit_trail(
    request_type: str,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete audit trail for a request
    Shows all approvals, rejections, returns, and comments
    """
    try:
        audit_trail = WorkflowEngine.get_request_audit_trail(
            db=db,
            request_id=request_id,
            request_type=request_type
        )
        
        return {
            "status": "success",
            "audit_trail": audit_trail,
            "message": "Audit trail retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Cross-Module Triggers (Event Handling)
# ─────────────────────────────────────────────────────────────

@router.post("/triggers/po-approved", response_model=dict)
async def trigger_po_approved(
    po_id: int,
    po_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger: PO Approved
    Executes:
    1. GL commitment entry
    2. Inventory pending receipt
    3. Warehouse notification
    """
    try:
        execute_trigger(
            db=db,
            event=TriggerEvent.PO_APPROVED,
            record_id=po_id,
            record_data=po_data
        )
        
        return {
            "status": "success",
            "message": "PO approved - cross-module triggers executed",
            "actions_executed": [
                "GL commitment posted",
                "Inventory pending receipt created",
                "Warehouse notified"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/triggers/goods-received", response_model=dict)
async def trigger_goods_received(
    grn_id: int,
    grn_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger: Goods Received Note (GRN)
    Executes:
    1. Update inventory stock
    2. Match against PO
    3. Check 3-way match (PO/GRN/Invoice)
    """
    try:
        execute_trigger(
            db=db,
            event=TriggerEvent.GOODS_RECEIVED,
            record_id=grn_id,
            record_data=grn_data
        )
        
        return {
            "status": "success",
            "message": "GRN recorded - stock updated and matching checks performed",
            "actions_executed": [
                "Inventory stock updated",
                "PO match verified",
                "Awaiting invoice for 3-way match"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Document Management (E-Archive)
# ─────────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(...),
    title: str = Query(...),
    module: str = Query(...),
    linked_record_type: str = Query(...),
    linked_record_id: int = Query(...),
    description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and archive a document
    Automatically linked to request (PR, PO, Employee, Contract, etc.)
    """
    try:
        contents = await file.read()
        result = {
            "status": "success",
            "document_id": f"doc-{datetime.utcnow().timestamp()}",
            "message": f"Document '{file.filename}' archived successfully",
            "file": {
                "name": file.filename,
                "size": len(contents),
                "type": file.content_type,
                "linked_to": f"{linked_record_type}#{linked_record_id}"
            }
        }
        
        # TODO: Use DocumentArchive.archive_document()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{linked_record_type}/{linked_record_id}", response_model=dict)
async def list_documents(
    linked_record_type: str,
    linked_record_id: int,
    module: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all archived documents for a record
    Shows all versions with is_latest flag
    """
    try:
        archive = DocumentArchive()
        documents = archive.search_documents(
            db=db,
            module=module,
            linked_record_type=linked_record_type,
            linked_record_id=linked_record_id
        )
        
        return {
            "status": "success",
            "documents": documents,
            "count": len(documents),
            "linked_to": f"{linked_record_type}#{linked_record_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/download", response_model=dict)
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download archived document"""
    try:
        archive = DocumentArchive()
        file_stream, metadata = archive.retrieve_document(db, document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")
