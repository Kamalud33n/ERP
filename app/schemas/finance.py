from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ExpenseCreate(BaseModel):
    title:       str
    amount:      float
    category:    str
    department:  str
    date:        date
    description: Optional[str] = None

class ExpenseUpdate(BaseModel):
    status:      str  # approved | rejected
    approved_by: int

class ExpenseOut(BaseModel):
    id:           int
    title:        str
    amount:       float
    category:     str
    department:   str
    date:         date
    description:  Optional[str]
    status:       str
    submitted_by: int
    approved_by:  Optional[int]
    created_at:   datetime

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    department: str
    category:   str
    amount:     float
    month:      str

class BudgetOut(BaseModel):
    id:         int
    department: str
    category:   str
    amount:     float
    spent:      float
    month:      str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class GLCreate(BaseModel):
    date:         date
    description:  str
    debit:        Optional[float] = 0.0
    credit:       Optional[float] = 0.0
    account_type: str
    reference:    Optional[str] = None

class GLOut(BaseModel):
    id:           int
    date:         date
    description:  str
    debit:        float
    credit:       float
    balance:      float
    account_type: str
    reference:    Optional[str]
    created_by:   int
    created_at:   datetime

    class Config:
        from_attributes = True