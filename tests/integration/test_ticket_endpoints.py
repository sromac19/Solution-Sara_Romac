"""Integracijski testovi za /tickets endpointe (kroz pravu FastAPI app + in-memory bazu)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_ticket(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/tickets",
        json={"title": "Novi ticket", "description": "Opis", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Novi ticket"
    assert data["status"] == "open"  # default
    assert data["priority"] == "high"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_ticket_requires_auth(client: AsyncClient):
    """POST /tickets bez Authorization headera mora vratiti 401."""
    response = await client.post("/tickets", json={"title": "Bez tokena"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_ticket_validation_error(client: AsyncClient, auth_headers: dict):
    # title je obavezan (min_length=1) - prazan title mora vratiti 422
    response = await client.post("/tickets", json={"title": ""}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_ticket_not_found(client: AsyncClient):
    response = await client.get("/tickets/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ticket_detail(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/tickets", json={"title": "Detail test"}, headers=auth_headers
    )
    ticket_id = create_resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Detail test"


@pytest.mark.asyncio
async def test_list_tickets_pagination(client: AsyncClient, auth_headers: dict):
    for i in range(5):
        await client.post("/tickets", json={"title": f"Ticket {i}"}, headers=auth_headers)

    response = await client.get("/tickets", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_list_tickets_description_truncated(client: AsyncClient, auth_headers: dict):
    long_description = "x" * 200
    await client.post(
        "/tickets",
        json={"title": "Long desc", "description": long_description},
        headers=auth_headers,
    )

    response = await client.get("/tickets")
    item = response.json()["items"][0]
    assert len(item["description"]) <= 100


@pytest.mark.asyncio
async def test_filter_by_status_and_priority(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/tickets",
        json={"title": "A", "status": "open", "priority": "low"},
        headers=auth_headers,
    )
    await client.post(
        "/tickets",
        json={"title": "B", "status": "closed", "priority": "high"},
        headers=auth_headers,
    )

    response = await client.get("/tickets", params={"status": "closed", "priority": "high"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "B"


@pytest.mark.asyncio
async def test_search_tickets(client: AsyncClient, auth_headers: dict):
    await client.post("/tickets", json={"title": "Printer is broken"}, headers=auth_headers)
    await client.post("/tickets", json={"title": "VPN not working"}, headers=auth_headers)

    response = await client.get("/tickets/search", params={"q": "printer"})
    data = response.json()
    assert data["total"] == 1
    assert "Printer" in data["items"][0]["title"]


@pytest.mark.asyncio
async def test_patch_ticket_partial_update(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/tickets",
        json={"title": "Original", "status": "open", "priority": "low"},
        headers=auth_headers,
    )
    ticket_id = create_resp.json()["id"]

    response = await client.patch(
        f"/tickets/{ticket_id}", json={"status": "closed"}, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["title"] == "Original"  # nepromijenjeno polje ostaje isto
    assert data["priority"] == "low"  # nepromijenjeno polje ostaje isto


@pytest.mark.asyncio
async def test_patch_ticket_requires_auth(client: AsyncClient):
    response = await client.patch("/tickets/1", json={"status": "closed"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_ticket_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.patch(
        "/tickets/9999", json={"status": "closed"}, headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/tickets",
        json={"title": "A", "status": "open", "priority": "low"},
        headers=auth_headers,
    )
    await client.post(
        "/tickets",
        json={"title": "B", "status": "closed", "priority": "high"},
        headers=auth_headers,
    )

    response = await client.get("/stats")
    data = response.json()
    assert data["total"] == 2
    assert data["by_status"]["open"] == 1
    assert data["by_status"]["closed"] == 1
