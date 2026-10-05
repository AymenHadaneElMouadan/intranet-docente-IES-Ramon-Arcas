"""JWT de acceso y cookies de refresh."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from fastapi import Response

from app.core.config import settings


def create_access_token(*, user_id: str, roles: list[str]) -> tuple[str, int]:
    """
    Emite un access JWT de corta duración.
    Devuelve (token, expires_in_seconds).
    """
    expires_in = settings.access_token_minutes * 60
    payload: dict[str, Any] = {
        "sub": user_id,
        "roles": roles,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
        "iat": datetime.now(UTC),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un access JWT. Lanza jwt.PyJWTError si es inválido."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token incorrecto")
    return payload


def new_refresh_token_value() -> str:
    """Valor opaco del refresh (no es un JWT); se guarda en Redis."""
    return str(uuid4())


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Adjunta la cookie HttpOnly del refresh al Response."""
    max_age = settings.refresh_token_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        path=settings.cookie_path,
        max_age=max_age,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Borra la cookie de refresh en el cliente."""
    response.delete_cookie(
        key=settings.cookie_name,
        path=settings.cookie_path,
    )
