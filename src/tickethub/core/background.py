"""
Pozadinski (background) sync job.

Koristi asyncio.create_task pokrenut unutar FastAPI lifespan handlera -
nema potrebe za vanjskim schedulerom (Celery i sl.) za ovako jednostavan
periodički zadatak, što drži projekt jednostavnijim za pokretanje.
"""

import asyncio

from tickethub.core.config import get_settings
from tickethub.core.logging import get_logger
from tickethub.db.session import AsyncSessionLocal
from tickethub.services.sync import sync_tickets_from_source

logger = get_logger(__name__)


async def periodic_sync_loop() -> None:
    settings = get_settings()
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await sync_tickets_from_source(db)
        except Exception:
            logger.exception("Background sync job je pao - pokušavam ponovno za %s sekundi",
                              settings.sync_interval_seconds)
        await asyncio.sleep(settings.sync_interval_seconds)
