from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut
from app.services.employee_service import (
    create_employee, get_all_employees, get_employee_by_id,
    get_employee_by_user_id, update_employee, delete_employee,
    assign_manager, remove_manager, get_direct_reports,
    get_org_chart, get_manager_chain,
)

router = APIRouter()

# ── Static paths MUST come before /{employee_id} ───────

@router.post("/", response_model=EmployeeOut)
def create(user_id: int, data: EmployeeCreate,
           db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_employee(db, user_id, data)

@router.get("/", response_model=List[EmployeeOut])
def get_all(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_employees(db)

@router.get("/me", response_model=EmployeeOut)
def get_my_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_employee_by_user_id(db, current_user.id)

@router.get("/org-chart", response_model=List[dict])
def org_chart(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Full org tree — nested by manager_id, single DB query, no N+1."""
    return get_org_chart(db)


# ── Parameterised /{employee_id} ───────────────────────

@router.get("/{employee_id}", response_model=EmployeeOut)
def get_by_id(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_employee_by_id(db, employee_id)

@router.put("/{employee_id}", response_model=EmployeeOut)
def update(employee_id: int, data: EmployeeUpdate,
           db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_employee(db, employee_id, data)

@router.delete("/{employee_id}")
def delete(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return delete_employee(db, employee_id)


# ── Org sub-paths /{employee_id}/... ───────────────────

@router.get("/{employee_id}/manager-chain", response_model=List[EmployeeOut])
def manager_chain(employee_id: int, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    return get_manager_chain(db, employee_id)

@router.get("/{employee_id}/direct-reports", response_model=List[EmployeeOut])
def direct_reports(employee_id: int, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    return get_direct_reports(db, employee_id)

@router.put("/{employee_id}/manager/{manager_id}", response_model=EmployeeOut)
def set_manager(employee_id: int, manager_id: int,
                db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return assign_manager(db, employee_id, manager_id)

@router.delete("/{employee_id}/manager", response_model=EmployeeOut)
def unset_manager(employee_id: int, db: Session = Depends(get_db),
                  current_user=Depends(get_hr)):
    return remove_manager(db, employee_id)