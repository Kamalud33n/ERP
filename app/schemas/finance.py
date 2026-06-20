from pydantic import BaseModel
from typing import Optional, List
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


# ── Journal Entry ──────────────────────────────────────
class JournalLineCreate(BaseModel):
    account_type: str
    description:  Optional[str] = None
    debit:        Optional[float] = 0.0
    credit:       Optional[float] = 0.0

class JournalLineOut(BaseModel):
    id:           int
    entry_id:     int
    account_type: str
    description:  Optional[str]
    debit:        float
    credit:       float

    class Config:
        from_attributes = True

class JournalEntryCreate(BaseModel):
    date:        date
    description: str
    reference:   Optional[str] = None
    lines:       List[JournalLineCreate]

class JournalEntryOut(BaseModel):
    id:           int
    entry_number: str
    date:         date
    description:  str
    reference:    Optional[str]
    status:       str
    created_by:   int
    created_at:   datetime
    lines:        List[JournalLineOut]

    class Config:
        from_attributes = True


# ── Journal Entry ──────────────────────────────────────
class JournalLineCreate(BaseModel):
    account_type: str
    description:  Optional[str] = None
    debit:        Optional[float] = 0.0
    credit:       Optional[float] = 0.0

class JournalLineOut(BaseModel):
    id:           int
    entry_id:     int
    account_type: str
    description:  Optional[str]
    debit:        float
    credit:       float

    class Config:
        from_attributes = True

class JournalEntryCreate(BaseModel):
    date:        date
    description: str
    reference:   Optional[str] = None
    lines:       List[JournalLineCreate]

class JournalEntryOut(BaseModel):
    id:           int
    entry_number: str
    date:         date
    description:  str
    reference:    Optional[str]
    status:       str
    created_by:   int
    created_at:   datetime
    lines:        List[JournalLineOut] = []

    class Config:
        from_attributes = True


# ── Chart of Accounts ──────────────────────────────────
class COACreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str  # asset | liability | equity | income | expense
    parent_id:    Optional[int] = None
    description:  Optional[str] = None

class COAUpdate(BaseModel):
    account_name: Optional[str] = None
    description:  Optional[str] = None
    is_active:    Optional[bool] = None

class COAOut(BaseModel):
    id:           int
    account_code: str
    account_name: str
    account_type: str
    parent_id:    Optional[int]
    description:  Optional[str]
    is_active:    bool
    created_by:   int
    created_at:   datetime

    class Config:
        from_attributes = True


# ── Accounts Payable ───────────────────────────────────
class VendorBillCreate(BaseModel):
    vendor_id:   int
    bill_date:   date
    due_date:    Optional[date] = None
    amount:      float
    description: Optional[str] = None

class VendorBillUpdate(BaseModel):
    due_date:    Optional[date] = None
    status:      Optional[str] = None
    description: Optional[str] = None

class VendorBillOut(BaseModel):
    id:           int
    vendor_id:    int
    bill_number:  str
    bill_date:    date
    due_date:     Optional[date]
    amount:       float
    paid_amount:  float
    outstanding:  float
    description:  Optional[str]
    status:       str
    created_by:   int
    created_at:   datetime

    class Config:
        from_attributes = True


class VendorPaymentCreate(BaseModel):
    bill_id:        int
    payment_date:   date
    amount:         float
    payment_method: Optional[str] = "bank_transfer"
    reference:      Optional[str] = None
    notes:          Optional[str] = None

class VendorPaymentOut(BaseModel):
    id:             int
    bill_id:        int
    vendor_id:      int
    payment_number: str
    payment_date:   date
    amount:         float
    payment_method: str
    reference:      Optional[str]
    notes:          Optional[str]
    created_by:     int
    created_at:     datetime

    class Config:
        from_attributes = True