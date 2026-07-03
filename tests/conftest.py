"""
Shared pytest fixtures.

Ključna odluka: svaki test dobiva svježu, izoliranu in-memory SQLite bazu
(preko StaticPool-a, jer in-memory SQLite inače "nestane" između konekcija).
To znači da se testovi mogu paralelno vrtjeti bez međusobnog utjecaja i bez
diranja stvarne lokalne tickethub.db datoteke.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from tickethub.core.cache import clear_cache
from tickethub.core.rate_limit import limiter
from tickethub.db.session import Base, get_db
from tickethub.main import app


@pytest.fixture(autouse=True)
def _reset_cache():
    """Cache je modul-level state - čistimo ga prije svakog testa da izbjegnemo curenje."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture(autouse=True)
def _disable_rate_limiting():
    """
    Rate limiter broji zahtjeve po IP-u i drži stanje u memoriji procesa.
    Test klijent (ASGITransport) šalje sve zahtjeve s istog "IP-a", pa bi
    se limit akumulirao kroz testove i lažno blokirao kasnije testove.
    Isključujemo ga globalno - dedicirani test rate-limitinga ga privremeno
    ponovno uključi (vidi test_rate_limiting.py).
    """
    limiter.enabled = False
    yield
    limiter.enabled = False


@pytest.fixture(autouse=True)
def _reset_cache():
    """Cache je modul-level state - čistimo ga prije svakog testa da izbjegnemo curenje."""
    clear_cache()
    yield
    clear_cache()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """
    Vraća Authorization header s valjanim TicketHub JWT-om, generiranim
    izravno preko create_access_token (bez HTTP poziva) - dovoljno za
    testiranje zaštićenih endpointa bez potrebe za mockanjem DummyJSON-a
    u svakom testu koji samo treba "biti ulogiran".
    """
    from tickethub.core.security import create_access_token

    token = create_access_token(username="testuser")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_todos() -> list[dict]:
    """Mockirani DummyJSON /todos odgovor - dovoljno raznolik za testiranje transformacija."""
    return [
        {"id": 1, "todo": "Do the dishes", "completed": False, "userId": 1},
        {"id": 2, "todo": "Buy groceries", "completed": True, "userId": 2},
        {"id": 3, "todo": "Walk the dog", "completed": False, "userId": 1},
    ]


@pytest.fixture
def sample_users() -> dict:
    """Mockirani DummyJSON /users odgovor."""
    return {"users": [{"id": 1, "username": "emilys"}, {"id": 2, "username": "michaelw"}]}
