from __future__ import annotations

from typing import Iterable, cast, Any

from sqlalchemy import create_engine, select, update, insert
from sqlalchemy.engine import Engine, CursorResult

from services.common.dsn import build_dsn
from .common import Base
from .common.models_vendor import Vendor, VendorPrice


class Repository:
    def __init__(self, engine: Engine | None = None):
        if engine is None:
            url = build_dsn(sync=True)
            engine = create_engine(url, future=True)
        self.engine = engine
        # ensure required tables exist, especially when using SQLite during tests
        Base.metadata.create_all(self.engine)

    def ensure_vendor(self, name: str) -> int:
        with self.engine.begin() as conn:
            try:
                r = conn.execute(select(Vendor.id).where(Vendor.name == name)).fetchone()
            except Exception:
                Base.metadata.create_all(self.engine)
                r = conn.execute(select(Vendor.id).where(Vendor.name == name)).fetchone()
            if r:
                return int(r[0])
            res = conn.execute(insert(Vendor).values(name=name).returning(Vendor.id))
            return int(res.scalar())

    def upsert_prices(
        self, vendor_id: int, rows: Iterable[dict], dry_run: bool = False
    ) -> tuple[int, int]:
        inserted = 0
        updated = 0
        with self.engine.begin() as conn:
            for row in rows:
                values = {
                    "vendor_id": vendor_id,
                    "sku": row.get("sku"),
                    "cost": row.get("cost"),
                    "moq": row.get("moq", 0),
                    "lead_time_days": row.get("lead_time_days", 0),
                    "currency": row.get("currency", "EUR"),
                }
                res = conn.execute(
                    update(VendorPrice)
                    .where(
                        VendorPrice.vendor_id == vendor_id,
                        VendorPrice.sku == values["sku"],
                    )
                    .values(**values)
                )
                if cast(CursorResult[Any], res).rowcount == 0:
                    if not dry_run:
                        conn.execute(insert(VendorPrice).values(**values))
                    inserted += 1
                else:
                    updated += 1
        return inserted, updated
