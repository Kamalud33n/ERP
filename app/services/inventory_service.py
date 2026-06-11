from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.inventory import Item, StockMovement
from app.schemas.inventory import ItemCreate, ItemUpdate, StockMovementCreate


# ── Item ───────────────────────────────────────────────
def create_item(db: Session, data: ItemCreate, created_by: int) -> Item:
    existing = db.query(Item).filter(Item.sku == data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    item = Item(
        name        = data.name,
        sku         = data.sku,
        category    = data.category,
        unit        = data.unit,
        description = data.description,
        min_stock   = data.min_stock,
        unit_price  = data.unit_price,
        created_by  = created_by
    )
    db.add(item)
    db.commit()
    db.refresh(item)
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
    db.commit()
    db.refresh(item)
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

    # Update stock
    if data.type == "in":
        item.current_stock += data.quantity
    elif data.type == "out":
        item.current_stock -= data.quantity
    elif data.type == "adjustment":
        item.current_stock = data.quantity

    movement = StockMovement(
        item_id   = data.item_id,
        type      = data.type,
        quantity  = data.quantity,
        reference = data.reference,
        note      = data.note,
        done_by   = done_by
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement

def get_movements_by_item(db: Session, item_id: int):
    return db.query(StockMovement).filter(
        StockMovement.item_id == item_id
    ).order_by(StockMovement.created_at.desc()).all()

def get_all_movements(db: Session):
    return db.query(StockMovement).order_by(StockMovement.created_at.desc()).all()

def get_inventory_summary(db: Session) -> dict:
    items         = db.query(Item).filter(Item.is_active == True).all()
    total_items   = len(items)
    low_stock     = len([i for i in items if i.current_stock <= i.min_stock])
    out_of_stock  = len([i for i in items if i.current_stock == 0])
    total_value   = sum(i.current_stock * i.unit_price for i in items)
    categories    = list(set(i.category for i in items))

    return {
        "total_items":  total_items,
        "low_stock":    low_stock,
        "out_of_stock": out_of_stock,
        "total_value":  round(total_value, 2),
        "categories":   len(categories)
    }