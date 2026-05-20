from uuid_extensions import uuid7
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import OrderItemModel, OrderModel
from exchange_client import get_rate
from product_client import get_product_price
from schemas import (
    OrderDetailOut,
    OrderIn,
    OrderItemOut,
    OrderSummaryOut,
    ProductOut,
)


def _new_id() -> str:
    return str(uuid7())


async def create_order(
    payload: OrderIn,
    id_account: str,
    session: AsyncSession,
) -> OrderDetailOut:
    item_models: List[OrderItemModel] = []
    order_total = 0.0

    for item in payload.items:
        unit_price = await get_product_price(item.id_product, id_account)
        line_total = round(unit_price * item.quantity, 2)
        order_total += line_total

        item_models.append(
            OrderItemModel(
                id=_new_id(),
                id_product=item.id_product,
                quantity=item.quantity,
                unit_price=unit_price,
                total=line_total,
            )
        )

    order_total = round(order_total, 2)
    order = OrderModel(
        id=_new_id(),
        id_account=id_account,
        total=order_total,
        items=item_models,
    )

    session.add(order)
    await session.commit()
    await session.refresh(order)

    return _to_detail(order, "USD")


async def list_orders(
    id_account: str,
    session: AsyncSession,
) -> List[OrderSummaryOut]:
    result = await session.execute(
        select(OrderModel).where(OrderModel.id_account == id_account)
    )
    orders = result.scalars().all()
    return [
        OrderSummaryOut(id=o.id, date=o.date, total=o.total)
        for o in orders
    ]


async def get_order(
    id_order: str,
    id_account: str,
    currency: Optional[str],
    session: AsyncSession,
) -> OrderDetailOut:
    result = await session.execute(
        select(OrderModel).where(
            OrderModel.id == id_order,
            OrderModel.id_account == id_account,
        )
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    target_currency = currency.strip().upper() if currency else "USD"
    rate = await get_rate("USD", target_currency, id_account) if target_currency != "USD" else 1.0

    return _to_detail(order, target_currency, rate)


def _to_detail(order: OrderModel, currency: str, rate: float = 1.0) -> OrderDetailOut:
    items_out = [
        OrderItemOut(
            id=item.id,
            product=ProductOut(id=item.id_product),
            quantity=item.quantity,
            total=round(item.total * rate, 2),
        )
        for item in order.items
    ]
    return OrderDetailOut(
        id=order.id,
        date=order.date,
        currency=currency,
        items=items_out,
        total=round(order.total * rate, 2),
    )
