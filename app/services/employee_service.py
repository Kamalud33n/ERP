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
        user_id=user_id, first_name=data.first_name, last_name=data.last_name,
        phone=data.phone, department=data.department, designation=data.designation,
        salary=data.salary, join_date=data.join_date, manager_id=data.manager_id,
    )
    db.add(employee); db.commit(); db.refresh(employee)
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
    db.commit(); db.refresh(employee)
    return employee

def delete_employee(db: Session, employee_id: int):
    employee = get_employee_by_id(db, employee_id)
    db.delete(employee); db.commit()
    return {"message": "Employee deleted successfully"}


# ── Org Structure ──────────────────────────────────────

def assign_manager(db: Session, employee_id: int, manager_id: int) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    if employee_id == manager_id:
        raise HTTPException(status_code=400, detail="An employee cannot be their own manager")
    get_employee_by_id(db, manager_id)   # confirm manager exists
    employee.manager_id = manager_id
    db.commit(); db.refresh(employee)
    return employee

def remove_manager(db: Session, employee_id: int) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    employee.manager_id = None
    db.commit(); db.refresh(employee)
    return employee

def get_direct_reports(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.manager_id == employee_id).all()

def get_org_chart(db: Session) -> list:
    """Single query + Python tree build — no N+1."""
    all_employees = db.query(Employee).all()

    def build_node(emp):
        return {
            "id":             emp.id,
            "user_id":        emp.user_id,
            "full_name":      f"{emp.first_name} {emp.last_name}".strip(),
            "designation":    emp.designation,
            "department":     emp.department,
            "manager_id":     emp.manager_id,
            "direct_reports": [build_node(dr) for dr in all_employees if dr.manager_id == emp.id],
        }

    roots = [e for e in all_employees if e.manager_id is None]
    return [build_node(r) for r in roots]

def get_manager_chain(db: Session, employee_id: int) -> list:
    """Returns [direct_manager, ..., CEO]. Cycle-safe."""
    chain, seen = [], set()
    emp = get_employee_by_id(db, employee_id)
    mgr_id = emp.manager_id
    while mgr_id and mgr_id not in seen:
        seen.add(mgr_id)
        mgr = db.query(Employee).filter(Employee.id == mgr_id).first()
        if not mgr:
            break
        chain.append(mgr)
        mgr_id = mgr.manager_id
    return chain