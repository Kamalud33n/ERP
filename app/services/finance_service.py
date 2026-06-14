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


# ── Profit & Loss ──────────────────────────────────────
def get_profit_and_loss(db: Session, month: str = None) -> dict:
    gl_entries = db.query(GeneralLedger).all()

    if month:
        from datetime import datetime
        gl_entries = [g for g in gl_entries if str(g.date).startswith(month)]

    income   = sum(g.credit for g in gl_entries if g.account_type == "income")
    expenses = sum(g.debit  for g in gl_entries if g.account_type == "expense")
    assets   = sum(g.debit  for g in gl_entries if g.account_type == "asset")
    liability= sum(g.credit for g in gl_entries if g.account_type == "liability")

    gross_profit = income - expenses
    net_profit   = gross_profit

    return {
        "period":        month or "All Time",
        "total_income":  round(income, 2),
        "total_expenses":round(expenses, 2),
        "gross_profit":  round(gross_profit, 2),
        "net_profit":    round(net_profit, 2),
        "total_assets":  round(assets, 2),
        "total_liability":round(liability, 2),
        "is_profitable": gross_profit > 0
    }


# ── Cash Flow ──────────────────────────────────────────
def get_cash_flow(db: Session, month: str = None) -> dict:
    gl_entries = db.query(GeneralLedger).order_by(GeneralLedger.date).all()

    if month:
        gl_entries = [g for g in gl_entries if str(g.date).startswith(month)]

    cash_in  = sum(g.credit for g in gl_entries)
    cash_out = sum(g.debit  for g in gl_entries)
    net_flow = cash_in - cash_out

    # Monthly breakdown
    monthly = {}
    for g in db.query(GeneralLedger).order_by(GeneralLedger.date).all():
        m = str(g.date)[:7]  # YYYY-MM
        if m not in monthly:
            monthly[m] = {"month": m, "cash_in": 0, "cash_out": 0, "net": 0}
        monthly[m]["cash_in"]  += g.credit
        monthly[m]["cash_out"] += g.debit
        monthly[m]["net"]       = monthly[m]["cash_in"] - monthly[m]["cash_out"]

    return {
        "period":     month or "All Time",
        "cash_in":    round(cash_in, 2),
        "cash_out":   round(cash_out, 2),
        "net_flow":   round(net_flow, 2),
        "is_positive":net_flow > 0,
        "monthly_breakdown": [
            {
                "month":    v["month"],
                "cash_in":  round(v["cash_in"], 2),
                "cash_out": round(v["cash_out"], 2),
                "net":      round(v["net"], 2)
            }
            for v in sorted(monthly.values(), key=lambda x: x["month"])
        ]
    }


# ── Expense Analysis ───────────────────────────────────
def get_expense_analysis(db: Session) -> dict:
    expenses = db.query(Expense).filter(Expense.status == "approved").all()

    # By category
    categories = {}
    for e in expenses:
        if e.category not in categories:
            categories[e.category] = 0
        categories[e.category] += e.amount

    # By department
    departments = {}
    for e in expenses:
        if e.department not in departments:
            departments[e.department] = 0
        departments[e.department] += e.amount

    # By month
    monthly = {}
    for e in expenses:
        m = str(e.date)[:7]
        if m not in monthly:
            monthly[m] = 0
        monthly[m] += e.amount

    total = sum(e.amount for e in expenses)

    return {
        "total_approved_expenses": round(total, 2),
        "by_category":   [{"category": k, "amount": round(v, 2)} for k, v in sorted(categories.items(), key=lambda x: -x[1])],
        "by_department": [{"department": k, "amount": round(v, 2)} for k, v in sorted(departments.items(), key=lambda x: -x[1])],
        "by_month":      [{"month": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())]
    }


# ── Journal Entry ──────────────────────────────────────
from app.models.finance import JournalEntry, JournalLine
from app.schemas.finance import JournalEntryCreate

def create_journal_entry(db: Session, data: JournalEntryCreate, created_by: int) -> JournalEntry:
    # Validate double entry — total debit must equal total credit
    total_debit  = sum(l.debit  for l in data.lines)
    total_credit = sum(l.credit for l in data.lines)
    if round(total_debit, 2) != round(total_credit, 2):
        raise HTTPException(status_code=400, detail=f"Double entry error: Debit ({total_debit}) ≠ Credit ({total_credit})")

    # Auto generate entry number
    count        = db.query(JournalEntry).count()
    entry_number = f"JE-{datetime.now().year}-{str(count + 1).zfill(4)}"

    entry = JournalEntry(
        entry_number = entry_number,
        date         = data.date,
        description  = data.description,
        reference    = data.reference,
        status       = "posted",
        created_by   = created_by
    )
    db.add(entry)
    db.flush()  # get entry.id before commit

    for line in data.lines:
        db.add(JournalLine(
            entry_id     = entry.id,
            account_type = line.account_type,
            description  = line.description,
            debit        = line.debit,
            credit       = line.credit
        ))

    db.commit()
    db.refresh(entry)
    return entry

def get_all_journal_entries(db: Session):
    return db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).all()

def get_journal_entry_by_id(db: Session, entry_id: int) -> JournalEntry:
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry

def reverse_journal_entry(db: Session, entry_id: int, created_by: int) -> JournalEntry:
    original = get_journal_entry_by_id(db, entry_id)
    if original.status == "reversed":
        raise HTTPException(status_code=400, detail="Entry already reversed")

    count        = db.query(JournalEntry).count()
    entry_number = f"JE-{datetime.now().year}-{str(count + 1).zfill(4)}-REV"

    # Create reversed entry — swap debit/credit
    reversal = JournalEntry(
        entry_number = entry_number,
        date         = datetime.now().date(),
        description  = f"Reversal of {original.entry_number}",
        reference    = original.entry_number,
        status       = "posted",
        created_by   = created_by
    )
    db.add(reversal)
    db.flush()

    for line in original.lines:
        db.add(JournalLine(
            entry_id     = reversal.id,
            account_type = line.account_type,
            description  = line.description,
            debit        = line.credit,   # swap!
            credit       = line.debit     # swap!
        ))

    original.status = "reversed"
    db.commit()
    db.refresh(reversal)
    return reversal