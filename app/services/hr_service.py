from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.hr import Leave, Attendance, Payroll
from app.schemas.hr import LeaveCreate, LeaveUpdate, AttendanceCreate, PayrollCreate

# ── Leave ──────────────────────────────────────────────
def apply_leave(db: Session, employee_id: int, data: LeaveCreate) -> Leave:
    leave = Leave(
        employee_id = employee_id,
        leave_type  = data.leave_type,
        start_date  = data.start_date,
        end_date    = data.end_date,
        days        = data.days,
        reason      = data.reason
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave

def get_all_leaves(db: Session):
    return db.query(Leave).all()

def get_leaves_by_employee(db: Session, employee_id: int):
    return db.query(Leave).filter(Leave.employee_id == employee_id).all()

def update_leave_status(db: Session, leave_id: int, data: LeaveUpdate) -> Leave:
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status      = data.status
    leave.approved_by = data.approved_by
    db.commit()
    db.refresh(leave)
    return leave


# ── Attendance ─────────────────────────────────────────
def mark_attendance(db: Session, data: AttendanceCreate) -> Attendance:
    existing = db.query(Attendance).filter(
        Attendance.employee_id == data.employee_id,
        Attendance.date        == data.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")

    attendance = Attendance(
        employee_id = data.employee_id,
        date        = data.date,
        check_in    = data.check_in,
        check_out   = data.check_out,
        status      = data.status
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance

def get_attendance_by_employee(db: Session, employee_id: int):
    return db.query(Attendance).filter(Attendance.employee_id == employee_id).all()

def get_all_attendance(db: Session):
    return db.query(Attendance).all()


# ── Payroll ────────────────────────────────────────────
def create_payroll(db: Session, data: PayrollCreate, processed_by: int) -> Payroll:
    existing = db.query(Payroll).filter(
        Payroll.employee_id == data.employee_id,
        Payroll.month       == data.month
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Payroll already processed for this month")

    net_salary = data.basic_salary + data.allowances - data.deductions

    payroll = Payroll(
        employee_id  = data.employee_id,
        month        = data.month,
        basic_salary = data.basic_salary,
        allowances   = data.allowances,
        deductions   = data.deductions,
        net_salary   = net_salary,
        status       = "processed",
        processed_by = processed_by,
        processed_at = datetime.utcnow()
    )
    db.add(payroll)
    db.commit()
    db.refresh(payroll)
    return payroll

def get_payroll_by_employee(db: Session, employee_id: int):
    return db.query(Payroll).filter(Payroll.employee_id == employee_id).all()

def get_all_payrolls(db: Session):
    return db.query(Payroll).all()