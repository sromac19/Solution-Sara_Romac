"""
Integracijski testovi za sync servis - koristimo `respx` da mockamo
DummyJSON HTTP pozive (nikad ne gađamo pravi vanjski servis u testovima,
jer to čini testove sporima, nestabilnima i ovisnima o mreži/dostupnosti).
"""

import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tickethub.models.ticket import Ticket, TicketPriority, TicketStatus
from tickethub.services.dummyjson_client import DummyJSONClient
from tickethub.services.sync import sync_tickets_from_source


@pytest.mark.asyncio
@respx.mock
async def test_sync_creates_tickets_from_source(
    db_session: AsyncSession, sample_todos, sample_users
):
    respx.get("https://dummyjson.com/todos").mock(
        return_value=httpx.Response(200, json={"todos": sample_todos})
    )
    respx.get("https://dummyjson.com/users").mock(
        return_value=httpx.Response(200, json=sample_users)
    )

    result = await sync_tickets_from_source(db_session, client=DummyJSONClient())

    assert result == {"created": 3, "updated": 0}

    tickets = (await db_session.execute(select(Ticket))).scalars().all()
    assert len(tickets) == 3

    ticket_1 = next(t for t in tickets if t.source_id == 1)
    assert ticket_1.title == "Do the dishes"
    assert ticket_1.status == TicketStatus.open  # completed=False
    assert ticket_1.priority == TicketPriority.medium  # 1 % 3 == 1
    assert ticket_1.assignee == "emilys"

    ticket_2 = next(t for t in tickets if t.source_id == 2)
    assert ticket_2.status == TicketStatus.closed  # completed=True
    assert ticket_2.priority == TicketPriority.high  # 2 % 3 == 2


@pytest.mark.asyncio
@respx.mock
async def test_sync_upserts_existing_tickets(db_session: AsyncSession, sample_todos, sample_users):
    respx.get("https://dummyjson.com/todos").mock(
        return_value=httpx.Response(200, json={"todos": sample_todos})
    )
    respx.get("https://dummyjson.com/users").mock(
        return_value=httpx.Response(200, json=sample_users)
    )

    # Prvi sync - kreira 3 ticketa
    await sync_tickets_from_source(db_session, client=DummyJSONClient())

    # Promijenimo podatak na izvoru (simuliramo da je todo sad completed)
    updated_todos = [dict(t) for t in sample_todos]
    updated_todos[0]["completed"] = True

    respx.get("https://dummyjson.com/todos").mock(
        return_value=httpx.Response(200, json={"todos": updated_todos})
    )

    # Drugi sync - treba AŽURIRATI postojeći ticket, ne duplicirati
    result = await sync_tickets_from_source(db_session, client=DummyJSONClient())
    assert result == {"created": 0, "updated": 3}

    tickets = (await db_session.execute(select(Ticket))).scalars().all()
    assert len(tickets) == 3  # i dalje 3, nema duplikata

    ticket_1 = next(t for t in tickets if t.source_id == 1)
    assert ticket_1.status == TicketStatus.closed  # osvježeno iz izvora
