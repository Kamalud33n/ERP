from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, nullable=False)
    amount      = Column(Float, nullable=False)
    category    = Column(String, nullable=False)  # travel | office | software | utilities | other
    department  = Column(String, nullable=False)
    date        = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(String, default="pending")  # pending | approved | rejected
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id          = Column(Integer, primary_key=True, index=True)
    department  = Column(String, nullable=False)
    category    = Column(String, nullable=False)
    amount      = Column(Float, nullable=False)
    spent       = Column(Float, default=0.0)
    month       = Column(String, nullable=False)  # 2024-06
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class GeneralLedger(Base):
    __tablename__ = "general_ledger"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(Date, nullable=False)
    description  = Column(String, nullable=False)
    debit        = Column(Float, default=0.0)
    credit       = Column(Float, default=0.0)
    balance      = Column(Float, default=0.0)
    account_type = Column(String, nullable=False)  # asset | liability | income | expense
    reference    = Column(String, nullable=True)
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)