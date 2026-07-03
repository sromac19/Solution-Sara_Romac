"""
Entrypoint FastAPI aplikacije.

Pokretanje lokalno:  uvicorn tickethub.main:app --reload
Pokretanje u Dockeru: vidi Dockerfile / docker-compose.yml
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from tickethub.api import auth, system, tickets
from tickethub.core.background import periodic_sync_loop
from tickethub.core.config import get_settings
from tickethub.core.logging import configure_logging, get_logger
from tickethub.core.rate_limit import limiter

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pokrećem %s u '%s' okruženju", settings.app_name, settings.environment)
    sync_task = asyncio.create_task(periodic_sync_loop())
    yield
    sync_task.cancel()
    logger.info("Gašenje aplikacije...")


app = FastAPI(
    title="TicketHub",
    description="Middleware REST servis koji prikuplja, pohranjuje i izlaže support tickete.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(system.router)
