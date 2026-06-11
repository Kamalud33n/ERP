from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Item ───────────────────────────────────────────────
class ItemCreate(BaseModel):
    name:          str
    sku:           str
    category:      str
    unit:          str
    description:   Optional[str] = None
    min_stock:     Optional[float] = 0.0
    unit_price:    Optional[float] = 0.0

class ItemUpdate(BaseModel):
    name:          Optional[str] = None
    category:      Optional[str] = None
    unit:          Optional[str] = None
    description:   Optional[str] = None
    min_stock:     Optional[float] = None
    unit_price:    Optional[float] = None
    is_active:     Optional[bool] = None

class ItemOut(BaseModel):
    id:            int
    name:          str
    sku:           str
    category:      str
    unit:          str
    description:   Optional[str]
    current_stock: float
    min_stock:     float
    unit_price:    float
    is_active:     bool
    created_by:    int
    created_at:    datetime

    class Config:
        from_attributes = True


# ── Stock Movement ─────────────────────────────────────
class StockMovementCreate(BaseModel):
    item_id:   int
    type:      str        # in | out | adjustment
    quantity:  float
    reference: Optional[str] = None
    note:      Optional[str] = None

class StockMovementOut(BaseModel):
    id:         int
    item_id:    int
    type:       str
    quantity:   float
    reference:  Optional[str]
    note:       Optional[str]
    done_by:    int
    created_at: datetime

    class Config:
        from_attributes = True