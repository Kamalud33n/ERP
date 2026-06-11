from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr
from app.schemas.hr import (
    LeaveCreate, LeaveUpdate, LeaveOut,
    AttendanceCreate, AttendanceOut,
    PayrollCreate, PayrollOut
)
from app.services.hr_service import (
    apply_leave, get_all_leaves, get_leaves_by_employee, update_leave_status,
    mark_attendance, get_attendance_by_employee, get_all_attendance,
    create_payroll, get_payroll_by_employee, get_all_payrolls
)
from app.services.employee_service import get_employee_by_user_id

router = APIRouter()

# ── Leave ──────────────────────────────────────────────

# Employee → apply leave
@router.post("/leave", response_model=LeaveOut)
def apply(data: LeaveCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return apply_leave(db, employee.id, data)

# HR/Admin → all leaves
@router.get("/leave", response_model=List[LeaveOut])
def all_leaves(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_leaves(db)

# Employee → own leaves
@router.get("/leave/me", response_model=List[LeaveOut])
def my_leaves(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_leaves_by_employee(db, employee.id)

# HR/Admin → approve or reject leave
@router.put("/leave/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: int, data: LeaveUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_leave_status(db, leave_id, data)


# ── Attendance ─────────────────────────────────────────

# HR/Admin → mark attendance
@router.post("/attendance", response_model=AttendanceOut)
def mark(data: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return mark_attendance(db, data)

# HR/Admin → all attendance
@router.get("/attendance", response_model=List[AttendanceOut])
def all_attendance(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_attendance(db)

# Employee → own attendance
@router.get("/attendance/me", response_model=List[AttendanceOut])
def my_attendance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_attendance_by_employee(db, employee.id)


# ── Payroll ────────────────────────────────────────────

# HR/Admin → process payroll
@router.post("/payroll", response_model=PayrollOut)
def process_payroll(data: PayrollCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_payroll(db, data, current_user.id)

# HR/Admin → all payrolls
@router.get("/payroll", response_model=List[PayrollOut])
def all_payrolls(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_payrolls(db)

# Employee → own payslips
@router.get("/payroll/me", response_model=List[PayrollOut])
def my_payroll(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_payroll_by_employee(db, employee.id)