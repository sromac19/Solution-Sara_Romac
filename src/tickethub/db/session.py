"""
Async database setup.

Koristimo SQLAlchemy 2.x async engine. Podržava i SQLite (lokalni dev,
brz start bez vanjskih servisa) i PostgreSQL (produkcija/Docker Compose) -
jedina razlika je DATABASE_URL varijabla, kod se ne mijenja.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from tickethub.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Zajednička baza za sve ORM modele."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency koji daje po jednu sesiju po requestu i
    garantira da se ona zatvori (i rollbacka u slučaju greške) na kraju.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
