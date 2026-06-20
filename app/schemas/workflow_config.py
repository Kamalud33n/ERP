from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StepCreate(BaseModel):
    name: str
    sequence: int
    approver_role: Optional[str] = None
    approver_user_id: Optional[int] = None
    auto_approve: Optional[bool] = False
    is_final: Optional[bool] = False

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[StepCreate] = []

class StepOut(BaseModel):
    id: int
    template_id: int
    name: str
    sequence: int
    approver_role: Optional[str]
    approver_user_id: Optional[int]
    auto_approve: bool
    is_final: bool

    class Config:
        from_attributes = True

class TemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    steps: List[StepOut] = []

    class Config:
        from_attributes = True
