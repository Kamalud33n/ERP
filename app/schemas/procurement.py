from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# ── Vendor ─────────────────────────────────────────────
class VendorCreate(BaseModel):
    name:     str
    email:    Optional[str] = None
    phone:    Optional[str] = None
    address:  Optional[str] = None
    category: Optional[str] = None

class VendorUpdate(BaseModel):
    name:     Optional[str] = None
    email:    Optional[str] = None
    phone:    Optional[str] = None
    address:  Optional[str] = None
    category: Optional[str] = None
    status:   Optional[str] = None

class VendorOut(BaseModel):
    id:         int
    name:       str
    email:      Optional[str]
    phone:      Optional[str]
    address:    Optional[str]
    category:   Optional[str]
    status:     str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Purchase Request ───────────────────────────────────
class PRCreate(BaseModel):
    title:          str
    description:    Optional[str] = None
    quantity:       int
    estimated_cost: float
    department:     str
    priority:       Optional[str] = "medium"

class PRApprove(BaseModel):
    status:    str            # hr_approved | finance_approved | final_approved | rejected
    vendor_id: Optional[int] = None   # Admin final approve பண்ணும்போது vendor select பண்ணணும்
    unit_price: Optional[float] = None  # PO auto create-க்கு வேணும்
    delivery_date: Optional[date] = None
    notes:     Optional[str] = None

class PROut(BaseModel):
    id:                int
    title:             str
    description:       Optional[str]
    quantity:          int
    estimated_cost:    float
    department:        str
    priority:          str
    status:            str
    requested_by:      int
    hr_approved_by:    Optional[int]
    fin_approved_by:   Optional[int]
    final_approved_by: Optional[int]
    created_at:        datetime

    class Config:
        from_attributes = True


# ── Purchase Order ─────────────────────────────────────
class POCreate(BaseModel):
    purchase_request_id: int
    vendor_id:           int
    quantity:            int
    unit_price:          float
    delivery_date:       Optional[date]  = None
    notes:               Optional[str]   = None

class POUpdate(BaseModel):
    status: str  # pending | delivered | cancelled

class POOut(BaseModel):
    id:                  int
    purchase_request_id: int
    vendor_id:           int
    po_number:           str
    quantity:            int
    unit_price:          float
    total_amount:        float
    delivery_date:       Optional[date]
    status:              str
    notes:               Optional[str]
    created_by:          int
    created_at:          datetime

    class Config:
        from_attributes = True