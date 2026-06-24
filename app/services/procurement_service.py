from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.procurement import Vendor, PurchaseRequest, PurchaseOrder
from app.schemas.procurement import VendorCreate, VendorUpdate, PRCreate, PRApprove, POCreate, POUpdate
from app.services.notification_service import create_notification


# ── Vendor ─────────────────────────────────────────────
def create_vendor(db: Session, data: VendorCreate, created_by: int) -> Vendor:
    vendor = Vendor(name=data.name, email=data.email, phone=data.phone,
                    address=data.address, category=data.category, created_by=created_by)
    db.add(vendor); db.commit(); db.refresh(vendor)
    return vendor

def get_all_vendors(db: Session):
    return db.query(Vendor).all()

def get_vendor_by_id(db: Session, vendor_id: int) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

def update_vendor(db: Session, vendor_id: int, data: VendorUpdate) -> Vendor:
    vendor = get_vendor_by_id(db, vendor_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
    db.commit(); db.refresh(vendor)
    return vendor

def delete_vendor(db: Session, vendor_id: int):
    vendor = get_vendor_by_id(db, vendor_id)
    db.delete(vendor); db.commit()
    return {"message": "Vendor deleted"}


# ── Purchase Request ───────────────────────────────────
def create_pr(db: Session, data: PRCreate, requested_by: int) -> PurchaseRequest:
    pr = PurchaseRequest(
        title=data.title, description=data.description, quantity=data.quantity,
        estimated_cost=data.estimated_cost, department=data.department,
        priority=data.priority, requested_by=requested_by
    )
    db.add(pr); db.commit(); db.refresh(pr)

    # Notify HR — new PR waiting
    from app.models.user import User
    hr_users = db.query(User).filter(
        User.role == "hr_manager", User.is_active == True
    ).all()
    for u in hr_users:
        create_notification(
            db=db, user_id=u.id,
            title="New Purchase Request",
            message=(
                f"A new purchase request '{data.title}' (Est: {data.estimated_cost:.2f}) "
                f"from dept '{data.department}' is pending your approval."
            ),
            module="procurement", notif_type="info",
        )
    return pr

def get_all_prs(db: Session):
    return db.query(PurchaseRequest).order_by(PurchaseRequest.created_at.desc()).all()

def get_pr_by_id(db: Session, pr_id: int) -> PurchaseRequest:
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Request not found")
    return pr

def get_prs_by_user(db: Session, user_id: int):
    return db.query(PurchaseRequest).filter(
        PurchaseRequest.requested_by == user_id
    ).order_by(PurchaseRequest.created_at.desc()).all()


def approve_pr(db: Session, pr_id: int, data: PRApprove, approved_by_user) -> dict:
    pr   = get_pr_by_id(db, pr_id)
    role = approved_by_user.role

    # ── Rejection ──────────────────────────────────────
    if data.status == "rejected":
        pr.status = "rejected"
        db.commit(); db.refresh(pr)
        create_notification(
            db=db, user_id=pr.requested_by,
            title="Purchase Request Rejected",
            message=(
                f"Your purchase request '{pr.title}' (PR #{pr.id}) "
                f"has been rejected by {approved_by_user.username} ({role})."
            ),
            module="procurement", notif_type="alert",
        )
        return {"pr": pr, "po": None}

    # ── HR Approval ────────────────────────────────────
    if role == "hr_manager":
        if pr.status != "pending":
            raise HTTPException(status_code=400, detail="HR can only approve pending requests")
        pr.status         = "hr_approved"
        pr.hr_approved_by = approved_by_user.id
        pr.hr_approved_at = datetime.utcnow()
        db.commit(); db.refresh(pr)

        # Notify requester
        create_notification(
            db=db, user_id=pr.requested_by,
            title="Purchase Request Update",
            message=(
                f"Your PR '{pr.title}' (PR #{pr.id}) passed HR review. "
                f"Awaiting Finance approval."
            ),
            module="procurement", notif_type="info",
        )
        # Notify Finance — their turn
        from app.models.user import User
        finance_users = db.query(User).filter(
            User.role == "finance", User.is_active == True
        ).all()
        for u in finance_users:
            create_notification(
                db=db, user_id=u.id,
                title="Purchase Request Awaiting Finance Approval",
                message=(
                    f"PR '{pr.title}' (PR #{pr.id}, Est: {pr.estimated_cost:.2f}) "
                    f"has passed HR review and is pending your approval."
                ),
                module="procurement", notif_type="info",
            )
        return {"pr": pr, "po": None}

    # ── Finance Approval ───────────────────────────────
    elif role == "finance":
        if pr.status != "hr_approved":
            raise HTTPException(status_code=400, detail="Finance can only approve HR approved requests")
        pr.status          = "finance_approved"
        pr.fin_approved_by = approved_by_user.id
        pr.fin_approved_at = datetime.utcnow()
        db.commit(); db.refresh(pr)

        # Notify requester
        create_notification(
            db=db, user_id=pr.requested_by,
            title="Purchase Request Update",
            message=(
                f"Your PR '{pr.title}' (PR #{pr.id}) passed Finance review. "
                f"Awaiting final approval."
            ),
            module="procurement", notif_type="info",
        )
        # Notify Admin — final step
        from app.models.user import User
        admin_users = db.query(User).filter(
            User.role == "admin", User.is_active == True
        ).all()
        for u in admin_users:
            create_notification(
                db=db, user_id=u.id,
                title="Purchase Request Awaiting Final Approval",
                message=(
                    f"PR '{pr.title}' (PR #{pr.id}, Est: {pr.estimated_cost:.2f}) "
                    f"has passed Finance review and requires your final approval."
                ),
                module="procurement", notif_type="info",
            )
        return {"pr": pr, "po": None}

    # ── Admin Final Approval → Auto PO Create ──────────
    elif role == "admin":
        if pr.status != "finance_approved":
            raise HTTPException(
                status_code=400,
                detail="Admin can only give final approval after Finance"
            )
        if not data.vendor_id:
            raise HTTPException(
                status_code=400,
                detail="vendor_id is required for final approval to auto-create PO"
            )

        unit_price = data.unit_price or pr.estimated_cost

        pr.status            = "final_approved"
        pr.final_approved_by = approved_by_user.id
        pr.final_approved_at = datetime.utcnow()
        db.commit(); db.refresh(pr)

        # ── Auto PO Create ─────────────────────────────
        existing_po = db.query(PurchaseOrder).filter(
            PurchaseOrder.purchase_request_id == pr.id
        ).first()

        po = None
        if not existing_po:
            count     = db.query(PurchaseOrder).count()
            po_number = f"PO-{datetime.now().year}-{str(count + 1).zfill(4)}"

            po = PurchaseOrder(
                purchase_request_id = pr.id,
                vendor_id           = data.vendor_id,
                po_number           = po_number,
                quantity            = pr.quantity,
                unit_price          = unit_price,
                total_amount        = pr.quantity * unit_price,
                delivery_date       = data.delivery_date,
                notes               = data.notes,
                created_by          = approved_by_user.id,
            )
            db.add(po); db.commit(); db.refresh(po)

            # GL entry — PO commitment (only here, not in create_po)
            from app.services.finance_service import post_gl_entry
            post_gl_entry(
                db,
                entry_date   = datetime.now().date(),
                description  = f"Purchase Order {po_number} committed",
                account_type = "liability",
                credit       = po.total_amount,
                reference    = po_number,
                created_by   = approved_by_user.id,
            )

            create_notification(
                db=db, user_id=pr.requested_by,
                title="Purchase Order Created Automatically",
                message=(
                    f"Your PR '{pr.title}' is fully approved! "
                    f"PO {po_number} has been automatically created. "
                    f"Total: {po.total_amount:.2f}."
                ),
                module="procurement", notif_type="success",
            )
        else:
            po = existing_po
            create_notification(
                db=db, user_id=pr.requested_by,
                title="Purchase Request Finally Approved",
                message=(
                    f"Your PR '{pr.title}' (PR #{pr.id}) "
                    f"has received final approval!"
                ),
                module="procurement", notif_type="success",
            )

        return {"pr": pr, "po": po}

    else:
        raise HTTPException(status_code=403, detail="You don't have permission to approve")


# ── Purchase Order ─────────────────────────────────────
def create_po(db: Session, data: POCreate, created_by: int) -> PurchaseOrder:
    pr = get_pr_by_id(db, data.purchase_request_id)
    if pr.status != "final_approved":
        raise HTTPException(status_code=400, detail="PO can only be created for final approved requests")
    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_request_id == data.purchase_request_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="PO already exists for this request")

    count     = db.query(PurchaseOrder).count()
    po_number = f"PO-{datetime.now().year}-{str(count + 1).zfill(4)}"
    po = PurchaseOrder(
        purchase_request_id = data.purchase_request_id,
        vendor_id           = data.vendor_id,
        po_number           = po_number,
        quantity            = data.quantity,
        unit_price          = data.unit_price,
        total_amount        = data.quantity * data.unit_price,
        delivery_date       = data.delivery_date,
        notes               = data.notes,
        created_by          = created_by,
    )
    db.add(po); db.commit(); db.refresh(po)

    # GL posting REMOVED — vendor bill creation handles actual liability
    # approve_pr (admin) already posts commitment GL when auto-creating PO
    # Double posting avoided ✅

    create_notification(
        db=db, user_id=pr.requested_by,
        title="Purchase Order Created",
        message=(
            f"A Purchase Order ({po_number}) has been raised "
            f"for your approved PR '{pr.title}'. "
            f"Total: {po.total_amount:.2f}."
        ),
        module="procurement", notif_type="success",
    )
    return po


def get_all_pos(db: Session):
    return db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()

def get_po_by_id(db: Session, po_id: int) -> PurchaseOrder:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po

def update_po_status(db: Session, po_id: int, data: POUpdate) -> PurchaseOrder:
    po = get_po_by_id(db, po_id)
    po.status = data.status
    db.commit(); db.refresh(po)
    return po

def get_procurement_summary(db: Session) -> dict:
    return {
        "total_prs":      db.query(PurchaseRequest).count(),
        "pending_prs":    db.query(PurchaseRequest).filter(PurchaseRequest.status == "pending").count(),
        "approved_prs":   db.query(PurchaseRequest).filter(PurchaseRequest.status == "final_approved").count(),
        "rejected_prs":   db.query(PurchaseRequest).filter(PurchaseRequest.status == "rejected").count(),
        "total_pos":      db.query(PurchaseOrder).count(),
        "total_po_value": round(sum(po.total_amount for po in db.query(PurchaseOrder).all()), 2),
        "total_vendors":  db.query(Vendor).filter(Vendor.status == "active").count(),
    }