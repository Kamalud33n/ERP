from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from typing import List
import os, shutil
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_hr
from app.schemas.hr import (
    LeaveCreate, LeaveUpdate, LeaveOut,
    AttendanceCreate, AttendanceOut,
    PayrollCreate, PayrollOut,
    ContractCreate, ContractUpdate, ContractOut,
    PerformanceCreate, PerformanceUpdate, PerformanceOut
)
from app.services.hr_service import (
    apply_leave, get_all_leaves, get_leaves_by_employee, update_leave_status,
    mark_attendance, get_attendance_by_employee, get_all_attendance,
    create_payroll, get_payroll_by_employee, get_all_payrolls,
    create_contract, get_all_contracts, get_contracts_by_employee,
    update_contract, get_expiring_contracts, get_expired_contracts,
    create_performance_review, get_all_reviews, get_reviews_by_employee,
    update_performance_review, get_performance_summary,
    save_document, get_documents_by_employee,
    get_all_documents, delete_document, ensure_upload_dir
)
from app.services.employee_service import get_employee_by_user_id

router = APIRouter()

UPLOAD_DIR = "uploads/documents"

# ── Leave ──────────────────────────────────────────────

@router.post("/leave", response_model=LeaveOut)
def apply(data: LeaveCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return apply_leave(db, employee.id, data)

@router.get("/leave", response_model=List[LeaveOut])
def all_leaves(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_leaves(db)

@router.get("/leave/me", response_model=List[LeaveOut])
def my_leaves(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_leaves_by_employee(db, employee.id)

@router.put("/leave/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: int, data: LeaveUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_leave_status(db, leave_id, data)


# ── Attendance ─────────────────────────────────────────

@router.post("/attendance", response_model=AttendanceOut)
def mark(data: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return mark_attendance(db, data)

@router.get("/attendance", response_model=List[AttendanceOut])
def all_attendance(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_attendance(db)

@router.get("/attendance/me", response_model=List[AttendanceOut])
def my_attendance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_attendance_by_employee(db, employee.id)


# ── Payroll ────────────────────────────────────────────

@router.post("/payroll", response_model=PayrollOut)
def process_payroll(data: PayrollCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_payroll(db, data, current_user.id)

@router.get("/payroll", response_model=List[PayrollOut])
def all_payrolls(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_payrolls(db)

@router.get("/payroll/me", response_model=List[PayrollOut])
def my_payroll(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_payroll_by_employee(db, employee.id)


# ── Contract ───────────────────────────────────────────

@router.post("/contract", response_model=ContractOut)
def add_contract(data: ContractCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_contract(db, data, current_user.id)

@router.get("/contract", response_model=List[ContractOut])
def all_contracts(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_contracts(db)

@router.get("/contract/me", response_model=List[ContractOut])
def my_contracts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_contracts_by_employee(db, employee.id)

@router.get("/contract/expiring")
def expiring_contracts(days: int = 30, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_expiring_contracts(db, days)

@router.get("/contract/expired")
def expired_contracts(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_expired_contracts(db)

@router.put("/contract/{contract_id}", response_model=ContractOut)
def edit_contract(contract_id: int, data: ContractUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_contract(db, contract_id, data)


# ── Performance Review ─────────────────────────────────

@router.post("/performance", response_model=PerformanceOut)
def add_review(data: PerformanceCreate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return create_performance_review(db, data, current_user.id)

@router.get("/performance", response_model=List[PerformanceOut])
def all_reviews(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_all_reviews(db)

@router.get("/performance/me", response_model=List[PerformanceOut])
def my_reviews(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return get_reviews_by_employee(db, employee.id)

@router.get("/performance/summary/{employee_id}")
def performance_summary(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return get_performance_summary(db, employee_id)

@router.put("/performance/{review_id}", response_model=PerformanceOut)
def update_review(review_id: int, data: PerformanceUpdate, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return update_performance_review(db, review_id, data)

@router.put("/performance/{review_id}/acknowledge", response_model=PerformanceOut)
def acknowledge_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_performance_review(db, review_id, PerformanceUpdate(status="acknowledged"))


# ── Documents ──────────────────────────────────────────

@router.post("/document")
async def upload_document(
    employee_id: int = Form(...),
    doc_type:    str = Form(...),
    doc_name:    str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_hr)
):
    ensure_upload_dir()
    filename  = f"{employee_id}_{doc_type}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = f"{round(os.path.getsize(file_path) / 1024, 1)} KB"
    return save_document(db, employee_id, doc_type, doc_name, file_path, size, current_user.id)

@router.get("/document")
def all_documents(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    docs = get_all_documents(db)
    return [{"id": d.id, "employee_id": d.employee_id, "doc_type": d.doc_type,
             "doc_name": d.doc_name, "file_size": d.file_size,
             "uploaded_by": d.uploaded_by, "created_at": str(d.created_at)} for d in docs]

@router.get("/document/me")
def my_documents(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    docs = get_documents_by_employee(db, employee.id)
    return [{"id": d.id, "employee_id": d.employee_id, "doc_type": d.doc_type,
             "doc_name": d.doc_name, "file_size": d.file_size,
             "uploaded_by": d.uploaded_by, "created_at": str(d.created_at)} for d in docs]

@router.get("/document/download/{doc_id}")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.hr import EmployeeDocument
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FastAPIFileResponse(doc.file_path, filename=doc.doc_name)

@router.delete("/document/{doc_id}")
def remove_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_hr)):
    return delete_document(db, doc_id)


# ── Export Reports ─────────────────────────────────────
from fastapi.responses import StreamingResponse
from app.services.export_service import (
    export_payroll_pdf, export_payroll_excel,
    export_employees_pdf, export_employees_excel
)
from app.services.employee_service import get_all_employees

# HR/Admin → export payroll PDF
@router.get("/export/payroll/pdf")
def export_payroll_pdf_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    payrolls = get_all_payrolls(db)
    buffer = export_payroll_pdf(payrolls)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=payroll_report.pdf"})

# HR/Admin → export payroll Excel
@router.get("/export/payroll/excel")
def export_payroll_excel_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    payrolls = get_all_payrolls(db)
    buffer = export_payroll_excel(payrolls)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=payroll_report.xlsx"})

# HR/Admin → export employees PDF
@router.get("/export/employees/pdf")
def export_employees_pdf_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    employees = get_all_employees(db)
    buffer = export_employees_pdf(employees)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=employee_list.pdf"})

# HR/Admin → export employees Excel
@router.get("/export/employees/excel")
def export_employees_excel_route(db: Session = Depends(get_db), current_user=Depends(get_hr)):
    employees = get_all_employees(db)
    buffer = export_employees_excel(employees)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employee_list.xlsx"})


# ── Single Payslip PDF ─────────────────────────────────
from app.services.export_service import export_single_payslip_pdf
from app.services.employee_service import get_all_employees

@router.get("/export/payslip/{payroll_id}/pdf")
def download_payslip(payroll_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.hr import Payroll
    from app.models.employee import Employee

    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")

    # Employee can only download own payslip
    if current_user.role == "employee":
        employee = get_employee_by_user_id(db, current_user.id)
        if payroll.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        employee = db.query(Employee).filter(Employee.id == payroll.employee_id).first()

    buffer = export_single_payslip_pdf(payroll, employee)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{payroll.month}.pdf"})


# ── Employee Self Check In/Out ──────────────────────────
from app.services.hr_service import employee_check_in, employee_check_out, get_today_attendance

@router.post("/attendance/checkin")
def check_in(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return employee_check_in(db, employee.id)

@router.post("/attendance/checkout")
def check_out(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    return employee_check_out(db, employee.id)

@router.get("/attendance/today")
def today_attendance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    employee = get_employee_by_user_id(db, current_user.id)
    att = get_today_attendance(db, employee.id)
    if not att:
        return {"status": "not_marked", "check_in": None, "check_out": None}
    return {
        "status":    att.status,
        "check_in":  str(att.check_in) if att.check_in else None,
        "check_out": str(att.check_out) if att.check_out else None,
        "date":      str(att.date)
    }