from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_admin
from app.schemas.asset import AssetCreate, AssetUpdate, AssetOut, MaintenanceCreate, MaintenanceOut
from app.services.asset_service import (
    create_asset, get_all_assets, get_asset_by_id, update_asset, delete_asset,
    calculate_depreciation, get_asset_summary, get_assets_by_employee,
    create_maintenance, get_maintenance_by_asset, get_all_maintenance,
    generate_asset_qr,
)
from app.services.employee_service import get_employee_by_user_id

router = APIRouter()

@router.post("/", response_model=AssetOut)
def add_asset(data: AssetCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_asset(db, data, current_user.id)

# Static paths before /{asset_id}
@router.get("/my-assets", response_model=List[AssetOut])
def my_assets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_assets_by_employee(db, employee.id)

@router.get("/summary")
def asset_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_asset_summary(db)

@router.post("/maintenance", response_model=MaintenanceOut)
def add_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_maintenance(db, data, current_user.id)

@router.get("/maintenance/all", response_model=List[MaintenanceOut])
def all_maintenance(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_maintenance(db)

@router.get("/maintenance/{asset_id}", response_model=List[MaintenanceOut])
def asset_maintenance(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_maintenance_by_asset(db, asset_id)

from app.services.export_service import export_assets_excel

@router.get("/export/excel")
def export_assets_excel_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    assets = get_all_assets(db)
    buffer = export_assets_excel(assets)
    return StreamingResponse(buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=asset_report.xlsx"})

# Parameterised
@router.get("/", response_model=List[AssetOut])
def all_assets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_all_assets(db)

@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_asset_by_id(db, asset_id)

@router.put("/{asset_id}", response_model=AssetOut)
def edit_asset(asset_id: int, data: AssetUpdate,
               db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_asset(db, asset_id, data)

@router.delete("/{asset_id}")
def remove_asset(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return delete_asset(db, asset_id)

@router.get("/{asset_id}/depreciation")
def depreciation(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return calculate_depreciation(db, asset_id)

@router.get("/{asset_id}/qr")
def asset_qr_code(asset_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Returns a PNG QR code. Print and attach to the physical asset."""
    return Response(content=generate_asset_qr(db, asset_id), media_type="image/png")