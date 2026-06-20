from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date
from app.models.asset import Asset, MaintenanceLog
from app.schemas.asset import AssetCreate, AssetUpdate, MaintenanceCreate


# ── Asset ──────────────────────────────────────────────
def create_asset(db: Session, data: AssetCreate, created_by: int) -> Asset:
    count      = db.query(Asset).count()
    asset_code = f"AST-{datetime.now().year}-{str(count + 1).zfill(4)}"

    asset = Asset(
        name              = data.name,
        asset_code        = asset_code,
        category          = data.category,
        serial_number     = data.serial_number,
        location          = data.location,
        department        = data.department,
        purchase_date     = data.purchase_date,
        purchase_price    = data.purchase_price,
        current_value     = data.purchase_price,
        depreciation_rate = data.depreciation_rate,
        description       = data.description,
        assigned_to       = data.assigned_to,
        created_by        = created_by
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Auto-post to GL: asset purchase increases fixed assets
    if data.purchase_price and data.purchase_price > 0:
        from app.services.finance_service import post_gl_entry
        post_gl_entry(
            db, entry_date=data.purchase_date or date.today(),
            description=f"Asset Purchase - {asset_code} - {data.name}",
            account_type="asset", debit=data.purchase_price,
            reference=asset_code, created_by=created_by
        )
    return asset

def get_all_assets(db: Session):
    return db.query(Asset).all()

def get_assets_by_employee(db: Session, employee_id: int):
    return db.query(Asset).filter(Asset.assigned_to == employee_id).all()

def get_asset_by_id(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

def update_asset(db: Session, asset_id: int, data: AssetUpdate) -> Asset:
    asset = get_asset_by_id(db, asset_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset

def delete_asset(db: Session, asset_id: int):
    asset = get_asset_by_id(db, asset_id)
    asset.status = "disposed"
    db.commit()
    return {"message": "Asset marked as disposed"}

def calculate_depreciation(db: Session, asset_id: int) -> dict:
    asset = get_asset_by_id(db, asset_id)
    if not asset.purchase_date or asset.depreciation_rate == 0:
        return {"message": "No depreciation data", "current_value": asset.current_value}

    years = (date.today() - asset.purchase_date).days / 365
    depreciated = asset.purchase_price * (asset.depreciation_rate / 100) * years
    current_value = max(0, asset.purchase_price - depreciated)

    # Only post the NEW depreciation since the last time this ran, so calling
    # this repeatedly (e.g. every dashboard load) doesn't double/triple-post
    # the same depreciation to the ledger.
    delta = round(asset.current_value - current_value, 2)

    asset.current_value = round(current_value, 2)
    db.commit()

    if delta > 0:
        from app.services.finance_service import post_gl_entry
        ref = f"DEPR-{asset.asset_code}-{date.today()}"
        post_gl_entry(
            db, entry_date=date.today(),
            description=f"Depreciation Expense - {asset.asset_code}",
            account_type="expense", debit=delta,
            reference=ref, created_by=asset.created_by
        )
        post_gl_entry(
            db, entry_date=date.today(),
            description=f"Accumulated Depreciation - {asset.asset_code}",
            account_type="asset", credit=delta,
            reference=ref, created_by=asset.created_by
        )

    return {
        "asset_id":      asset_id,
        "asset_code":    asset.asset_code,
        "purchase_price": asset.purchase_price,
        "years_used":    round(years, 2),
        "depreciated":   round(depreciated, 2),
        "current_value": round(current_value, 2),
        "gl_posted_this_run": delta if delta > 0 else 0.0
    }

def get_asset_summary(db: Session) -> dict:
    assets       = db.query(Asset).all()
    total        = len(assets)
    active       = len([a for a in assets if a.status == "active"])
    under_repair = len([a for a in assets if a.status == "under_repair"])
    disposed     = len([a for a in assets if a.status == "disposed"])
    total_value  = sum(a.current_value for a in assets if a.status == "active")

    return {
        "total_assets":  total,
        "active":        active,
        "under_repair":  under_repair,
        "disposed":      disposed,
        "total_value":   round(total_value, 2)
    }


# ── Maintenance ────────────────────────────────────────
def create_maintenance(db: Session, data: MaintenanceCreate, done_by: int) -> MaintenanceLog:
    # Update asset status if under repair
    asset = get_asset_by_id(db, data.asset_id)
    if data.status == "in_progress":
        asset.status = "under_repair"
    elif data.status == "completed" and asset.status == "under_repair":
        asset.status = "active"

    log = MaintenanceLog(
        asset_id         = data.asset_id,
        type             = data.type,
        description      = data.description,
        cost             = data.cost,
        maintenance_date = data.maintenance_date,
        next_due_date    = data.next_due_date,
        status           = data.status,
        done_by          = done_by
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_maintenance_by_asset(db: Session, asset_id: int):
    return db.query(MaintenanceLog).filter(
        MaintenanceLog.asset_id == asset_id
    ).order_by(MaintenanceLog.created_at.desc()).all()

def get_all_maintenance(db: Session):
    return db.query(MaintenanceLog).order_by(MaintenanceLog.created_at.desc()).all()