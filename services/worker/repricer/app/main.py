from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from typing import Iterable

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.db import get_session

from .logic import (
    DEFAULT_MIN_ROI,
    DEFAULT_QUANT,
    DEFAULT_UNDERCUT,
    compute_price,
    decide_price,
)
from .schemas import (
    ApplyRequest,
    ApplyResponse,
    PriceRequest,
    PriceResponse,
    SimItem,
    SimulateRequest,
    SimulateResponse,
    SimulateResult,
)

app = FastAPI(title="AWA Repricer")

QUERY_REPRICER_INPUT = text(
    """
    SELECT cost, fees, buybox_price
    FROM v_roi_full
    WHERE asin = :asin
    """
)


def _load_decimal_env(name: str, default: Decimal) -> Decimal:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return default
    return value


MIN_ROI = _load_decimal_env("REPRICER_MIN_ROI", DEFAULT_MIN_ROI)
UNDERCUT = _load_decimal_env("REPRICER_BUYBOX_GAP", DEFAULT_UNDERCUT)
ROUNDING = _load_decimal_env("REPRICER_ROUND", DEFAULT_QUANT)


def _strategy_label(applied: Iterable[str]) -> str:
    order = {"min_roi": 0, "buybox_gap": 1, "map": 2}

    def sort_key(name: str) -> int:
        return order.get(name, 99)

    applied_sorted = sorted(set(applied), key=sort_key)
    if not applied_sorted:
        return "unknown"
    return "+".join(applied_sorted)


async def _fetch_inputs(session: AsyncSession, asin: str) -> dict:
    result = await session.execute(QUERY_REPRICER_INPUT, {"asin": asin})
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"ASIN {asin} not found")
    return dict(row)


def _build_sim_request_items(payload: SimulateRequest) -> list[SimItem]:
    items: list[SimItem] = []
    if payload.items:
        items.extend(payload.items)
    if payload.asin:
        items.append(SimItem(asin=payload.asin, map_price=None))
    return items


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.post("/price", response_model=PriceResponse, tags=["pricing"])
async def price(req: PriceRequest):
    new_price = compute_price(req.asin, req.our_cost, req.fee_estimate)
    return PriceResponse(asin=req.asin, new_price=new_price)


@app.post(
    "/pricing/simulate",
    response_model=SimulateResponse,
    tags=["pricing"],
)
async def simulate(
    req: SimulateRequest, session: AsyncSession = Depends(get_session)
) -> SimulateResponse:
    items = _build_sim_request_items(req)
    if not items:
        raise HTTPException(status_code=400, detail="No ASINs provided")

    results: list[SimulateResult] = []
    for item in items:
        inputs = await _fetch_inputs(session, item.asin)
        price, explain = decide_price(
            item.asin,
            inputs["cost"],
            inputs["fees"],
            buybox=inputs.get("buybox_price"),
            map_price=item.map_price,
            min_roi=MIN_ROI,
            undercut=UNDERCUT,
            quant=ROUNDING,
        )
        strategy = _strategy_label(explain.get("applied", []))
        results.append(
            SimulateResult(
                asin=item.asin,
                new_price=price,
                strategy=strategy,
                context=explain,
            )
        )

    return SimulateResponse(results=results)


def _prepare_context(
    explain: dict, note: str | None, map_price: Decimal | None
) -> dict:
    context = dict(explain)
    if note:
        context["note"] = note
    if map_price is not None:
        context["map_price"] = map_price
    return context


async def _log_price_update(
    session: AsyncSession,
    asin: str,
    old_price: Decimal | None,
    new_price: Decimal,
    strategy: str,
    context: dict,
) -> None:
    payload = {
        "asin": asin,
        "old_price": old_price,
        "new_price": new_price,
        "strategy": strategy,
        "context": json.dumps(context, default=str),
    }
    await session.execute(
        text(
            """
            INSERT INTO price_updates_log (
                asin,
                old_price,
                new_price,
                strategy,
                actor,
                context
            )
            VALUES (
                :asin,
                :old_price,
                :new_price,
                :strategy,
                'repricer',
                :context::jsonb
            )
            """
        ),
        payload,
    )


@app.post(
    "/pricing/apply",
    response_model=ApplyResponse,
    tags=["pricing"],
)
async def apply_prices(
    req: ApplyRequest, session: AsyncSession = Depends(get_session)
) -> ApplyResponse:
    if not req.items:
        raise HTTPException(status_code=400, detail="No ASINs provided")

    results: list[dict] = []
    applied_count = 0

    for item in req.items:
        changed = item.old_price is None or item.old_price != item.new_price
        context = {}

        if not req.dry_run:
            inputs = await _fetch_inputs(session, item.asin)
            _, explain = decide_price(
                item.asin,
                inputs["cost"],
                inputs["fees"],
                buybox=inputs.get("buybox_price"),
                map_price=item.map_price,
                min_roi=MIN_ROI,
                undercut=UNDERCUT,
                quant=ROUNDING,
            )
            context = _prepare_context(explain, item.note, item.map_price)
            await _log_price_update(
                session,
                item.asin,
                item.old_price,
                item.new_price,
                item.strategy,
                context,
            )
            applied_count += 1

        results.append({"asin": item.asin, "changed": changed})

    if not req.dry_run:
        await session.commit()

    return ApplyResponse(applied=applied_count, results=results)


async def full(session: AsyncSession) -> list[PriceResponse]:
    result = await session.execute(
        text("SELECT asin, our_cost, fee_estimate FROM repricer_input")
    )
    rows = result.fetchall()
    out: list[PriceResponse] = []
    for asin, cost, fee in rows:
        out.append(PriceResponse(asin=asin, new_price=compute_price(asin, cost, fee)))
    return out
