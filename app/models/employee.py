from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name    = Column(String(100), nullable=False)
    last_name     = Column(String(100), nullable=False)
    phone         = Column(String(20))
    department    = Column(String(100))
    designation   = Column(String(100))
    salary        = Column(Float, default=0.0)
    join_date     = Column(Date)
    manager_id    = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    user         = relationship("User", back_populates="employee")
    leaves       = relationship("Leave", back_populates="employee")
    attendance   = relationship("Attendance", back_populates="employee")
    payrolls     = relationship("Payroll", back_populates="employee")
    manager      = relationship("Employee", remote_side="Employee.id",
                                foreign_keys="Employee.manager_id", backref="direct_reports")