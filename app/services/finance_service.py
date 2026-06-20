from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date
from app.models.finance import Expense, Budget, GeneralLedger
from app.schemas.finance import ExpenseCreate, ExpenseUpdate, BudgetCreate, GLCreate

# ── GL Posting Helper ──────────────────────────────────
# BUG FIX: `datetime` was previously only imported inside get_profit_and_loss(),
# so create_journal_entry, reverse_journal_entry, get_balance_sheet,
# create_vendor_bill, and create_vendor_payment all crashed with
# NameError at runtime. Fixed by importing at module level above.

def post_gl_entry(db: Session, entry_date, description: str, account_type: str,
                   debit: float = 0.0, credit: float = 0.0,
                   reference: str = None, created_by: int = None) -> GeneralLedger:
    """
    Internal helper used both by the manual /gl endpoint and by auto-posting
    hooks from other modules (payroll, procurement, assets). Keeps the
    running-balance logic in one place.
    """
    last_entry = db.query(GeneralLedger).order_by(GeneralLedger.id.desc()).first()
    last_balance = last_entry.balance if last_entry else 0.0
    new_balance = last_balance + debit - credit

    entry = GeneralLedger(
        date         = entry_date,
        description  = description,
        debit        = debit,
        credit       = credit,
        balance      = new_balance,
        account_type = account_type,
        reference    = reference,
        created_by   = created_by
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


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

def get_over_budget_alerts(db: Session):
    """
    Return Budget objects where spent exceeds the allocated amount.
    """
    return db.query(Budget).filter(Budget.spent > Budget.amount).all()


# ── General Ledger ─────────────────────────────────────
def create_gl_entry(db: Session, data: GLCreate, created_by: int) -> GeneralLedger:
    return post_gl_entry(
        db, entry_date=data.date, description=data.description,
        account_type=data.account_type, debit=data.debit, credit=data.credit,
        reference=data.reference, created_by=created_by
    )

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
        gl_entries = [g for g in gl_entries if str(g.date).startswith(month)]

    # Net per account type (credit - debit for income/liability, debit - credit for expense/asset)
    # FIX: previously one-sided (e.g. expenses = sum(debit) only), so a credit
    # entry against an expense account (a refund/correction) had no effect.
    income    = sum(g.credit for g in gl_entries if g.account_type == "income")  - sum(g.debit  for g in gl_entries if g.account_type == "income")
    expenses  = sum(g.debit  for g in gl_entries if g.account_type == "expense") - sum(g.credit for g in gl_entries if g.account_type == "expense")
    assets    = sum(g.debit  for g in gl_entries if g.account_type == "asset")   - sum(g.credit for g in gl_entries if g.account_type == "asset")
    liability = sum(g.credit for g in gl_entries if g.account_type == "liability") - sum(g.debit for g in gl_entries if g.account_type == "liability")

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


# ── Chart of Accounts ──────────────────────────────────
from app.models.finance import ChartOfAccount
from app.schemas.finance import COACreate, COAUpdate

def create_coa(db: Session, data: COACreate, created_by: int) -> ChartOfAccount:
    existing = db.query(ChartOfAccount).filter(ChartOfAccount.account_code == data.account_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")
    coa = ChartOfAccount(
        account_code = data.account_code,
        account_name = data.account_name,
        account_type = data.account_type,
        parent_id    = data.parent_id,
        description  = data.description,
        created_by   = created_by
    )
    db.add(coa)
    db.commit()
    db.refresh(coa)
    return coa

def get_all_coa(db: Session):
    return db.query(ChartOfAccount).filter(ChartOfAccount.is_active == True).order_by(ChartOfAccount.account_code).all()

def get_coa_by_type(db: Session, account_type: str):
    return db.query(ChartOfAccount).filter(
        ChartOfAccount.account_type == account_type,
        ChartOfAccount.is_active    == True
    ).order_by(ChartOfAccount.account_code).all()

def update_coa(db: Session, coa_id: int, data: COAUpdate) -> ChartOfAccount:
    coa = db.query(ChartOfAccount).filter(ChartOfAccount.id == coa_id).first()
    if not coa:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(coa, field, value)
    db.commit()
    db.refresh(coa)
    return coa

def seed_default_coa(db: Session, created_by: int):
    """Seed default Chart of Accounts"""
    defaults = [
        # Assets (1000-1999)
        ("1000", "Cash & Cash Equivalents", "asset", None),
        ("1001", "Cash on Hand",            "asset", None),
        ("1002", "Bank Account",            "asset", None),
        ("1100", "Accounts Receivable",     "asset", None),
        ("1200", "Inventory",               "asset", None),
        ("1500", "Fixed Assets",            "asset", None),
        ("1501", "Equipment",               "asset", None),
        ("1502", "Furniture",               "asset", None),
        # Liabilities (2000-2999)
        ("2000", "Accounts Payable",        "liability", None),
        ("2001", "Vendor Payables",         "liability", None),
        ("2100", "Salaries Payable",        "liability", None),
        ("2200", "Tax Payable",             "liability", None),
        # Equity (3000-3999)
        ("3000", "Owner Equity",            "equity", None),
        ("3100", "Retained Earnings",       "equity", None),
        # Income (4000-4999)
        ("4000", "Revenue",                 "income", None),
        ("4001", "Sales Revenue",           "income", None),
        ("4002", "Service Revenue",         "income", None),
        # Expenses (5000-5999)
        ("5000", "Operating Expenses",      "expense", None),
        ("5001", "Salaries Expense",        "expense", None),
        ("5002", "Rent Expense",            "expense", None),
        ("5003", "Utilities Expense",       "expense", None),
        ("5004", "Office Supplies",         "expense", None),
        ("5005", "Travel Expense",          "expense", None),
        ("5006", "Software & IT",           "expense", None),
        ("5100", "Depreciation Expense",    "expense", None),
    ]
    count = 0
    for code, name, acc_type, parent in defaults:
        exists = db.query(ChartOfAccount).filter(ChartOfAccount.account_code == code).first()
        if not exists:
            db.add(ChartOfAccount(
                account_code = code,
                account_name = name,
                account_type = acc_type,
                parent_id    = parent,
                created_by   = created_by
            ))
            count += 1
    db.commit()
    return {"message": f"{count} accounts seeded successfully"}


# ── Balance Sheet ──────────────────────────────────────
def get_balance_sheet(db: Session) -> dict:
    gl_entries = db.query(GeneralLedger).all()

    # FIX: net per account type instead of one-sided sum, so payments/depreciation
    # (which post the opposite side) actually reduce the totals.
    total_assets      = sum(g.debit  for g in gl_entries if g.account_type == "asset")     - sum(g.credit for g in gl_entries if g.account_type == "asset")
    total_liabilities = sum(g.credit for g in gl_entries if g.account_type == "liability") - sum(g.debit  for g in gl_entries if g.account_type == "liability")
    total_income       = sum(g.credit for g in gl_entries if g.account_type == "income")   - sum(g.debit  for g in gl_entries if g.account_type == "income")
    total_expenses     = sum(g.debit  for g in gl_entries if g.account_type == "expense")  - sum(g.credit for g in gl_entries if g.account_type == "expense")
    net_profit        = total_income - total_expenses
    total_equity      = net_profit  # simplified

    return {
        "assets": {
            "total": round(total_assets, 2),
            "breakdown": [
                {"name": "Fixed Assets",    "amount": round(total_assets * 0.6, 2)},
                {"name": "Current Assets",  "amount": round(total_assets * 0.4, 2)},
            ]
        },
        "liabilities": {
            "total": round(total_liabilities, 2),
            "breakdown": [
                {"name": "Accounts Payable", "amount": round(total_liabilities * 0.5, 2)},
                {"name": "Other Payables",   "amount": round(total_liabilities * 0.5, 2)},
            ]
        },
        "equity": {
            "total":      round(total_equity, 2),
            "net_profit": round(net_profit, 2),
        },
        "balance_check": round(total_assets, 2) == round(total_liabilities + total_equity, 2),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


# ── Accounts Payable ───────────────────────────────────
from app.models.finance import VendorBill, VendorPayment
from app.schemas.finance import VendorBillCreate, VendorBillUpdate, VendorPaymentCreate

def create_vendor_bill(db: Session, data: VendorBillCreate, created_by: int) -> VendorBill:
    count       = db.query(VendorBill).count()
    bill_number = f"BILL-{datetime.now().year}-{str(count + 1).zfill(4)}"

    bill = VendorBill(
        vendor_id   = data.vendor_id,
        bill_number = bill_number,
        bill_date   = data.bill_date,
        due_date    = data.due_date,
        amount      = data.amount,
        outstanding = data.amount,  # initially full amount outstanding
        description = data.description,
        created_by  = created_by
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    # Auto-post to GL: vendor bill = liability incurred
    post_gl_entry(
        db, entry_date=data.bill_date,
        description=f"Vendor Bill {bill_number} received",
        account_type="liability", credit=data.amount,
        reference=bill_number, created_by=created_by
    )
    return bill

def get_all_bills(db: Session):
    return db.query(VendorBill).order_by(VendorBill.created_at.desc()).all()

def get_bill_by_id(db: Session, bill_id: int) -> VendorBill:
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

def get_outstanding_bills(db: Session):
    return db.query(VendorBill).filter(
        VendorBill.status.in_(["unpaid", "partial", "overdue"])
    ).order_by(VendorBill.due_date).all()

def update_bill(db: Session, bill_id: int, data: VendorBillUpdate) -> VendorBill:
    bill = get_bill_by_id(db, bill_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(bill, field, value)
    db.commit()
    db.refresh(bill)
    return bill

def create_vendor_payment(db: Session, data: VendorPaymentCreate, created_by: int) -> VendorPayment:
    bill = get_bill_by_id(db, data.bill_id)

    if data.amount > bill.outstanding:
        raise HTTPException(status_code=400, detail=f"Payment amount ({data.amount}) exceeds outstanding ({bill.outstanding})")

    count          = db.query(VendorPayment).count()
    payment_number = f"PAY-{datetime.now().year}-{str(count + 1).zfill(4)}"

    payment = VendorPayment(
        bill_id        = data.bill_id,
        vendor_id      = bill.vendor_id,
        payment_number = payment_number,
        payment_date   = data.payment_date,
        amount         = data.amount,
        payment_method = data.payment_method,
        reference      = data.reference,
        notes          = data.notes,
        created_by     = created_by
    )
    db.add(payment)

    # Update bill outstanding and status
    bill.paid_amount  += data.amount
    bill.outstanding   = round(bill.amount - bill.paid_amount, 2)

    if bill.outstanding <= 0:
        bill.status = "paid"
    elif bill.paid_amount > 0:
        bill.status = "partial"

    db.commit()
    db.refresh(payment)

    # Auto-post to GL: payment reduces the liability (debit liability)
    post_gl_entry(
        db, entry_date=data.payment_date,
        description=f"Vendor Payment {payment_number} - Bill {bill.bill_number}",
        account_type="liability", debit=data.amount,
        reference=payment_number, created_by=created_by
    )
    return payment

def get_payments_by_bill(db: Session, bill_id: int):
    return db.query(VendorPayment).filter(VendorPayment.bill_id == bill_id).all()

def get_ap_summary(db: Session) -> dict:
    bills        = db.query(VendorBill).all()
    total_bills  = len(bills)
    total_amount = sum(b.amount for b in bills)
    total_paid   = sum(b.paid_amount for b in bills)
    outstanding  = sum(b.outstanding for b in bills)
    overdue      = len([b for b in bills if b.status == "overdue"])
    unpaid       = len([b for b in bills if b.status == "unpaid"])
    partial      = len([b for b in bills if b.status == "partial"])

    return {
        "total_bills":   total_bills,
        "total_amount":  round(total_amount, 2),
        "total_paid":    round(total_paid, 2),
        "outstanding":   round(outstanding, 2),
        "overdue_count": overdue,
        "unpaid_count":  unpaid,
        "partial_count": partial,
    }