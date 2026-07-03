"""
REST endpointi za tickete.

Napomena o redoslijedu ruta: /tickets/search MORA biti definiran PRIJE
/tickets/{ticket_id}, inače bi FastAPI pokušao "search" parsirati kao
ticket_id (int) i vratio 422 grešku umjesto da pogodi search rutu.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from tickethub.core.rate_limit import limiter
from tickethub.core.security import get_current_username
from tickethub.db.session import get_db
from tickethub.models.ticket import TicketPriority, TicketStatus
from tickethub.schemas.ticket import (
    PaginatedTickets,
    TicketCreate,
    TicketDetail,
    TicketListItem,
    TicketUpdate,
)
from tickethub.services import ticket_repository as repo

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=PaginatedTickets)
async def list_tickets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedTickets:
    """Paginirana lista ticketa, uz opcionalno filtriranje po statusu i prioritetu."""
    items, total = await repo.list_tickets(
        db, page=page, page_size=page_size, status=status_filter, priority=priority
    )
    return PaginatedTickets(
        items=[TicketListItem.from_orm_truncated(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=repo.total_pages(total, page_size),
    )


@router.get("/search", response_model=PaginatedTickets)
async def search_tickets(
    q: str = Query(..., min_length=1, description="Tekst za pretragu po naslovu/opisu"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedTickets:
    """Pretraga ticketa po naslovu (i opisu) - case-insensitive substring match."""
    items, total = await repo.list_tickets(db, page=page, page_size=page_size, search=q)
    return PaginatedTickets(
        items=[TicketListItem.from_orm_truncated(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=repo.total_pages(total, page_size),
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)) -> TicketDetail:
    ticket = await repo.get_ticket_by_id(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nije pronađen")
    return TicketDetail.model_validate(ticket)


@router.post("", response_model=TicketDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_ticket(
    request: Request,
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_username),
) -> TicketDetail:
    """Zahtijeva Authorization: Bearer <token> (vidi POST /auth/login)."""
    ticket = await repo.create_ticket(db, payload)
    return TicketDetail.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketDetail)
@limiter.limit("20/minute")
async def update_ticket(
    request: Request,
    ticket_id: int,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_username),
) -> TicketDetail:
    """Zahtijeva Authorization: Bearer <token> (vidi POST /auth/login)."""
    ticket = await repo.get_ticket_by_id(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nije pronađen")
    updated = await repo.update_ticket(db, ticket, payload)
    return TicketDetail.model_validate(updated)
