from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_admin
from app.schemas.inventory import ItemCreate, ItemUpdate, ItemOut, StockMovementCreate, StockMovementOut
from app.services.inventory_service import (
    create_item, get_all_items, get_item_by_id, update_item, delete_item, get_low_stock_items,
    add_stock_movement, get_movements_by_item, get_all_movements, get_inventory_summary
)

router = APIRouter()

@router.post("/item", response_model=ItemOut)
def add_item(data: ItemCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_item(db, data, current_user.id)

@router.get("/item", response_model=List[ItemOut])
def all_items(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_all_items(db)

@router.get("/item/low-stock", response_model=List[ItemOut])
def low_stock(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_low_stock_items(db)

@router.get("/item/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_item_by_id(db, item_id)

@router.put("/item/{item_id}", response_model=ItemOut)
def edit_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_item(db, item_id, data)

@router.delete("/item/{item_id}")
def remove_item(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return delete_item(db, item_id)

@router.post("/movement", response_model=StockMovementOut)
def stock_movement(data: StockMovementCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return add_stock_movement(db, data, current_user.id)

@router.get("/movement", response_model=List[StockMovementOut])
def all_movements(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_movements(db)

@router.get("/movement/{item_id}", response_model=List[StockMovementOut])
def item_movements(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_movements_by_item(db, item_id)

@router.get("/summary")
def inventory_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_inventory_summary(db)


# ── Export Reports ─────────────────────────────────────
from fastapi.responses import StreamingResponse
from app.services.export_service import export_inventory_excel

@router.get("/export/excel")
def export_inventory_excel_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    items = get_all_items(db)
    buffer = export_inventory_excel(items)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_report.xlsx"})