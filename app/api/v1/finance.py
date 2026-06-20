from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_finance
from app.schemas.finance import (
    ExpenseCreate, ExpenseUpdate, ExpenseOut,
    BudgetCreate, BudgetOut,
    GLCreate, GLOut,
    JournalEntryCreate, JournalEntryOut,
    COACreate, COAUpdate, COAOut,
    VendorBillCreate, VendorBillUpdate, VendorBillOut,
    VendorPaymentCreate, VendorPaymentOut
)
from app.services.finance_service import (
    create_expense, get_all_expenses, get_expenses_by_department, update_expense_status,
    create_budget, get_all_budgets, get_budget_by_department, get_over_budget_alerts,
    create_gl_entry, get_all_gl_entries, get_gl_by_account_type,
    get_finance_summary,
    get_profit_and_loss, get_cash_flow, get_expense_analysis,
    create_journal_entry, get_all_journal_entries, get_journal_entry_by_id, reverse_journal_entry,
    create_coa, get_all_coa, get_coa_by_type, update_coa, seed_default_coa,
    get_balance_sheet,
    create_vendor_bill, get_all_bills, get_bill_by_id, get_outstanding_bills,
    update_bill, create_vendor_payment, get_payments_by_bill, get_ap_summary
)
from app.services.export_service import (
    export_expense_pdf, export_expense_excel, export_pl_pdf
)

router = APIRouter()


# ── Expense ────────────────────────────────────────────

@router.post("/expense", response_model=ExpenseOut)
def submit_expense(data: ExpenseCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_expense(db, data, current_user.id)

@router.get("/expense", response_model=List[ExpenseOut])
def all_expenses(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_expenses(db)

@router.get("/expense/me", response_model=List[ExpenseOut])
def my_expenses(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.finance import Expense
    return db.query(Expense).filter(Expense.submitted_by == current_user.id).all()

@router.get("/expense/dept/{department}", response_model=List[ExpenseOut])
def expenses_by_dept(department: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_expenses_by_department(db, department)

@router.put("/expense/{expense_id}")
def update_expense(expense_id: int, data: ExpenseUpdate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    result = update_expense_status(db, expense_id, data, current_user.id)
    response = {"expense": result["expense"]}
    if result.get("over_budget"):
        response["warning"] = "⚠️ OVER BUDGET!"
        response["budget_info"] = result.get("budget_info")
    return response


# ── Budget ─────────────────────────────────────────────

@router.post("/budget", response_model=BudgetOut)
def add_budget(data: BudgetCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_budget(db, data, current_user.id)

@router.get("/budget", response_model=List[BudgetOut])
def all_budgets(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_budgets(db)

@router.get("/budget/dept/{department}", response_model=List[BudgetOut])
def budget_by_dept(department: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_budget_by_department(db, department)

@router.get("/budget/alerts")
def budget_alerts(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_over_budget_alerts(db)


# ── General Ledger ─────────────────────────────────────

@router.post("/gl", response_model=GLOut)
def add_gl(data: GLCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_gl_entry(db, data, current_user.id)

@router.get("/gl", response_model=List[GLOut])
def all_gl(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_gl_entries(db)

@router.get("/gl/{account_type}", response_model=List[GLOut])
def gl_by_type(account_type: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_gl_by_account_type(db, account_type)


# ── Summary ────────────────────────────────────────────

@router.get("/summary")
def finance_summary(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_finance_summary(db)


# ── Reports ────────────────────────────────────────────

@router.get("/reports/pl")
def profit_loss(month: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_profit_and_loss(db, month)

@router.get("/reports/cashflow")
def cash_flow(month: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_cash_flow(db, month)

@router.get("/reports/expense-analysis")
def expense_analysis(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_expense_analysis(db)

@router.get("/reports/balance-sheet")
def balance_sheet(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_balance_sheet(db)


# ── Journal Entries ────────────────────────────────────

@router.post("/journal", response_model=JournalEntryOut)
def add_journal(data: JournalEntryCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_journal_entry(db, data, current_user.id)

@router.get("/journal", response_model=List[JournalEntryOut])
def all_journals(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_journal_entries(db)

@router.get("/journal/{entry_id}", response_model=JournalEntryOut)
def get_journal(entry_id: int, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_journal_entry_by_id(db, entry_id)

@router.post("/journal/{entry_id}/reverse", response_model=JournalEntryOut)
def reverse_journal(entry_id: int, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return reverse_journal_entry(db, entry_id, current_user.id)


# ── Chart of Accounts ──────────────────────────────────

@router.post("/coa", response_model=COAOut)
def add_coa(data: COACreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_coa(db, data, current_user.id)

@router.get("/coa", response_model=List[COAOut])
def all_coa(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_coa(db)

@router.get("/coa/type/{account_type}", response_model=List[COAOut])
def coa_by_type(account_type: str, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_coa_by_type(db, account_type)

@router.put("/coa/{coa_id}", response_model=COAOut)
def edit_coa(coa_id: int, data: COAUpdate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return update_coa(db, coa_id, data)

@router.post("/coa/seed")
def seed_coa(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return seed_default_coa(db, current_user.id)


# ── Accounts Payable ───────────────────────────────────

@router.post("/ap/bill", response_model=VendorBillOut)
def add_bill(data: VendorBillCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_vendor_bill(db, data, current_user.id)

@router.get("/ap/bill", response_model=List[VendorBillOut])
def all_bills(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_all_bills(db)

@router.get("/ap/bill/outstanding", response_model=List[VendorBillOut])
def outstanding_bills(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_outstanding_bills(db)

@router.put("/ap/bill/{bill_id}", response_model=VendorBillOut)
def edit_bill(bill_id: int, data: VendorBillUpdate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return update_bill(db, bill_id, data)

@router.post("/ap/payment", response_model=VendorPaymentOut)
def make_payment(data: VendorPaymentCreate, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return create_vendor_payment(db, data, current_user.id)

@router.get("/ap/payment/{bill_id}", response_model=List[VendorPaymentOut])
def bill_payments(bill_id: int, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_payments_by_bill(db, bill_id)

@router.get("/ap/summary")
def ap_summary(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    return get_ap_summary(db)


# ── Export Reports ─────────────────────────────────────

@router.get("/export/expenses/pdf")
def export_expenses_pdf_route(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    expenses = get_all_expenses(db)
    buffer = export_expense_pdf(expenses)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=expense_report.pdf"})

@router.get("/export/expenses/excel")
def export_expenses_excel_route(db: Session = Depends(get_db), current_user=Depends(get_finance)):
    expenses = get_all_expenses(db)
    buffer = export_expense_excel(expenses)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=expense_report.xlsx"})

@router.get("/export/pl/pdf")
def export_pl_pdf_route(month: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_finance)):
    pl_data = get_profit_and_loss(db, month)
    buffer = export_pl_pdf(pl_data)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=profit_loss_report.pdf"})