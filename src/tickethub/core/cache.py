"""
TTL cache s automatskim odabirom backend-a.

Ako je REDIS_URL postavljen (npr. u docker-compose.yml), cache koristi
Redis - bitno za scenarij s više instanci aplikacije koje trebaju dijeliti
cache. Ako REDIS_URL nije postavljen (npr. lokalni razvoj bez Dockera),
automatski se koristi in-memory rječnik - ista funkcionalnost, bez
vanjske ovisnosti. Odabir se radi jednom pri prvom pozivu (lazy), a kod
koji cache koristi (api/system.py) ne zna niti ne mari koji je backend
aktivan.
"""

import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

from tickethub.core.config import get_settings
from tickethub.core.logging import get_logger

logger = get_logger(__name__)

_memory_store: dict[str, tuple[float, Any]] = {}
_redis_client = None
_redis_unavailable = False


def _get_redis_client():
    """Lazy-inicijalizira Redis klijenta; vraća None ako Redis nije konfiguriran/dostupan."""
    global _redis_client, _redis_unavailable

    settings = get_settings()
    if not settings.redis_url or _redis_unavailable:
        return None

    if _redis_client is None:
        try:
            import redis.asyncio as redis

            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        except ImportError:
            logger.warning("redis paket nije instaliran - koristim in-memory cache fallback")
            _redis_unavailable = True
            return None

    return _redis_client


async def cached(key: str, fetch_fn: Callable[[], Awaitable[Any]]) -> Any:
    """Vraća cachiranu vrijednost ako nije istekla, inače poziva fetch_fn i cachira rezultat."""
    settings = get_settings()
    redis_client = _get_redis_client()

    if redis_client is not None:
        try:
            cached_value = await redis_client.get(key)
            if cached_value is not None:
                return json.loads(cached_value)

            value = await fetch_fn()
            await redis_client.set(key, json.dumps(value), ex=settings.cache_ttl_seconds)
            return value
        except Exception:
            # Redis je nedostupan usred rada (npr. kontejner se gasi) -
            # ne rušimo request, samo preskačemo cache za ovaj poziv.
            logger.warning("Redis cache nedostupan, preskačem cache za ključ '%s'", key)
            return await fetch_fn()

    # In-memory fallback
    now = time.monotonic()
    if key in _memory_store:
        cached_at, value = _memory_store[key]
        if now - cached_at < settings.cache_ttl_seconds:
            return value

    value = await fetch_fn()
    _memory_store[key] = (now, value)
    return value


def clear_cache() -> None:
    """Čisti in-memory cache - korisno u testovima da izbjegnemo curenje stanja."""
    _memory_store.clear()
