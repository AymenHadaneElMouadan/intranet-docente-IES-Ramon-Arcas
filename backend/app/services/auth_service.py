"""Autenticación Google + emisión de tokens."""

from typing import Any

from fastapi import HTTPException, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import (
    clear_refresh_cookie,
    create_access_token,
    new_refresh_token_value,
    set_refresh_cookie,
)
from app.models.usuario import AccessTokenResponse, UsuarioEstado, UsuarioPublic, doc_to_usuario
from app.services import usuario_service

REFRESH_PREFIX = "refresh:"


async def store_refresh(redis: Redis, token: str, user_id: str) -> None:
    """Guarda el refresh opaco en Redis con TTL."""
    ttl = settings.refresh_token_days * 24 * 60 * 60
    await redis.set(f"{REFRESH_PREFIX}{token}", user_id, ex=ttl)


async def revoke_refresh(redis: Redis, token: str | None) -> None:
    """Invalida un refresh concreto (logout)."""
    if token:
        await redis.delete(f"{REFRESH_PREFIX}{token}")


async def resolve_refresh_user_id(redis: Redis, token: str | None) -> str | None:
    if not token:
        return None
    return await redis.get(f"{REFRESH_PREFIX}{token}")


def verify_google_id_token(token: str) -> dict[str, Any]:
    """
    Verifica el id_token con Google.
    En tests se puede parchear esta función.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GOOGLE_CLIENT_ID no configurado",
        )
    try:
        return google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="id_token inválido") from exc


async def login_with_google(
    db: AsyncIOMotorDatabase,
    redis: Redis,
    response: Response,
    id_token_value: str,
) -> AccessTokenResponse:
    """Valida Google, crea/recupera usuario y emite access + cookie refresh."""
    claims = verify_google_id_token(id_token_value)
    email = claims.get("email")
    google_sub = claims.get("sub")
    name = claims.get("name") or (email.split("@")[0] if email else "Usuario")
    if not email or not google_sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de Google incompleto")
    # Evita vincular cuentas con email no verificado en Google.
    if claims.get("email_verified") is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El email de Google no está verificado",
        )

    doc = await usuario_service.get_by_google_sub(db, google_sub)
    if doc is None:
        doc = await usuario_service.get_by_email(db, email)
        if doc is None:
            user = await usuario_service.create_from_google(
                db, email=email, name=name, google_sub=google_sub
            )
        else:
            # Vincula google_sub a un usuario existente por email.
            await db[usuario_service.COLLECTION].update_one(
                {"_id": doc["_id"]},
                {"$set": {"google_sub": google_sub}},
            )
            doc["google_sub"] = google_sub
            user = doc_to_usuario(doc)
    else:
        user = doc_to_usuario(doc)

    return await issue_tokens(redis, response, user)


async def issue_tokens(redis: Redis, response: Response, user: UsuarioPublic) -> AccessTokenResponse:
    """Emite access JWT y cookie refresh para un usuario ya conocido."""
    access, expires_in = create_access_token(user_id=user.id, roles=user.roles)
    refresh = new_refresh_token_value()
    await store_refresh(redis, refresh, user.id)
    set_refresh_cookie(response, refresh)
    return AccessTokenResponse(access_token=access, expires_in=expires_in)


async def refresh_access(
    db: AsyncIOMotorDatabase,
    redis: Redis,
    response: Response,
    refresh_token: str | None,
) -> AccessTokenResponse:
    """Renueva el access a partir de la cookie refresh."""
    user_id = await resolve_refresh_user_id(redis, refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    user = await usuario_service.get_by_id(db, user_id)
    if user is None:
        await revoke_refresh(redis, refresh_token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    # Cuentas inactivas no pueden renovar sesión.
    if user.estado == UsuarioEstado.inactivo:
        await revoke_refresh(redis, refresh_token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    # Rotación sencilla: invalida el refresh anterior y emite uno nuevo.
    # pendiente y activo sí pueden refrescar (pendiente necesita /auth/me).
    await revoke_refresh(redis, refresh_token)
    return await issue_tokens(redis, response, user)


async def logout(redis: Redis, response: Response, refresh_token: str | None) -> dict[str, str]:
    await revoke_refresh(redis, refresh_token)
    clear_refresh_cookie(response)
    return {"detail": "Sesión cerrada"}
