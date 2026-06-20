from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ApprovalWorkflow(Base):
    """Master workflow template for each request type"""
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    module = Column(String(100), nullable=False)  # hr, finance, procurement, inventory, assets
    request_type = Column(String(100), nullable=False)  # leave, expense, purchase_request, etc.
    approval_chain = Column(Text, nullable=False)  # JSON array of steps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    instances = relationship("ApprovalInstance", back_populates="workflow", cascade="all, delete-orphan")


class ApprovalInstance(Base):
    """Instance of a request going through approval workflow"""
    __tablename__ = "approval_instances"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, nullable=False)  # ID of the actual request (PR, expense, leave, etc.)
    request_type = Column(String(100), nullable=False)  # leave, expense, purchase_request, etc.
    module = Column(String(100), nullable=False)  # hr, finance, procurement, etc.
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    
    # Tracking
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who submitted the request
    status = Column(String(50), default="pending_approval")  # pending_approval, approved, rejected, return_for_edit
    
    # Approval chain state
    current_step = Column(Integer, default=0)  # Which step we're on (0-indexed)
    current_approvals = Column(Integer, default=0)  # How many approvals at this step
    approval_chain = Column(Text, nullable=False)  # JSON copy of approval steps
    approvers_json = Column(Text, nullable=True)  # JSON array of {user_id, role} for current step
    
    # Approval tracking
    last_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_approved_at = Column(DateTime, nullable=True)
    auto_approved = Column(Boolean, default=False)
    comments = Column(Text, nullable=True)
    
    # Rejection tracking
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Return for edit tracking
    returned_for_edit_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    returned_for_edit_at = Column(DateTime, nullable=True)
    return_reason = Column(Text, nullable=True)
    
    # Final approval
    approved_at = Column(DateTime, nullable=True)
    
    # Request data snapshot
    request_data = Column(Text, nullable=True)  # JSON of original request data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    workflow = relationship("ApprovalWorkflow", back_populates="instances")


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    steps = relationship("WorkflowStep", back_populates="template", order_by="WorkflowStep.sequence", cascade="all, delete-orphan")

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False)
    name = Column(String(200), nullable=False)
    sequence = Column(Integer, default=1)
    approver_role = Column(String(100), nullable=True)  # role name or special token like 'department_manager'
    approver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    auto_approve = Column(Boolean, default=False)  # if true, system auto-approves and moves on
    is_final = Column(Boolean, default=False)

    template = relationship("WorkflowTemplate", back_populates="steps")
