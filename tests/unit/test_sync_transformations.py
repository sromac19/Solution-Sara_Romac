"""
Unit testovi za čistu transformacijsku logiku (bez baze, bez mreže) -
najbrži i najstabilniji sloj testova, provjerava pravila iz specifikacije:
- status: completed -> closed / open
- priority: id % 3 -> low/medium/high
"""

import pytest
from tickethub.models.ticket import TicketPriority, TicketStatus
from tickethub.services.sync import compute_priority, compute_status


@pytest.mark.parametrize(
    "completed,expected",
    [
        (True, TicketStatus.closed),
        (False, TicketStatus.open),
    ],
)
def test_compute_status(completed, expected):
    assert compute_status(completed) == expected


@pytest.mark.parametrize(
    "source_id,expected",
    [
        (0, TicketPriority.low),
        (1, TicketPriority.medium),
        (2, TicketPriority.high),
        (3, TicketPriority.low),
        (99, TicketPriority.low),  # 99 % 3 == 0 -> low
        (100, TicketPriority.medium),  # 100 % 3 == 1 -> medium
    ],
)
def test_compute_priority(source_id, expected):
    assert compute_priority(source_id) == expected
