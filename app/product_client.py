import os

import httpx
from fastapi import HTTPException, status


PRODUCT_URL = os.getenv(
    "PRODUCT_SERVICE_URL",
    "http://product:8080/products/{id_product}",
)
REQUEST_TIMEOUT = float(os.getenv("PRODUCT_REQUEST_TIMEOUT_SECONDS", "5"))


async def get_product_price(id_product: str, id_account: str) -> float:
    """Fetch product price from the Product service."""
    url = PRODUCT_URL.format(id_product=id_product)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers={"id-account": id_account})
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product {id_product} not found",
                )
            response.raise_for_status()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Product service rejected the request",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Product service is unavailable",
        ) from exc

    payload = response.json()
    try:
        return float(payload["price"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Product service returned an invalid payload",
        ) from exc
