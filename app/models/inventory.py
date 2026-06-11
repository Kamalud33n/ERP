from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Item(Base):
    __tablename__ = "items"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String, nullable=False)
    sku           = Column(String, unique=True, nullable=False)
    category      = Column(String, nullable=False)
    unit          = Column(String, nullable=False)  # pcs, kg, ltr, box...
    description   = Column(Text, nullable=True)
    current_stock = Column(Float, default=0.0)
    min_stock     = Column(Float, default=0.0)     # low stock alert threshold
    unit_price    = Column(Float, default=0.0)
    is_active     = Column(Boolean, default=True)
    created_by    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    movements = relationship("StockMovement", back_populates="item")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id          = Column(Integer, primary_key=True, index=True)
    item_id     = Column(Integer, ForeignKey("items.id"), nullable=False)
    type        = Column(String, nullable=False)   # in | out | adjustment
    quantity    = Column(Float, nullable=False)
    reference   = Column(String, nullable=True)    # PO number, manual, etc
    note        = Column(Text, nullable=True)
    done_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="movements")