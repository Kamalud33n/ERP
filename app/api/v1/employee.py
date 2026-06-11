from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr, get_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut
from app.services.employee_service import (
    create_employee, get_all_employees, get_employee_by_id,
    get_employee_by_user_id, update_employee, delete_employee
)

router = APIRouter()

# HR/Admin → create employee profile
@router.post("/", response_model=EmployeeOut)
def create(user_id: int, data: EmployeeCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_employee(db, user_id, data)

# HR/Admin → get all employees
@router.get("/", response_model=List[EmployeeOut])
def get_all(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_employees(db)

# Employee → get own profile
@router.get("/me", response_model=EmployeeOut)
def get_my_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_employee_by_user_id(db, current_user.id)

# HR/Admin → get employee by id
@router.get("/{employee_id}", response_model=EmployeeOut)
def get_by_id(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_employee_by_id(db, employee_id)

# HR/Admin → update employee
@router.put("/{employee_id}", response_model=EmployeeOut)
def update(employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_employee(db, employee_id, data)

# Admin only → delete employee
@router.delete("/{employee_id}")
def delete(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return delete_employee(db, employee_id)