from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .logic import compute_price
from .schemas import PriceRequest, PriceResponse

app = FastAPI(title="AWA Repricer")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.post("/price", response_model=PriceResponse, tags=["pricing"])
async def price(req: PriceRequest):
    new_price = compute_price(req.asin, req.our_cost, req.fee_estimate)
    return PriceResponse(asin=req.asin, new_price=new_price)


async def full(session: AsyncSession) -> list[PriceResponse]:
    result = await session.execute(
        text("SELECT asin, our_cost, fee_estimate FROM repricer_input")
    )
    rows = result.fetchall()
    out: list[PriceResponse] = []
    for asin, cost, fee in rows:
        out.append(PriceResponse(asin=asin, new_price=compute_price(asin, cost, fee)))
    return out
