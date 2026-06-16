from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(200), nullable=False)
    asset_code      = Column(String(50), unique=True, nullable=False)  # auto generate
    category        = Column(String(100), nullable=False)   # IT, Furniture, Vehicle, Equipment
    serial_number   = Column(String(100), nullable=True)
    location        = Column(String(200), nullable=True)
    department      = Column(String(100), nullable=True)
    purchase_date   = Column(Date, nullable=True)
    purchase_price  = Column(Float, default=0.0)
    current_value   = Column(Float, default=0.0)
    depreciation_rate = Column(Float, default=0.0)   # % per year
    status          = Column(String(20), default="active")  # active | under_repair | disposed | lost
    description     = Column(Text, nullable=True)
    assigned_to     = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_by      = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    maintenance_logs = relationship("MaintenanceLog", back_populates="asset")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id           = Column(Integer, primary_key=True, index=True)
    asset_id     = Column(Integer, ForeignKey("assets.id"), nullable=False)
    type         = Column(String(50), nullable=False)   # preventive | corrective | inspection
    description  = Column(Text, nullable=False)
    cost         = Column(Float, default=0.0)
    maintenance_date = Column(Date, nullable=False)
    next_due_date    = Column(Date, nullable=True)
    status       = Column(String(20), default="completed")  # scheduled | in_progress | completed
    done_by      = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="maintenance_logs")