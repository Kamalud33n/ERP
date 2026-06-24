from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.inventory import Item, StockMovement
from app.schemas.inventory import ItemCreate, ItemUpdate, StockMovementCreate
from app.services.notification_service import create_notifications_bulk


# ── Item ───────────────────────────────────────────────
def create_item(db: Session, data: ItemCreate, created_by: int) -> Item:
    existing = db.query(Item).filter(Item.sku == data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    item = Item(name=data.name, sku=data.sku, category=data.category, unit=data.unit,
                description=data.description, min_stock=data.min_stock,
                unit_price=data.unit_price, created_by=created_by)
    db.add(item); db.commit(); db.refresh(item)
    return item

def get_all_items(db: Session):
    return db.query(Item).filter(Item.is_active == True).all()

def get_item_by_id(db: Session, item_id: int) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

def update_item(db: Session, item_id: int, data: ItemUpdate) -> Item:
    item = get_item_by_id(db, item_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit(); db.refresh(item)
    return item

def delete_item(db: Session, item_id: int):
    item = get_item_by_id(db, item_id)
    item.is_active = False
    db.commit()
    return {"message": "Item deactivated"}

def get_low_stock_items(db: Session):
    items = db.query(Item).filter(Item.is_active == True).all()
    return [i for i in items if i.current_stock <= i.min_stock]


# ── Stock Movement ─────────────────────────────────────
def add_stock_movement(db: Session, data: StockMovementCreate, done_by: int) -> StockMovement:
    item = get_item_by_id(db, data.item_id)

    if data.type == "out" and item.current_stock < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {item.current_stock}")

    if data.type == "in":
        item.current_stock += data.quantity
    elif data.type == "out":
        item.current_stock -= data.quantity
    elif data.type == "adjustment":
        item.current_stock = data.quantity

    movement = StockMovement(
        item_id=data.item_id, type=data.type, quantity=data.quantity,
        reference=data.reference, note=data.note, done_by=done_by
    )
    db.add(movement); db.commit(); db.refresh(movement)

    # ── Low-stock alert ───────────────────────────────────
    if data.type in ("out", "adjustment") and item.current_stock <= item.min_stock:
        from app.models.user import User
        alert_users = db.query(User).filter(
            User.role.in_(["admin", "hr_manager"]),
            User.is_active == True
        ).all()
        user_ids = [u.id for u in alert_users]
        if user_ids:
            level = "OUT OF STOCK" if item.current_stock == 0 else "LOW STOCK"
            create_notifications_bulk(
                db=db, user_ids=user_ids,
                title=f"Inventory Alert: {level}",
                message=(
                    f"Item '{item.name}' (SKU: {item.sku}) is {level.lower()}. "
                    f"Current: {item.current_stock} {item.unit}, "
                    f"Minimum threshold: {item.min_stock} {item.unit}. "
                    f"Please raise a Purchase Request."
                ),
                module="inventory",
                notif_type="alert" if item.current_stock == 0 else "warning",
            )

    return movement

def get_movements_by_item(db: Session, item_id: int):
    return db.query(StockMovement).filter(StockMovement.item_id == item_id).order_by(StockMovement.created_at.desc()).all()

def get_all_movements(db: Session):
    return db.query(StockMovement).order_by(StockMovement.created_at.desc()).all()

def get_inventory_summary(db: Session) -> dict:
    items = db.query(Item).filter(Item.is_active == True).all()
    return {
        "total_items":  len(items),
        "low_stock":    len([i for i in items if i.current_stock <= i.min_stock]),
        "out_of_stock": len([i for i in items if i.current_stock == 0]),
        "total_value":  round(sum(i.current_stock * i.unit_price for i in items), 2),
        "categories":   len(set(i.category for i in items))
    }


# ── Barcode Generation ─────────────────────────────────
def generate_item_barcode(db: Session, item_id: int) -> bytes:
    """
    EAN-13 for 12-digit numeric SKUs; Code128 for everything else.
    Returns raw PNG bytes.
    """
    import barcode
    from barcode.writer import ImageWriter
    import io

    item = get_item_by_id(db, item_id)
    sku  = item.sku
    buf  = io.BytesIO()

    if sku.isdigit() and len(sku) == 12:
        bc = barcode.get("ean13", sku, writer=ImageWriter())
    else:
        bc = barcode.get("code128", sku, writer=ImageWriter())

    bc.write(buf, options={"module_width": 0.4, "module_height": 15.0,
                            "font_size": 10, "text_distance": 5.0, "write_text": True})
    buf.seek(0)
    return buf.read()