from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from sqlalchemy import create_engine, func, insert, literal_column, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from awa_common.base import Base
from awa_common.dsn import build_dsn
from awa_common.models_vendor import Vendor, VendorPrice

_TABLE_NAME = VendorPrice.__tablename__ or "vendor_prices"
_KEY_COLUMNS = ("vendor_id", "sku")
_UPDATE_COLUMNS = ("cost", "moq", "lead_time_days", "currency")


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

    def _prepare_row(self, vendor_id: int, row: Mapping[str, Any] | Any) -> dict[str, Any]:
        if is_dataclass(row):
            data = asdict(row)
        elif isinstance(row, Mapping):
            data = dict(row)
        else:
            data = {k: getattr(row, k) for k in ("sku", "unit_price", "currency", "moq", "lead_time_d")}
        unit_price = data.get("unit_price", data.get("cost"))
        currency = str(data.get("currency", "EUR") or "EUR").strip() or "EUR"
        lead_time = data.get("lead_time_d", data.get("lead_time_days", 0))
        return {
            "vendor_id": vendor_id,
            "sku": data.get("sku"),
            "cost": unit_price,
            "moq": data.get("moq", 0),
            "lead_time_days": lead_time,
            "currency": currency.upper(),
        }

    def upsert_prices(self, vendor_id: int, rows: Iterable[Any], dry_run: bool = False) -> tuple[int, int]:
        payload = [self._prepare_row(vendor_id, row) for row in rows]
        payload = [row for row in payload if row["sku"]]
        deduped: dict[tuple[int, str], dict[str, Any]] = {}
        duplicates = 0
        for row in payload:
            key = (row["vendor_id"], row["sku"])
            if key in deduped:
                duplicates += 1
            deduped[key] = row
        payload = list(deduped.values())
        if not payload:
            return 0, 0

        dialect = self.engine.dialect.name
        dispatcher = self._upsert_postgres if dialect == "postgresql" else self._upsert_generic

        if dry_run:
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    inserted, updated = dispatcher(conn, payload)
                finally:
                    trans.rollback()
            return inserted, updated + duplicates

        with self.engine.begin() as conn:
            inserted, updated = dispatcher(conn, payload)
            return inserted, updated + duplicates

    def _upsert_postgres(self, conn, rows: list[dict[str, Any]]) -> tuple[int, int]:
        table = VendorPrice.__table__
        stmt = pg_insert(table).values(rows)
        excluded = stmt.excluded
        update_values = {col: excluded[col] for col in _UPDATE_COLUMNS}
        update_values["updated_at"] = func.now()
        change_predicate = or_(
            table.c.cost.is_distinct_from(excluded.cost),
            table.c.moq.is_distinct_from(excluded.moq),
            table.c.lead_time_days.is_distinct_from(excluded.lead_time_days),
            table.c.currency.is_distinct_from(excluded.currency),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[table.c.vendor_id, table.c.sku],
            set_=update_values,
            where=change_predicate,
        ).returning(literal_column("xmax = 0").label("inserted_flag"))
        result = conn.execute(stmt)
        result_rows = result.fetchall()
        inserted = sum(1 for row in result_rows if bool(row.inserted_flag))
        updated = len(result_rows) - inserted
        return inserted, updated

    def _upsert_generic(self, conn, rows: list[dict[str, Any]]) -> tuple[int, int]:
        """Fallback path for SQLite and other dialects."""
        inserted = 0
        updated = 0
        for row in rows:
            existing = (
                conn.execute(
                    select(
                        VendorPrice.cost,
                        VendorPrice.moq,
                        VendorPrice.lead_time_days,
                        VendorPrice.currency,
                    ).where(VendorPrice.vendor_id == row["vendor_id"], VendorPrice.sku == row["sku"])
                )
                .mappings()
                .first()
            )
            if existing is None:
                conn.execute(insert(VendorPrice).values(**row))
                inserted += 1
                continue
            if not (
                existing["cost"] == row["cost"]
                and existing["moq"] == row["moq"]
                and existing["lead_time_days"] == row["lead_time_days"]
                and existing["currency"] == row["currency"]
            ):
                conn.execute(
                    update(VendorPrice)
                    .where(VendorPrice.vendor_id == row["vendor_id"], VendorPrice.sku == row["sku"])
                    .values(
                        cost=row["cost"],
                        moq=row["moq"],
                        lead_time_days=row["lead_time_days"],
                        currency=row["currency"],
                    )
                )
                updated += 1
        return inserted, updated
