from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.employee import Employee
from app.models.hr import Leave, Attendance, Payroll
from app.models.finance import Expense, Budget, GeneralLedger
from app.services.employee_service import get_employee_by_user_id

router = APIRouter()

@router.get("/")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # ── Admin Dashboard ────────────────────────────────
    if current_user.role == "admin":
        total_employees  = db.query(Employee).count()
        total_users      = db.query(User).count()
        pending_leaves   = db.query(Leave).filter(Leave.status == "pending").count()
        pending_expenses = db.query(Expense).filter(Expense.status == "pending").count()
        total_budget     = sum(b.amount for b in db.query(Budget).all())
        total_spent      = sum(b.spent for b in db.query(Budget).all())
        total_payrolls   = db.query(Payroll).filter(Payroll.status == "processed").count()

        return {
            "role":             "admin",
            "total_employees":  total_employees,
            "total_users":      total_users,
            "pending_leaves":   pending_leaves,
            "pending_expenses": pending_expenses,
            "total_budget":     round(total_budget, 2),
            "total_spent":      round(total_spent, 2),
            "budget_remaining": round(total_budget - total_spent, 2),
            "total_payrolls":   total_payrolls,
        }

    # ── HR Manager Dashboard ───────────────────────────
    elif current_user.role == "hr_manager":
        total_employees    = db.query(Employee).count()
        pending_leaves     = db.query(Leave).filter(Leave.status == "pending").count()
        approved_leaves    = db.query(Leave).filter(Leave.status == "approved").count()
        rejected_leaves    = db.query(Leave).filter(Leave.status == "rejected").count()
        total_attendance   = db.query(Attendance).count()
        present_today      = db.query(Attendance).filter(Attendance.status == "present").count()
        pending_payrolls   = db.query(Payroll).filter(Payroll.status == "pending").count()

        return {
            "role":            "hr_manager",
            "total_employees": total_employees,
            "pending_leaves":  pending_leaves,
            "approved_leaves": approved_leaves,
            "rejected_leaves": rejected_leaves,
            "total_attendance": total_attendance,
            "present_today":   present_today,
            "pending_payrolls": pending_payrolls,
        }

    # ── Finance Dashboard ──────────────────────────────
    elif current_user.role == "finance":
        total_expenses   = sum(e.amount for e in db.query(Expense).filter(Expense.status == "approved").all())
        pending_expenses = db.query(Expense).filter(Expense.status == "pending").count()
        total_budget     = sum(b.amount for b in db.query(Budget).all())
        total_spent      = sum(b.spent for b in db.query(Budget).all())
        gl_entries       = db.query(GeneralLedger).count()
        last_gl          = db.query(GeneralLedger).order_by(GeneralLedger.id.desc()).first()

        return {
            "role":             "finance",
            "total_expenses":   round(total_expenses, 2),
            "pending_expenses": pending_expenses,
            "total_budget":     round(total_budget, 2),
            "total_spent":      round(total_spent, 2),
            "budget_remaining": round(total_budget - total_spent, 2),
            "gl_entries":       gl_entries,
            "last_balance":     round(last_gl.balance, 2) if last_gl else 0.0,
        }

    # ── Employee Dashboard ─────────────────────────────
    elif current_user.role == "employee":
        try:
            employee        = get_employee_by_user_id(db, current_user.id)
            my_leaves       = db.query(Leave).filter(Leave.employee_id == employee.id).all()
            my_attendance   = db.query(Attendance).filter(Attendance.employee_id == employee.id).all()
            my_payrolls     = db.query(Payroll).filter(Payroll.employee_id == employee.id).all()
            pending_leaves  = sum(1 for l in my_leaves if l.status == "pending")
            approved_leaves = sum(1 for l in my_leaves if l.status == "approved")
            present_days    = sum(1 for a in my_attendance if a.status == "present")
            last_payroll    = db.query(Payroll).filter(
                Payroll.employee_id == employee.id
            ).order_by(Payroll.id.desc()).first()

            return {
                "role":             "employee",
                "name":             f"{employee.first_name} {employee.last_name}",
                "department":       employee.department,
                "designation":      employee.designation,
                "total_leaves":     len(my_leaves),
                "pending_leaves":   pending_leaves,
                "approved_leaves":  approved_leaves,
                "present_days":     present_days,
                "total_payrolls":   len(my_payrolls),
                "last_net_salary":  round(last_payroll.net_salary, 2) if last_payroll else 0.0,
            }
        except:
            return {
                "role":    "employee",
                "message": "Employee profile not created yet"
            }

    return {"message": "Unknown role"}