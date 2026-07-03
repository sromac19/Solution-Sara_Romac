"""
Autentifikacija - POST /auth/login.

Prosljeđuje kredencijale DummyJSON-u (koji ih provjerava protiv svojih
demo korisnika - vidi https://dummyjson.com/docs/auth), a pri uspjehu
izdaje vlastiti TicketHub JWT koji se koristi za write endpointe.

Demo kredencijali za testiranje (javno dokumentirani na dummyjson.com):
    username: emilys
    password: emilyspass
"""

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from tickethub.core.config import get_settings
from tickethub.core.logging import get_logger
from tickethub.core.rate_limit import limiter
from tickethub.core.security import create_access_token
from tickethub.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest) -> TokenResponse:
    settings = get_settings()

    async with httpx.AsyncClient(base_url=settings.dummyjson_base_url, timeout=10.0) as client:
        response = await client.post(
            "/auth/login",
            json={"username": payload.username, "password": payload.password},
        )

    if response.status_code != status.HTTP_200_OK:
        logger.warning("Neuspio login pokušaj za korisnika '%s'", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravno korisničko ime ili lozinka",
        )

    token = create_access_token(username=payload.username)
    return TokenResponse(access_token=token)
