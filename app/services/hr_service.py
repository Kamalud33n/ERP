from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.hr import Leave, Attendance, Payroll, ActivityLog
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

def update_leave_status(db: Session, leave_id: int, data: LeaveUpdate, done_by_user) -> Leave:
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status      = data.status
    leave.approved_by = data.approved_by

    # Activity log
    log = ActivityLog(
        action       = f"{data.status}_leave",
        module       = "hr",
        reference_id = leave_id,
        done_by      = done_by_user.id,
        done_by_role = done_by_user.role,
        description  = f"{done_by_user.username} {data.status} leave #{leave_id} (Employee {leave.employee_id})",
        reversed     = False
    )
    db.add(log)
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
def create_payroll(db: Session, data: PayrollCreate, processed_by_user) -> Payroll:
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
        processed_by = processed_by_user.id,
        processed_at = datetime.utcnow()
    )
    db.add(payroll)

    # Activity log
    log = ActivityLog(
        action       = "processed_payroll",
        module       = "payroll",
        reference_id = data.employee_id,
        done_by      = processed_by_user.id,
        done_by_role = processed_by_user.role,
        description  = f"{processed_by_user.username} processed payroll for Employee {data.employee_id} - {data.month} (Net: {net_salary})",
        reversed     = False
    )
    db.add(log)
    db.commit()
    db.refresh(payroll)
    return payroll

def get_payroll_by_employee(db: Session, employee_id: int):
    return db.query(Payroll).filter(Payroll.employee_id == employee_id).all()

def get_all_payrolls(db: Session):
    return db.query(Payroll).all()


# ── Activity Log ───────────────────────────────────────
def get_all_activity_logs(db: Session):
    return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()


# ── Contract ───────────────────────────────────────────
from app.models.hr import Contract
from app.schemas.hr import ContractCreate, ContractUpdate
from datetime import date

def create_contract(db: Session, data: ContractCreate, created_by: int) -> Contract:
    contract = Contract(
        employee_id   = data.employee_id,
        contract_type = data.contract_type,
        start_date    = data.start_date,
        end_date      = data.end_date,
        salary        = data.salary,
        position      = data.position,
        department    = data.department,
        notes         = data.notes,
        created_by    = created_by
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

def get_all_contracts(db: Session):
    return db.query(Contract).all()

def get_contracts_by_employee(db: Session, employee_id: int):
    return db.query(Contract).filter(Contract.employee_id == employee_id).all()

def update_contract(db: Session, contract_id: int, data: ContractUpdate) -> Contract:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(contract, field, value)
    db.commit()
    db.refresh(contract)
    return contract

def get_expiring_contracts(db: Session, days: int = 30):
    from datetime import timedelta
    today     = date.today()
    threshold = today + timedelta(days=days)
    return db.query(Contract).filter(
        Contract.end_date != None,
        Contract.end_date <= threshold,
        Contract.end_date >= today,
        Contract.status == "active"
    ).all()

def get_expired_contracts(db: Session):
    today = date.today()
    expired = db.query(Contract).filter(
        Contract.end_date != None,
        Contract.end_date < date.today(),
        Contract.status == "active"
    ).all()
    # Auto mark as expired
    for c in expired:
        c.status = "expired"
    db.commit()
    return expired


# ── Performance Review ─────────────────────────────────
from app.models.hr import PerformanceReview
from app.schemas.hr import PerformanceCreate, PerformanceUpdate

def create_performance_review(db: Session, data: PerformanceCreate, reviewer_id: int) -> PerformanceReview:
    existing = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == data.employee_id,
        PerformanceReview.period      == data.period
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Review already exists for this period")

    review = PerformanceReview(
        employee_id      = data.employee_id,
        reviewer_id      = reviewer_id,
        period           = data.period,
        rating           = data.rating,
        kpi_score        = data.kpi_score,
        attendance_score = data.attendance_score,
        teamwork_score   = data.teamwork_score,
        technical_score  = data.technical_score,
        comments         = data.comments,
        goals            = data.goals,
        status           = "submitted"
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

def get_all_reviews(db: Session):
    return db.query(PerformanceReview).order_by(PerformanceReview.created_at.desc()).all()

def get_reviews_by_employee(db: Session, employee_id: int):
    return db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == employee_id
    ).order_by(PerformanceReview.created_at.desc()).all()

def update_performance_review(db: Session, review_id: int, data: PerformanceUpdate) -> PerformanceReview:
    review = db.query(PerformanceReview).filter(PerformanceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    return review

def get_performance_summary(db: Session, employee_id: int) -> dict:
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == employee_id
    ).all()
    if not reviews:
        return {"message": "No reviews found"}

    avg_rating   = sum(r.rating for r in reviews) / len(reviews)
    avg_kpi      = sum(r.kpi_score for r in reviews) / len(reviews)
    avg_attend   = sum(r.attendance_score for r in reviews) / len(reviews)
    avg_teamwork = sum(r.teamwork_score for r in reviews) / len(reviews)
    avg_tech     = sum(r.technical_score for r in reviews) / len(reviews)

    return {
        "employee_id":    employee_id,
        "total_reviews":  len(reviews),
        "avg_rating":     round(avg_rating, 2),
        "avg_kpi":        round(avg_kpi, 2),
        "avg_attendance": round(avg_attend, 2),
        "avg_teamwork":   round(avg_teamwork, 2),
        "avg_technical":  round(avg_tech, 2)
    }


# ── Document ───────────────────────────────────────────
from app.models.hr import EmployeeDocument
import os

UPLOAD_DIR = "uploads/documents"

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_document(db: Session, employee_id: int, doc_type: str, doc_name: str, file_path: str, file_size: str, uploaded_by: int) -> EmployeeDocument:
    doc = EmployeeDocument(
        employee_id = employee_id,
        doc_type    = doc_type,
        doc_name    = doc_name,
        file_path   = file_path,
        file_size   = file_size,
        uploaded_by = uploaded_by
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_documents_by_employee(db: Session, employee_id: int):
    return db.query(EmployeeDocument).filter(
        EmployeeDocument.employee_id == employee_id
    ).order_by(EmployeeDocument.created_at.desc()).all()

def get_all_documents(db: Session):
    return db.query(EmployeeDocument).order_by(EmployeeDocument.created_at.desc()).all()

def delete_document(db: Session, doc_id: int):
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}