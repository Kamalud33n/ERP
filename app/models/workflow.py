from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(100), nullable=False)  # leave | purchase | expense | asset
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    amount = Column(Float, nullable=True)
    status = Column(String(50), default="pending")  # pending | in_progress | approved | rejected | cancelled
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=True)
    current_step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    histories = relationship("ApprovalHistory", back_populates="request", cascade="all, delete-orphan")
    # relationships to config (optional)
    template = relationship("WorkflowTemplate", backref="requests")

class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # approved | rejected | commented | progressed
    comment = Column(Text, nullable=True)
    step = Column(String(100), nullable=True)
    acted_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", back_populates="histories")
