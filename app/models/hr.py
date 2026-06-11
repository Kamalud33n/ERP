from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Leave(Base):
    __tablename__ = "leaves"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type  = Column(String, nullable=False)  # annual | sick | unpaid | emergency
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    days        = Column(Integer, nullable=False)
    reason      = Column(String)
    status      = Column(String, default="pending")  # pending | approved | rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="leaves")


class Attendance(Base):
    __tablename__ = "attendance"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date        = Column(Date, nullable=False)
    check_in    = Column(DateTime, nullable=True)
    check_out   = Column(DateTime, nullable=True)
    status      = Column(String, default="present")  # present | absent | late | half_day
    created_at  = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="attendance")


class Payroll(Base):
    __tablename__ = "payrolls"

    id             = Column(Integer, primary_key=True, index=True)
    employee_id    = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month          = Column(String, nullable=False)  # 2024-06
    basic_salary   = Column(Float, default=0.0)
    allowances     = Column(Float, default=0.0)
    deductions     = Column(Float, default=0.0)
    net_salary     = Column(Float, default=0.0)
    status         = Column(String, default="pending")  # pending | processed | paid
    processed_by   = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at   = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="payrolls")