from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_admin
from app.schemas.asset import AssetCreate, AssetUpdate, AssetOut, MaintenanceCreate, MaintenanceOut
from app.services.asset_service import (
    create_asset, get_all_assets, get_asset_by_id, update_asset, delete_asset,
    calculate_depreciation, get_asset_summary,
    create_maintenance, get_maintenance_by_asset, get_all_maintenance
)

router = APIRouter()

# ── Asset ──────────────────────────────────────────────

@router.post("/", response_model=AssetOut)
def add_asset(data: AssetCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_asset(db, data, current_user.id)

@router.get("/", response_model=List[AssetOut])
def all_assets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_all_assets(db)

@router.get("/summary")
def asset_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_asset_summary(db)

@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_asset_by_id(db, asset_id)

@router.put("/{asset_id}", response_model=AssetOut)
def edit_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_asset(db, asset_id, data)

@router.delete("/{asset_id}")
def remove_asset(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return delete_asset(db, asset_id)

@router.get("/{asset_id}/depreciation")
def depreciation(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return calculate_depreciation(db, asset_id)

# ── Maintenance ────────────────────────────────────────

@router.post("/maintenance", response_model=MaintenanceOut)
def add_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_maintenance(db, data, current_user.id)

@router.get("/maintenance/all", response_model=List[MaintenanceOut])
def all_maintenance(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_maintenance(db)

@router.get("/maintenance/{asset_id}", response_model=List[MaintenanceOut])
def asset_maintenance(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_maintenance_by_asset(db, asset_id)