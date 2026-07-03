"""
ORM model za Ticket.

Napomena o dizajnu:
- `id` je naš interni auto-increment primary key (vrijedi i za tickete
  sinkronizirane iz DummyJSON-a i za one kreirane kroz POST /tickets).
- `source_id` čuva izvorni ID iz DummyJSON-a (todo.id) kako bismo pri
  ponovnoj sinkronizaciji mogli prepoznati "isti" ticket i ažurirati ga
  umjesto duplicirati (upsert po source_id).
- `raw_source_json` čuva puni originalni JSON iz izvora radi endpointa
  GET /tickets/{id} koji traži "puni JSON iz izvora".
"""

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from tickethub.db.session import Base


class TicketStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), nullable=False, default=TicketStatus.open, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), nullable=False, default=TicketPriority.medium, index=True
    )

    assignee: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Puni originalni JSON iz DummyJSON-a (samo za sinkronizirane tickete)
    raw_source_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
