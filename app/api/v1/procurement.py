from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_finance, get_admin
from app.schemas.procurement import (
    VendorCreate, VendorUpdate, VendorOut,
    PRCreate, PRApprove, PROut,
    POCreate, POUpdate, POOut
)
from app.services.procurement_service import (
    create_vendor, get_all_vendors, get_vendor_by_id, update_vendor, delete_vendor,
    create_pr, get_all_prs, get_pr_by_id, get_prs_by_user, approve_pr,
    create_po, get_all_pos, get_po_by_id, update_po_status,
    get_procurement_summary
)

router = APIRouter()


# ── Vendor ─────────────────────────────────────────────

@router.post("/vendor", response_model=VendorOut)
def add_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_finance)
):
    return create_vendor(db, data, current_user.id)


@router.get("/vendor", response_model=List[VendorOut])
def all_vendors(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_all_vendors(db)


@router.put("/vendor/{vendor_id}", response_model=VendorOut)
def edit_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_finance)
):
    return update_vendor(db, vendor_id, data)


@router.delete("/vendor/{vendor_id}")
def remove_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin)
):
    return delete_vendor(db, vendor_id)


# ── Purchase Request ───────────────────────────────────

# Any logged in user → PR create
@router.post("/pr", response_model=PROut)
def submit_pr(
    data: PRCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_pr(db, data, current_user.id)


# ⚠️ /pr/me MUST be BEFORE /pr/{pr_id}
@router.get("/pr/me", response_model=List[PROut])
def my_prs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_prs_by_user(db, current_user.id)


# HR + Finance + Admin → all PRs
# Employee → own PRs மட்டும்
@router.get("/pr", response_model=List[PROut])
def all_prs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "employee":
        return get_prs_by_user(db, current_user.id)
    return get_all_prs(db)


# FIX: response_model=PROut → dict (auto PO return பண்றோம்)
@router.put("/pr/{pr_id}")
def approve_reject_pr(
    pr_id: int,
    data: PRApprove,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = approve_pr(db, pr_id, data, current_user)
    # result = {"pr": PurchaseRequest, "po": PurchaseOrder or None}
    response = {
        "message": "Action completed successfully",
        "pr":      result["pr"],
        "po":      result["po"],  # Auto-created PO or None
    }
    return response


# ── Purchase Order ─────────────────────────────────────

# Admin only → Manual PO create (if needed)
@router.post("/po", response_model=POOut)
def create_purchase_order(
    data: POCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin)
):
    return create_po(db, data, current_user.id)


# ⚠️ /po static paths BEFORE /{po_id}
# HR + Finance + Admin → all POs
@router.get("/po", response_model=List[POOut])
def all_pos(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "employee":
        raise HTTPException(status_code=403, detail="Access denied")
    return get_all_pos(db)


@router.get("/po/{po_id}", response_model=POOut)
def get_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "employee":
        raise HTTPException(status_code=403, detail="Access denied")
    return get_po_by_id(db, po_id)


# Finance/Admin → update PO status
@router.put("/po/{po_id}", response_model=POOut)
def update_po(
    po_id: int,
    data: POUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_finance)
):
    return update_po_status(db, po_id, data)


# ── Summary ────────────────────────────────────────────

@router.get("/summary")
def procurement_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "employee":
        raise HTTPException(status_code=403, detail="Access denied")
    return get_procurement_summary(db)