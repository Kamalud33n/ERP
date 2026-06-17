from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Leave(Base):
    __tablename__ = "leaves"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type  = Column(String(50), nullable=False)  # annual | sick | unpaid | emergency
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    days        = Column(Integer, nullable=False)
    reason      = Column(Text)
    status      = Column(String(20), default="pending")  # pending | approved | rejected
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
    status      = Column(String(20), default="present")  # present | absent | late | half_day
    created_at  = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="attendance")


class Payroll(Base):
    __tablename__ = "payrolls"

    id             = Column(Integer, primary_key=True, index=True)
    employee_id    = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month          = Column(String(20), nullable=False)  # 2024-06
    basic_salary   = Column(Float, default=0.0)
    allowances     = Column(Float, default=0.0)
    deductions     = Column(Float, default=0.0)
    net_salary     = Column(Float, default=0.0)
    status         = Column(String(20), default="pending")  # pending | processed | paid
    processed_by   = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at   = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="payrolls")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id          = Column(Integer, primary_key=True, index=True)
    action      = Column(String(50), nullable=False)   # approved_leave | rejected_leave | approved_expense | rejected_expense | processed_payroll
    module      = Column(String(50), nullable=False)   # hr | finance | payroll
    reference_id= Column(Integer, nullable=False)  # leave_id | expense_id | payroll_id
    done_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    done_by_role= Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    reversed    = Column(Boolean, default=False)
    reversed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Contract(Base):
    __tablename__ = "contracts"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(Integer, ForeignKey("employees.id"), nullable=False)
    contract_type = Column(String(50), nullable=False)   # full_time | part_time | contract | internship
    start_date    = Column(Date, nullable=False)
    end_date      = Column(Date, nullable=True)       # null = permanent
    salary        = Column(Float, nullable=False)
    position      = Column(String(100), nullable=False)
    department    = Column(String(100), nullable=False)
    status        = Column(String(20), default="active")  # active | expired | terminated
    notes         = Column(Text, nullable=True)
    created_by    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="contracts")


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id             = Column(Integer, primary_key=True, index=True)
    employee_id    = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewer_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    period         = Column(String(20), nullable=False)   # 2024-Q1 | 2024-H1 | 2024
    rating         = Column(Float, nullable=False)    # 1.0 - 5.0
    kpi_score      = Column(Float, default=0.0)       # 0 - 100
    attendance_score = Column(Float, default=0.0)     # 0 - 100
    teamwork_score = Column(Float, default=0.0)       # 0 - 100
    technical_score= Column(Float, default=0.0)       # 0 - 100
    comments       = Column(Text, nullable=True)
    goals          = Column(Text, nullable=True)
    status         = Column(String(20), default="draft")  # draft | submitted | acknowledged
    created_at     = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="performance_reviews")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id            = Column(Integer, primary_key=True, index=True)
    employee_id   = Column(Integer, ForeignKey("employees.id"), nullable=False)
    doc_type      = Column(String(50), nullable=False)   # offer_letter | id_proof | contract | certificate | other
    doc_name      = Column(String(255), nullable=False)
    file_path     = Column(String(500), nullable=False)
    file_size     = Column(String(50), nullable=True)
    uploaded_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="documents")


class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title       = Column(String(255), nullable=False)
    message     = Column(Text, nullable=False)
    type        = Column(String(50), default="info")   # info | warning | success | alert
    module      = Column(String(50), nullable=True)     # hr | finance | admin | system
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)   