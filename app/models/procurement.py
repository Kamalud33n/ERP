from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(200), nullable=False)
    email        = Column(String(255), nullable=True)
    phone        = Column(String(20), nullable=True)
    address      = Column(Text, nullable=True)
    category     = Column(String(100), nullable=True)  # IT, Office, Maintenance...
    status       = Column(String(20), default="active")  # active | inactive
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(200), nullable=False)
    description   = Column(Text, nullable=True)
    quantity      = Column(Integer, nullable=False)
    estimated_cost= Column(Float, nullable=False)
    department    = Column(String(100), nullable=False)
    priority      = Column(String(20), default="medium")  # low | medium | high | urgent
    status        = Column(String(30), default="pending")  # pending | hr_approved | finance_approved | final_approved | rejected

    requested_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    hr_approved_by= Column(Integer, ForeignKey("users.id"), nullable=True)
    fin_approved_by= Column(Integer, ForeignKey("users.id"), nullable=True)
    final_approved_by= Column(Integer, ForeignKey("users.id"), nullable=True)

    hr_approved_at  = Column(DateTime, nullable=True)
    fin_approved_at = Column(DateTime, nullable=True)
    final_approved_at= Column(DateTime, nullable=True)

    created_at    = Column(DateTime, default=datetime.utcnow)

    purchase_order = relationship("PurchaseOrder", back_populates="purchase_request", uselist=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id                  = Column(Integer, primary_key=True, index=True)
    purchase_request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    vendor_id           = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    po_number           = Column(String(50), unique=True, nullable=False)
    quantity            = Column(Integer, nullable=False)
    unit_price          = Column(Float, nullable=False)
    total_amount        = Column(Float, nullable=False)
    delivery_date       = Column(Date, nullable=True)
    status              = Column(String(20), default="pending")  # pending | delivered | cancelled
    notes               = Column(Text, nullable=True)
    created_by          = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at          = Column(DateTime, default=datetime.utcnow)

    vendor           = relationship("Vendor", back_populates="purchase_orders")
    purchase_request = relationship("PurchaseRequest", back_populates="purchase_order")