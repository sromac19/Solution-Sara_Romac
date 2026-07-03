"""
Pydantic sheme (v2) - odvojene od ORM modela namjerno (separation of concerns):
API ugovor (što klijent šalje/prima) ne mora biti 1:1 isto što je u bazi.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from tickethub.models.ticket import TicketPriority, TicketStatus


class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    status: TicketStatus = TicketStatus.open
    priority: TicketPriority = TicketPriority.medium
    assignee: str | None = Field(default=None, max_length=200)


class TicketCreate(TicketBase):
    """Ulazna shema za POST /tickets."""

    pass


class TicketUpdate(BaseModel):
    """
    Ulazna shema za PATCH /tickets/{id}.
    Svi atributi su opcionalni jer PATCH mijenja samo poslana polja.
    """

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assignee: str | None = Field(default=None, max_length=200)


class TicketListItem(BaseModel):
    """Skraćeni prikaz za GET /tickets (lista) - opis skraćen na <= 100 znakova."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TicketStatus
    priority: TicketPriority
    description: str | None = None

    @classmethod
    def from_orm_truncated(cls, ticket) -> "TicketListItem":
        desc = ticket.description
        if desc and len(desc) > 100:
            desc = desc[:97] + "..."
        return cls(
            id=ticket.id,
            title=ticket.title,
            status=ticket.status,
            priority=ticket.priority,
            description=desc,
        )


class TicketDetail(TicketBase):
    """Puni prikaz za GET /tickets/{id}, uključuje i originalni izvorni JSON."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int | None = None
    raw_source_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class PaginatedTickets(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    page_size: int
    pages: int
