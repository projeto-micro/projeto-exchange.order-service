import os
import time
from typing import Dict, Tuple

import httpx
from fastapi import HTTPException, status


CacheEntry = Tuple[float, float]

EXCHANGE_URL = os.getenv(
    "EXCHANGE_SERVICE_URL",
    "http://exchange:8080/exchanges/{from_currency}/{to_currency}",
)
REQUEST_TIMEOUT = float(os.getenv("EXCHANGE_REQUEST_TIMEOUT_SECONDS", "5"))
CACHE_TTL = int(os.getenv("EXCHANGE_CACHE_TTL_SECONDS", "60"))

_cache: Dict[str, CacheEntry] = {}


def _cache_key(from_currency: str, to_currency: str) -> str:
    return f"{from_currency}-{to_currency}"


def _read_cache(key: str) -> float | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    created_at, rate = entry
    if time.time() - created_at > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return rate


def _write_cache(key: str, rate: float) -> float:
    _cache[key] = (time.time(), rate)
    return rate


async def get_rate(from_currency: str, to_currency: str, id_account: str) -> float:
    """Return sell rate FROM → TO, using local cache when valid."""
    source = from_currency.strip().upper()
    target = to_currency.strip().upper()

    if source == target:
        return 1.0

    key = _cache_key(source, target)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    url = EXCHANGE_URL.format(from_currency=source, to_currency=target)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers={"id-account": id_account})
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Exchange service rejected {source}-{target}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Exchange service is unavailable",
        ) from exc

    payload = response.json()
    try:
        rate = float(payload["sell"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Exchange service returned an invalid payload",
        ) from exc

    return _write_cache(key, rate)
