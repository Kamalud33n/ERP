from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.finance import Expense, Budget, GeneralLedger
from app.schemas.finance import ExpenseCreate, ExpenseUpdate, BudgetCreate, GLCreate

# ── Expense ────────────────────────────────────────────
def create_expense(db: Session, data: ExpenseCreate, submitted_by: int) -> Expense:
    expense = Expense(
        title        = data.title,
        amount       = data.amount,
        category     = data.category,
        department   = data.department,
        date         = data.date,
        description  = data.description,
        submitted_by = submitted_by
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

def get_all_expenses(db: Session):
    return db.query(Expense).all()

def get_expenses_by_department(db: Session, department: str):
    return db.query(Expense).filter(Expense.department == department).all()

def update_expense_status(db: Session, expense_id: int, data: ExpenseUpdate) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.status      = data.status
    expense.approved_by = data.approved_by
    if data.status == "approved":
        budget = db.query(Budget).filter(
            Budget.department == expense.department,
            Budget.category   == expense.category
        ).first()
        if budget:
            budget.spent += expense.amount
            db.commit()
    db.commit()
    db.refresh(expense)
    return expense


# ── Budget ─────────────────────────────────────────────
def create_budget(db: Session, data: BudgetCreate, created_by: int) -> Budget:
    existing = db.query(Budget).filter(
        Budget.department == data.department,
        Budget.category   == data.category,
        Budget.month      == data.month
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this department/category/month")

    budget = Budget(
        department = data.department,
        category   = data.category,
        amount     = data.amount,
        month      = data.month,
        created_by = created_by
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget

def get_all_budgets(db: Session):
    return db.query(Budget).all()

def get_budget_by_department(db: Session, department: str):
    return db.query(Budget).filter(Budget.department == department).all()


# ── General Ledger ─────────────────────────────────────
def create_gl_entry(db: Session, data: GLCreate, created_by: int) -> GeneralLedger:
    last_entry = db.query(GeneralLedger).order_by(GeneralLedger.id.desc()).first()
    last_balance = last_entry.balance if last_entry else 0.0
    new_balance  = last_balance + data.debit - data.credit

    entry = GeneralLedger(
        date         = data.date,
        description  = data.description,
        debit        = data.debit,
        credit       = data.credit,
        balance      = new_balance,
        account_type = data.account_type,
        reference    = data.reference,
        created_by   = created_by
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_all_gl_entries(db: Session):
    return db.query(GeneralLedger).order_by(GeneralLedger.date).all()

def get_gl_by_account_type(db: Session, account_type: str):
    return db.query(GeneralLedger).filter(GeneralLedger.account_type == account_type).all()

def get_finance_summary(db: Session) -> dict:
    total_expenses  = sum(e.amount for e in db.query(Expense).filter(Expense.status == "approved").all())
    total_budget    = sum(b.amount for b in db.query(Budget).all())
    total_spent     = sum(b.spent  for b in db.query(Budget).all())
    pending_expenses = db.query(Expense).filter(Expense.status == "pending").count()

    return {
        "total_expenses":    round(total_expenses, 2),
        "total_budget":      round(total_budget, 2),
        "total_spent":       round(total_spent, 2),
        "budget_remaining":  round(total_budget - total_spent, 2),
        "pending_expenses":  pending_expenses
    }