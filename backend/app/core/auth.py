from __future__ import annotations

from functools import lru_cache
from typing import Optional

import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.core.config import Settings, get_settings
from app.core.errors import ApiError


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    # Caches keys in-process; Supabase rotates rarely and the client refetches on miss.
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode(token: str, settings: Settings) -> dict:
    signing_key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
    )


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify a Supabase access token and return the user's UUID.

    Every user-scoped query in this app filters on the value returned here, so a
    failure must raise rather than fall back to any default identity.
    """
    if not settings.supabase_url:
        raise ApiError(500, "AUTH_NOT_CONFIGURED", "Supabase не настроен на сервере.")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(401, "NOT_AUTHENTICATED", "Требуется вход в систему.")

    token = authorization[7:].strip()
    try:
        claims = _decode(token, settings)
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "TOKEN_EXPIRED", "Сессия истекла. Войдите снова.") from exc
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        raise ApiError(401, "INVALID_TOKEN", "Недействительный токен доступа.") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise ApiError(401, "INVALID_TOKEN", "В токене отсутствует идентификатор пользователя.")
    return user_id


def get_current_user_email(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        return _decode(authorization[7:].strip(), settings).get("email")
    except jwt.InvalidTokenError:
        return None
