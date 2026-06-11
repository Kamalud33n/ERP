from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


# ── Asset ──────────────────────────────────────────────
class AssetCreate(BaseModel):
    name:               str
    category:           str
    serial_number:      Optional[str] = None
    location:           Optional[str] = None
    department:         Optional[str] = None
    purchase_date:      Optional[date] = None
    purchase_price:     Optional[float] = 0.0
    depreciation_rate:  Optional[float] = 0.0
    description:        Optional[str] = None
    assigned_to:        Optional[int] = None

class AssetUpdate(BaseModel):
    name:               Optional[str] = None
    category:           Optional[str] = None
    serial_number:      Optional[str] = None
    location:           Optional[str] = None
    department:         Optional[str] = None
    status:             Optional[str] = None
    depreciation_rate:  Optional[float] = None
    current_value:      Optional[float] = None
    assigned_to:        Optional[int] = None

class AssetOut(BaseModel):
    id:                 int
    name:               str
    asset_code:         str
    category:           str
    serial_number:      Optional[str]
    location:           Optional[str]
    department:         Optional[str]
    purchase_date:      Optional[date]
    purchase_price:     float
    current_value:      float
    depreciation_rate:  float
    status:             str
    description:        Optional[str]
    assigned_to:        Optional[int]
    created_by:         int
    created_at:         datetime

    class Config:
        from_attributes = True


# ── Maintenance Log ────────────────────────────────────
class MaintenanceCreate(BaseModel):
    asset_id:           int
    type:               str
    description:        str
    cost:               Optional[float] = 0.0
    maintenance_date:   date
    next_due_date:      Optional[date] = None
    status:             Optional[str] = "completed"

class MaintenanceOut(BaseModel):
    id:                 int
    asset_id:           int
    type:               str
    description:        str
    cost:               float
    maintenance_date:   date
    next_due_date:      Optional[date]
    status:             str
    done_by:            int
    created_at:         datetime

    class Config:
        from_attributes = True