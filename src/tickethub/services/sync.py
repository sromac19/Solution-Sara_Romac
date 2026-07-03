"""
Sync servis: dohvaća podatke iz DummyJSON-a, transformira ih u naš
Ticket model i sprema (upsert) u lokalnu bazu.

Pravila transformacije (iz specifikacije zadatka):
- title       <- todo["todo"]
- status      <- "closed" ako je todo["completed"] == True, inače "open"
- priority    <- id % 3 -> 0: low, 1: medium, 2: high
- assignee    <- username korisnika s odgovarajućim userId
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tickethub.core.logging import get_logger
from tickethub.models.ticket import Ticket, TicketPriority, TicketStatus
from tickethub.services.dummyjson_client import DummyJSONClient

logger = get_logger(__name__)

_PRIORITY_BY_MOD = {
    0: TicketPriority.low,
    1: TicketPriority.medium,
    2: TicketPriority.high,
}


def compute_priority(source_id: int) -> TicketPriority:
    return _PRIORITY_BY_MOD[source_id % 3]


def compute_status(completed: bool) -> TicketStatus:
    return TicketStatus.closed if completed else TicketStatus.open


async def sync_tickets_from_source(
    db: AsyncSession, client: DummyJSONClient | None = None
) -> dict[str, int]:
    """
    Puni lokalnu bazu ticketima iz DummyJSON-a.

    Upsert logika: ako ticket sa zadanim source_id već postoji, ažuriramo
    ga (osim polja koja je korisnik ručno promijenio preko PATCH-a -
    to bismo u naprednijoj verziji rješavali "dirty" flagom; za potrebe
    zadatka held simple: sync uvijek osvježi podatke iz izvora).

    Vraća statistiku {"created": N, "updated": N} korisnu za logging/response.
    """
    client = client or DummyJSONClient()

    todos = await client.fetch_todos()
    users_by_id = await client.fetch_users()

    existing_result = await db.execute(select(Ticket).where(Ticket.source_id.is_not(None)))
    existing_by_source_id = {t.source_id: t for t in existing_result.scalars().all()}

    created, updated = 0, 0

    for todo in todos:
        source_id = todo["id"]
        user_id = todo.get("userId")
        assignee = users_by_id.get(user_id, f"user-{user_id}")

        title = todo["todo"]
        status = compute_status(todo.get("completed", False))
        priority = compute_priority(source_id)

        existing = existing_by_source_id.get(source_id)
        if existing:
            existing.title = title
            existing.status = status
            existing.priority = priority
            existing.assignee = assignee
            existing.raw_source_json = todo
            updated += 1
        else:
            ticket = Ticket(
                source_id=source_id,
                title=title,
                description=title,
                status=status,
                priority=priority,
                assignee=assignee,
                raw_source_json=todo,
            )
            db.add(ticket)
            created += 1

    await db.commit()
    logger.info("Sync završen: %d novih, %d ažuriranih ticketa", created, updated)
    return {"created": created, "updated": updated}
