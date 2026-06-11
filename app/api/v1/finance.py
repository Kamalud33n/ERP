from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_finance
from app.schemas.finance import (
    ExpenseCreate, ExpenseUpdate, ExpenseOut,
    BudgetCreate, BudgetOut,
    GLCreate, GLOut
)
from app.services.finance_service import (
    create_expense, get_all_expenses, get_expenses_by_department, update_expense_status,
    create_budget, get_all_budgets, get_budget_by_department,
    create_gl_entry, get_all_gl_entries, get_gl_by_account_type,
    get_finance_summary
)

router = APIRouter()

# ── Expense ────────────────────────────────────────────

# Any logged in user → submit expense
@router.post("/expense", response_model=ExpenseOut)
def submit_expense(data: ExpenseCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_expense(db, data, current_user.id)

# Finance/Admin → all expenses
@router.get("/expense", response_model=List[ExpenseOut])
def all_expenses(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_expenses(db)

# Finance/Admin → filter by department
@router.get("/expense/dept/{department}", response_model=List[ExpenseOut])
def expenses_by_dept(department: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_expenses_by_department(db, department)

# Finance/Admin → approve or reject expense
@router.put("/expense/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, data: ExpenseUpdate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return update_expense_status(db, expense_id, data)


# ── Budget ─────────────────────────────────────────────

# Finance/Admin → create budget
@router.post("/budget", response_model=BudgetOut)
def add_budget(data: BudgetCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_budget(db, data, current_user.id)

# Finance/Admin → all budgets
@router.get("/budget", response_model=List[BudgetOut])
def all_budgets(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_budgets(db)

# Finance/Admin → filter by department
@router.get("/budget/dept/{department}", response_model=List[BudgetOut])
def budget_by_dept(department: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_budget_by_department(db, department)


# ── General Ledger ─────────────────────────────────────

# Finance/Admin → create GL entry
@router.post("/gl", response_model=GLOut)
def add_gl(data: GLCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_gl_entry(db, data, current_user.id)

# Finance/Admin → all GL entries
@router.get("/gl", response_model=List[GLOut])
def all_gl(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_gl_entries(db)

# Finance/Admin → filter by account type
@router.get("/gl/{account_type}", response_model=List[GLOut])
def gl_by_type(account_type: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_gl_by_account_type(db, account_type)


# ── Summary ────────────────────────────────────────────

# Finance/Admin → finance summary
@router.get("/summary")
def finance_summary(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_finance_summary(db)