import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Vendor(Base):
    """Vendor of inventory items."""

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(5), default="en")
    email: Mapped[str | None] = mapped_column(String(120))

    prices: Mapped[list["VendorPrice"]] = relationship(
        "VendorPrice", back_populates="vendor", cascade="all, delete"
    )


class VendorPrice(Base):
    """Association table linking vendors to pricing."""

    __tablename__ = "vendor_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    moq: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="€")
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    vendor: Mapped[Vendor] = relationship("Vendor", back_populates="prices")

    __table_args__ = (UniqueConstraint("vendor_id", "sku", name="uq_vendor_sku"),)
