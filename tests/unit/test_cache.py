"""Unit test za in-memory TTL cache fallback (bez Redisa)."""

import pytest
from tickethub.core.cache import cached, clear_cache


@pytest.mark.asyncio
async def test_cached_returns_fresh_value_on_first_call():
    clear_cache()
    calls = []

    async def fetch():
        calls.append(1)
        return {"value": 42}

    result = await cached("test-key", fetch)
    assert result == {"value": 42}
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_cached_reuses_value_within_ttl():
    clear_cache()
    calls = []

    async def fetch():
        calls.append(1)
        return {"count": len(calls)}

    first = await cached("test-key-2", fetch)
    second = await cached("test-key-2", fetch)

    # fetch_fn se poziva samo jednom - drugi poziv vraća cachiranu vrijednost
    assert first == second
    assert len(calls) == 1
