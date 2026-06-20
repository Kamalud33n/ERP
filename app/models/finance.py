from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    amount      = Column(Float, nullable=False)
    category    = Column(String(50), nullable=False)  # travel | office | software | utilities | other
    department  = Column(String(100), nullable=False)
    date        = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(String(20), default="pending")  # pending | approved | rejected
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id          = Column(Integer, primary_key=True, index=True)
    department  = Column(String(100), nullable=False)
    category    = Column(String(100), nullable=False)
    amount      = Column(Float, nullable=False)
    spent       = Column(Float, default=0.0)
    month       = Column(String(20), nullable=False)  # 2024-06
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class GeneralLedger(Base):
    __tablename__ = "general_ledger"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(Date, nullable=False)
    description  = Column(String(255), nullable=False)
    debit        = Column(Float, default=0.0)
    credit       = Column(Float, default=0.0)
    balance      = Column(Float, default=0.0)
    account_type = Column(String(50), nullable=False)  # asset | liability | income | expense
    reference    = Column(String(100), nullable=True)
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id           = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(50), unique=True, nullable=False)  # JE-2024-0001
    date         = Column(Date, nullable=False)
    description  = Column(String(255), nullable=False)
    reference    = Column(String(100), nullable=True)
    status       = Column(String(20), default="draft")  # draft | posted | reversed
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    lines = relationship("JournalLine", back_populates="entry")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id           = Column(Integer, primary_key=True, index=True)
    entry_id     = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset | liability | income | expense
    description  = Column(String(255), nullable=True)
    debit        = Column(Float, default=0.0)
    credit       = Column(Float, default=0.0)

    entry = relationship("JournalEntry", back_populates="lines")


class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"

    id           = Column(Integer, primary_key=True, index=True)
    account_code = Column(String(20), unique=True, nullable=False)  # 1001, 2001, etc
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset | liability | equity | income | expense
    parent_id    = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)
    description  = Column(Text, nullable=True)
    is_active    = Column(Boolean, default=True)
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)


class VendorBill(Base):
    __tablename__ = "vendor_bills"

    id            = Column(Integer, primary_key=True, index=True)
    vendor_id     = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    bill_number   = Column(String(50), unique=True, nullable=False)  # BILL-2024-0001
    bill_date     = Column(Date, nullable=False)
    due_date      = Column(Date, nullable=True)
    amount        = Column(Float, nullable=False)
    paid_amount   = Column(Float, default=0.0)
    outstanding   = Column(Float, nullable=False)  # amount - paid_amount
    description   = Column(Text, nullable=True)
    status        = Column(String(20), default="unpaid")  # unpaid | partial | paid | overdue
    created_by    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    payments = relationship("VendorPayment", back_populates="bill")


class VendorPayment(Base):
    __tablename__ = "vendor_payments"

    id             = Column(Integer, primary_key=True, index=True)
    bill_id        = Column(Integer, ForeignKey("vendor_bills.id"), nullable=False)
    vendor_id      = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    payment_number = Column(String(50), unique=True, nullable=False)  # PAY-2024-0001
    payment_date   = Column(Date, nullable=False)
    amount         = Column(Float, nullable=False)
    payment_method = Column(String(50), default="bank_transfer")  # bank_transfer | cash | cheque
    reference      = Column(String(100), nullable=True)
    notes          = Column(Text, nullable=True)
    created_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)

    bill = relationship("VendorBill", back_populates="payments")