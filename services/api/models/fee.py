from sqlalchemy import Column, DateTime, Numeric, String, func

from awa_common.base import Base


class Fee(Base):
    __tablename__ = "fees_raw"

    asin = Column(String, primary_key=True)
    fulfil_fee = Column(Numeric(10, 2), nullable=False)
    referral_fee = Column(Numeric(10, 2), nullable=False)
    storage_fee = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="€")
    captured_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
