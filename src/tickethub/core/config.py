"""
Centralizirana konfiguracija aplikacije.

Koristimo pydantic-settings kako bismo sve env varijable validirali na
startu aplikacije (fail-fast), umjesto da greške u konfiguraciji otkrivamo
tek kad neki endpoint padne u runtime-u.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Aplikacija
    app_name: str = "TicketHub"
    environment: str = "local"  # local | ci | production
    log_level: str = "INFO"

    # Baza podataka
    # Lokalno koristimo SQLite (async preko aiosqlite), u Compose/produkciji
    # možemo prebaciti na PostgreSQL (async preko asyncpg) samo promjenom ove varijable.
    database_url: str = "sqlite+aiosqlite:///./tickethub.db"

    # Vanjski izvor podataka
    dummyjson_base_url: str = "https://dummyjson.com"
    dummyjson_todos_limit: int = 150  # DummyJSON ima ukupno 150 todo zapisa

    # Sigurnost (za bonus JWT auth)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Background sync
    sync_interval_seconds: int = 300  # osvježi podatke svakih 5 min

    # Cache (in-memory TTL, nice-to-have)
    cache_ttl_seconds: int = 30

    # Redis (opcionalno) - ako je postavljen, cache koristi Redis umjesto
    # in-memory rječnika (bitno za skaliranje na više instanci aplikacije,
    # gdje in-memory cache po procesu ne bi bio dijeljen). Ako nije
    # postavljen, aplikacija automatski koristi in-memory fallback -
    # cijela funkcionalnost radi identično, samo bez perzistencije cachea
    # kroz restart / dijeljenja između instanci.
    redis_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Settings se cachiraju jer se .env čita samo jednom po pokretanju procesa."""
    return Settings()
