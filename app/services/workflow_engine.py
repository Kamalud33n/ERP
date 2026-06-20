"""
Workflow Engine - Multi-level Approval System
Handles dynamic routing of requests through configurable approval chains
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import ApprovalWorkflow, ApprovalInstance, User
from app.services.email_service import EmailService, EmailTemplates
from app.tasks.celery_config import send_email_task
import json


class ApprovalStatus(str, Enum):
    """Approval statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURN_FOR_EDIT = "return_for_edit"


class RequestStatus(str, Enum):
    """Request statuses"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ApprovalStep(BaseModel):
    """Single approval step in workflow"""
    order: int
    role: str
    approver_count: int = 1  # Number of approvers needed at this step
    auto_approve: bool = False  # Auto-approve if balance available
    parallel: bool = False  # All approvers in parallel or sequential
    description: str


class WorkflowTemplate(BaseModel):
    """Configurable approval workflow template"""
    name: str
    module: str  # hr, finance, procurement, etc.
    request_type: str  # leave, expense, purchase_request, etc.
    steps: List[ApprovalStep]
    requires_documentation: bool = True
    default_reviewers: Dict[str, List[str]] = {}  # role -> user_ids


class WorkflowEngine:
    """
    Manages approval workflows across all modules
    Supports:
    - Multi-level approval chains
    - Parallel & sequential approvals
    - Auto-approval based on budget/threshold
    - Request rejection & return for edit
    - Audit trail of all approvals
    """

    @staticmethod
    def create_workflow_template(
        db: Session,
        template: WorkflowTemplate
    ) -> ApprovalWorkflow:
        """Create a new workflow template"""
        workflow = ApprovalWorkflow(
            name=template.name,
            module=template.module,
            request_type=template.request_type,
            approval_chain=json.dumps([step.dict() for step in template.steps]),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def initiate_approval(
        db: Session,
        request_id: int,
        request_type: str,
        module: str,
        initiated_by: int,
        request_data: Dict[str, Any],
        department_id: Optional[int] = None
    ) -> ApprovalInstance:
        """
        Initiate approval workflow for a request
        Returns first pending approval instance
        """
        # Get workflow template
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.module == module,
            ApprovalWorkflow.request_type == request_type,
            ApprovalWorkflow.is_active == True
        ).first()

        if not workflow:
            raise ValueError(f"No workflow found for {module}.{request_type}")

        # Parse approval steps
        steps = json.loads(workflow.approval_chain)

        # Create approval instance for first step
        first_step = steps[0]
        approvers = WorkflowEngine._get_approvers_for_role(
            db=db,
            role=first_step['role'],
            department_id=department_id
        )

        if not approvers:
            raise ValueError(f"No approvers found for role: {first_step['role']}")

        approval_instance = ApprovalInstance(
            request_id=request_id,
            request_type=request_type,
            module=module,
            workflow_id=workflow.id,
            initiated_by=initiated_by,
            current_step=0,
            status=RequestStatus.PENDING_APPROVAL.value,
            approval_chain=workflow.approval_chain,
            approvers_json=json.dumps([{"user_id": a.id, "role": first_step['role']} for a in approvers]),
            request_data=json.dumps(request_data),
            created_at=datetime.utcnow()
        )
        db.add(approval_instance)
        db.commit()
        db.refresh(approval_instance)

        # Send approval notifications
        WorkflowEngine._send_approval_notifications(
            approvers=approvers,
            request_type=request_type,
            request_id=request_id,
            initiated_by_id=initiated_by,
            request_data=request_data
        )

        return approval_instance

    @staticmethod
    def approve_request(
        db: Session,
        approval_id: int,
        approver_id: int,
        comments: str = ""
    ) -> Optional[ApprovalInstance]:
        """
        Approve a request at current step
        Returns next approval instance or None if final approval
        """
        approval = db.query(ApprovalInstance).filter(
            ApprovalInstance.id == approval_id
        ).first()

        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        steps = json.loads(approval.approval_chain)
        current_step_idx = approval.current_step

        # Record approval
        approval.current_approvals = (approval.current_approvals or 0) + 1
        approval.last_approved_by = approver_id
        approval.last_approved_at = datetime.utcnow()
        approval.comments = comments

        current_step = steps[current_step_idx]

        # Check if all approvers in this step have approved
        required_approvals = current_step.get('approver_count', 1)
        if approval.current_approvals >= required_approvals:
            # Move to next step
            if current_step_idx + 1 < len(steps):
                next_step = steps[current_step_idx + 1]
                approval.current_step += 1
                approval.current_approvals = 0

                # Get next approvers
                next_approvers = WorkflowEngine._get_approvers_for_role(
                    db=db,
                    role=next_step['role'],
                    department_id=None  # TODO: get from request context
                )

                approval.approvers_json = json.dumps([
                    {"user_id": a.id, "role": next_step['role']} for a in next_approvers
                ])

                # Send notifications to next approvers
                request_data = json.loads(approval.request_data) if approval.request_data else {}
                WorkflowEngine._send_approval_notifications(
                    approvers=next_approvers,
                    request_type=approval.request_type,
                    request_id=approval.request_id,
                    initiated_by_id=approval.initiated_by,
                    request_data=request_data,
                    message=f"Request from step {current_step_idx + 1}: {comments}"
                )

                db.commit()
                db.refresh(approval)
                return approval
            else:
                # Final approval complete
                approval.status = RequestStatus.APPROVED.value
                approval.approved_at = datetime.utcnow()

                # Send approval decision notification
                requester = db.query(User).filter(User.id == approval.initiated_by).first()
                if requester:
                    send_email_task.delay(
                        to_email=requester.email,
                        subject=f"✅ Your {approval.request_type} has been approved",
                        html_content=EmailTemplates.approval_decision(
                            request_type=approval.request_type,
                            request_id=approval.request_id,
                            status="approved",
                            approved_by=f"User {approver_id}"
                        )
                    )

                db.commit()
                db.refresh(approval)
                return None  # No next approval

        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def reject_request(
        db: Session,
        approval_id: int,
        rejected_by: int,
        reason: str
    ) -> ApprovalInstance:
        """Reject a request (returns to step 0)"""
        approval = db.query(ApprovalInstance).filter(
            ApprovalInstance.id == approval_id
        ).first()

        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        approval.status = RequestStatus.REJECTED.value
        approval.rejected_by = rejected_by
        approval.rejected_at = datetime.utcnow()
        approval.rejection_reason = reason

        # Send rejection notification
        requester = db.query(User).filter(User.id == approval.initiated_by).first()
        if requester:
            send_email_task.delay(
                to_email=requester.email,
                subject=f"❌ Your {approval.request_type} was rejected",
                html_content=EmailTemplates.approval_decision(
                    request_type=approval.request_type,
                    request_id=approval.request_id,
                    status="rejected",
                    reason=reason
                )
            )

        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def return_for_edit(
        db: Session,
        approval_id: int,
        returned_by: int,
        required_changes: str
    ) -> ApprovalInstance:
        """Return request for edit (goes back to submitter)"""
        approval = db.query(ApprovalInstance).filter(
            ApprovalInstance.id == approval_id
        ).first()

        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        approval.status = RequestStatus.RETURN_FOR_EDIT.value
        approval.current_step = 0
        approval.returned_for_edit_at = datetime.utcnow()
        approval.returned_for_edit_by = returned_by
        approval.return_reason = required_changes

        # Send return notification
        requester = db.query(User).filter(User.id == approval.initiated_by).first()
        if requester:
            send_email_task.delay(
                to_email=requester.email,
                subject=f"📝 Your {approval.request_type} needs edits",
                html_content=f"""
                <h2>Request #{approval.request_id} - Changes Required</h2>
                <p>Please make the following changes:</p>
                <p><strong>{required_changes}</strong></p>
                <p><a href="http://localhost:3000/requests/{approval.request_id}">View Request</a></p>
                """
            )

        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def auto_approve_if_eligible(
        db: Session,
        approval_id: int,
        request_amount: float,
        approver_limit: float
    ) -> bool:
        """Auto-approve if request is below approver's limit"""
        if request_amount <= approver_limit:
            approval = db.query(ApprovalInstance).filter(
                ApprovalInstance.id == approval_id
            ).first()

            if approval:
                approval.auto_approved = True
                approval.auto_approved_at = datetime.utcnow()
                # Proceed to next step
                WorkflowEngine.approve_request(db, approval_id, 0, comments="Auto-approved")
                return True

        return False

    @staticmethod
    def get_pending_approvals_for_user(
        db: Session,
        user_id: int
    ) -> List[ApprovalInstance]:
        """Get all pending approvals for a specific user"""
        approvals = db.query(ApprovalInstance).filter(
            ApprovalInstance.status == RequestStatus.PENDING_APPROVAL.value
        ).all()

        # Filter those where user is in approvers
        pending = []
        for approval in approvals:
            approvers = json.loads(approval.approvers_json or "[]")
            if any(a.get("user_id") == user_id for a in approvers):
                pending.append(approval)

        return pending

    @staticmethod
    def get_request_audit_trail(
        db: Session,
        request_id: int,
        request_type: str
    ) -> Dict[str, Any]:
        """Get complete audit trail for a request"""
        approval = db.query(ApprovalInstance).filter(
            ApprovalInstance.request_id == request_id,
            ApprovalInstance.request_type == request_type
        ).first()

        if not approval:
            return {}

        audit_trail = {
            "request_id": request_id,
            "request_type": request_type,
            "status": approval.status,
            "initiated_at": approval.created_at.isoformat() if approval.created_at else None,
            "initiated_by": approval.initiated_by,
            "current_step": approval.current_step,
            "approval_chain": json.loads(approval.approval_chain) if approval.approval_chain else [],
            "approvals": []
        }

        # Build approval history
        if approval.last_approved_by:
            audit_trail["approvals"].append({
                "step": approval.current_step - 1,
                "approved_by": approval.last_approved_by,
                "approved_at": approval.last_approved_at.isoformat() if approval.last_approved_at else None,
                "comments": approval.comments
            })

        if approval.status == RequestStatus.REJECTED.value:
            audit_trail["rejection"] = {
                "rejected_by": approval.rejected_by,
                "rejected_at": approval.rejected_at.isoformat() if approval.rejected_at else None,
                "reason": approval.rejection_reason
            }

        return audit_trail

    @staticmethod
    def _get_approvers_for_role(
        db: Session,
        role: str,
        department_id: Optional[int] = None
    ) -> List[User]:
        """Get users with a specific role (optionally filtered by department)"""
        from app.models import Role
        query = db.query(User).join(Role).filter(Role.name == role)

        if department_id:
            query = query.filter(User.department_id == department_id)

        return query.all()

    @staticmethod
    def _send_approval_notifications(
        approvers: List[User],
        request_type: str,
        request_id: int,
        initiated_by_id: int,
        request_data: Dict[str, Any],
        message: str = ""
    ):
        """Send approval notifications to approvers"""
        for approver in approvers:
            send_email_task.delay(
                to_email=approver.email,
                subject=f"⚠️ Action Required: {request_type} #{request_id}",
                html_content=EmailTemplates.approval_notification(
                    approver_name=approver.first_name or "Approver",
                    request_type=request_type,
                    request_id=request_id,
                    requested_by=f"Employee {initiated_by_id}",
                    request_details=request_data,
                    action_url=f"http://localhost:3000/approvals/{request_id}"
                )
            )
