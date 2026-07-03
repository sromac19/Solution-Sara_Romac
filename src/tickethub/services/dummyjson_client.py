"""
Tanki async HTTP klijent prema DummyJSON-u.

Namjerno odvojen od sync/transformacijske logike (services/sync.py) -
ovaj modul samo dohvaća sirove podatke, ne zna ništa o našem Ticket modelu.
To olakšava testiranje (mockamo httpx, ne moramo mockati bazu) i mijenjanje
izvora u budućnosti.
"""

from typing import Any

import httpx
from tickethub.core.config import get_settings
from tickethub.core.logging import get_logger

logger = get_logger(__name__)


class DummyJSONClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        settings = get_settings()
        self._base_url = base_url or settings.dummyjson_base_url
        self._timeout = timeout

    async def fetch_todos(self, limit: int = 150) -> list[dict[str, Any]]:
        """Dohvaća sve todo-e (koji se transformiraju u tickete)."""
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get("/todos", params={"limit": limit})
            response.raise_for_status()
            data = response.json()
            return data.get("todos", [])

    async def fetch_users(self, limit: int = 200) -> dict[int, str]:
        """
        Dohvaća korisnike i vraća mapu {userId: username} kako bismo
        mogli razriješiti `assignee` polje bez N+1 poziva po tiketu.
        """
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get("/users", params={"limit": limit})
            response.raise_for_status()
            data = response.json()
            users = data.get("users", [])
            return {user["id"]: user["username"] for user in users}
