"""
JWT autentifikacija.

Tok: korisnik se prijavljuje preko POST /auth/login sa DummyJSON
kredencijalima (npr. username="emilys", password="emilyspass" - to su
DummyJSON-ovi demo useri, vidi https://dummyjson.com/docs/auth).
TicketHub proslijedi te kredencijale DummyJSON-u radi provjere, a zatim
sam izda VLASTITI JWT (potpisan našim JWT_SECRET_KEY) koji se koristi za
autorizaciju write operacija unutar TicketHub-a.

Zašto ne koristimo direktno DummyJSON-ov token? Jer TicketHub treba
kontrolirati vlastiti expiry, secret i payload (npr. buduće role/scope-ove),
neovisno o vanjskom izvoru. DummyJSON ovdje služi samo kao "identity
provider" za provjeru je li lozinka točna.
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from tickethub.core.config import get_settings

settings = get_settings()
_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(username: str, expires_minutes: int = 60) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Vraća username (sub) iz tokena, ili baca JWTError ako je nevažeći/istekao."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    username = payload.get("sub")
    if username is None:
        raise JWTError("Token ne sadrži 'sub' claim")
    return username


async def get_current_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency za zaštitu ruta. Koristi se kao:
        current_user: str = Depends(get_current_username)

    Vraća 401 ako Authorization header nedostaje ili je token nevažeći.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nedostaje Authorization header (Bearer token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nevažeći ili istekao token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
