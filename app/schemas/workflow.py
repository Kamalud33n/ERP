from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RequestCreate(BaseModel):
    request_type: str
    title: str
    description: Optional[str] = None
    department: Optional[str] = None
    amount: Optional[float] = None

class ApprovalIn(BaseModel):
    action: str  # approved | rejected | commented | progressed
    comment: Optional[str] = None
    step: Optional[str] = None
    next_status: Optional[str] = None

class ApprovalOut(BaseModel):
    id: int
    request_id: int
    approver_id: int
    action: str
    comment: Optional[str]
    step: Optional[str]
    acted_at: datetime

    class Config:
        from_attributes = True

class RequestOut(BaseModel):
    id: int
    request_type: str
    title: str
    description: Optional[str]
    department: Optional[str]
    amount: Optional[float]
    status: str
    created_by: int
    created_at: datetime
    histories: List[ApprovalOut] = []

    class Config:
        from_attributes = True
