"""Testovi za /auth/login i rate limiting."""

import httpx
import pytest
import respx
from httpx import AsyncClient
from tickethub.core.rate_limit import limiter
from tickethub.core.security import decode_access_token


@pytest.mark.asyncio
@respx.mock
async def test_login_success_returns_valid_token(client: AsyncClient):
    respx.post("https://dummyjson.com/auth/login").mock(
        return_value=httpx.Response(200, json={"id": 1, "username": "emilys"})
    )

    response = await client.post(
        "/auth/login", json={"username": "emilys", "password": "emilyspass"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]

    # Token mora biti dekodabilan i sadržavati ispravan username
    username = decode_access_token(data["access_token"])
    assert username == "emilys"


@pytest.mark.asyncio
@respx.mock
async def test_login_failure_returns_401(client: AsyncClient):
    respx.post("https://dummyjson.com/auth/login").mock(
        return_value=httpx.Response(400, json={"message": "Invalid credentials"})
    )

    response = await client.post(
        "/auth/login", json={"username": "emilys", "password": "wrong-password"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limiting_blocks_after_threshold(client: AsyncClient, auth_headers: dict):
    """
    Dedicirani test rate limitinga - privremeno ponovno uključi limiter
    (globalno je isključen u conftest.py radi stabilnosti ostalih testova),
    pošalje više zahtjeva nego dopušteno (10/minute na POST /tickets) i
    provjeri da server na kraju vrati 429.
    """
    limiter.enabled = True
    try:
        responses = []
        for i in range(12):
            r = await client.post(
                "/tickets", json={"title": f"Rate limit test {i}"}, headers=auth_headers
            )
            responses.append(r.status_code)

        assert 429 in responses, f"Očekivan barem jedan 429 odgovor, dobiveno: {responses}"
    finally:
        limiter.enabled = False
