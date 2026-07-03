"""Sistemski endpointi: health-check, statistika, ručni okidač sync-a."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from tickethub.core.cache import cached
from tickethub.db.session import get_db
from tickethub.services import ticket_repository as repo
from tickethub.services.sync import sync_tickets_from_source

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check() -> dict:
    """Jednostavan health-check pogodan za Docker/k8s liveness probe."""
    return {"status": "ok"}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Agregirane statistike: ukupan broj ticketa po statusu i prioritetu.
    Cachirano na kratko (CACHE_TTL_SECONDS) jer se stats tipično prikazuju
    na dashboardu i ne moraju biti real-time do zadnje sekunde.
    """
    return await cached("stats", lambda: repo.get_stats(db))


@router.post("/sync", status_code=202)
async def trigger_sync(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Ručno pokreće sinkronizaciju iz DummyJSON-a (osim automatskog
    background job-a koji se vrti periodički - vidi core/background.py).
    """
    result = await sync_tickets_from_source(db)
    return {"message": "Sync dovršen", **result}
