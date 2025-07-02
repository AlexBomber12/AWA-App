from fastapi import FastAPI
from .schemas import PriceRequest, PriceResponse
from .logic import compute_price

app = FastAPI(title="AWA Repricer")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.post("/price", response_model=PriceResponse, tags=["pricing"])
async def price(req: PriceRequest):
    new_price = compute_price(req.asin, req.our_cost, req.fee_estimate)
    return PriceResponse(asin=req.asin, new_price=new_price)
