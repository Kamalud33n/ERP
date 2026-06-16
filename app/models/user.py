from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    email       = Column(String(255), unique=True, index=True, nullable=False)
    username    = Column(String(100), unique=True, index=True, nullable=False)
    password    = Column(String(255), nullable=False)
    role        = Column(String(50), default="employee")  # admin | hr_manager | finance | employee
    is_active   = Column(Boolean, default=True)
    mfa_secret  = Column(String(255), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="user", uselist=False)