from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    locale = Column(String(5), default="en")
    email = Column(String(120))

    prices = relationship("VendorPrice", back_populates="vendor", cascade="all, delete")


class VendorPrice(Base):
    __tablename__ = "vendor_prices"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    sku = Column(String, nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    moq = Column(Integer, default=0)
    lead_time_days = Column(Integer, default=0)
    currency = Column(String(3), default="€")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("Vendor", back_populates="prices")

    __table_args__ = (UniqueConstraint("vendor_id", "sku", name="uq_vendor_sku"),)
