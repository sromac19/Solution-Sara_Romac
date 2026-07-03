"""
Repository sloj: sadrži sve upite nad Ticket tablicom.

Razlog izdvajanja iz API routera: routeri bi trebali biti tanki (parsiranje
requesta, pozivanje servisa, vraćanje response-a), dok upitna logika
(filteri, paginacija, search) živi ovdje - lakše za testiranje i ponovno
korištenje (npr. background sync ili budući CLI alat).
"""

from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from tickethub.models.ticket import Ticket, TicketPriority, TicketStatus
from tickethub.schemas.ticket import TicketCreate, TicketUpdate


async def get_ticket_by_id(db: AsyncSession, ticket_id: int) -> Ticket | None:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalar_one_or_none()


async def list_tickets(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    search: str | None = None,
) -> tuple[list[Ticket], int]:
    """Vraća (stavke_na_stranici, ukupan_broj) uz opcionalne filtere i pretragu."""
    query = select(Ticket)
    count_query = select(func.count()).select_from(Ticket)

    if status is not None:
        query = query.where(Ticket.status == status)
        count_query = count_query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
        count_query = count_query.where(Ticket.priority == priority)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern)))
        count_query = count_query.where(
            or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern))
        )

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Ticket.id).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return list(items), total


def total_pages(total: int, page_size: int) -> int:
    return max(1, ceil(total / page_size))


async def create_ticket(db: AsyncSession, payload: TicketCreate) -> Ticket:
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def update_ticket(db: AsyncSession, ticket: Ticket, payload: TicketUpdate) -> Ticket:
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(ticket, field, value)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_stats(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(Ticket))).scalar_one()

    by_status_rows = (
        await db.execute(select(Ticket.status, func.count()).group_by(Ticket.status))
    ).all()
    by_priority_rows = (
        await db.execute(select(Ticket.priority, func.count()).group_by(Ticket.priority))
    ).all()

    return {
        "total": total,
        "by_status": {status.value: count for status, count in by_status_rows},
        "by_priority": {priority.value: count for priority, count in by_priority_rows},
    }
