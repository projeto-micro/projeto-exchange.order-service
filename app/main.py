from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, Query
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession

from database import create_tables, get_session
from order_service import create_order, get_order, list_orders
from schemas import OrderDetailOut, OrderIn, OrderSummaryOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Order API",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Order API"}


@app.get("/health-check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
async def info() -> dict[str, str]:
    return {
        "application": "order-service",
        "framework": "FastAPI",
        "status": "running",
    }


@app.post("/orders", response_model=OrderDetailOut, status_code=201)
async def post_order(
    payload: OrderIn,
    id_account: str = Header(..., alias="id-account"),
    session: AsyncSession = Depends(get_session),
) -> OrderDetailOut:
    return await create_order(payload, id_account, session)


@app.get("/orders", response_model=List[OrderSummaryOut])
async def get_orders(
    id_account: str = Header(..., alias="id-account"),
    session: AsyncSession = Depends(get_session),
) -> List[OrderSummaryOut]:
    return await list_orders(id_account, session)


@app.get("/orders/{id_order}", response_model=OrderDetailOut)
async def get_order_by_id(
    id_order: str,
    currency: Optional[str] = Query(default=None),
    id_account: str = Header(..., alias="id-account"),
    session: AsyncSession = Depends(get_session),
) -> OrderDetailOut:
    return await get_order(id_order, id_account, currency, session)
