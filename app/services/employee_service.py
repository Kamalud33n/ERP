from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

def create_employee(db: Session, user_id: int, data: EmployeeCreate) -> Employee:
    existing = db.query(Employee).filter(Employee.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee profile already exists for this user")

    employee = Employee(
        user_id     = user_id,
        first_name  = data.first_name,
        last_name   = data.last_name,
        phone       = data.phone,
        department  = data.department,
        designation = data.designation,
        salary      = data.salary,
        join_date   = data.join_date
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

def get_all_employees(db: Session):
    return db.query(Employee).all()

def get_employee_by_id(db: Session, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

def get_employee_by_user_id(db: Session, user_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return employee

def update_employee(db: Session, employee_id: int, data: EmployeeUpdate) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee

def delete_employee(db: Session, employee_id: int):
    employee = get_employee_by_id(db, employee_id)
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}