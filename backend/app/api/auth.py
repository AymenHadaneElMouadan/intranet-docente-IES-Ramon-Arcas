"""Endpoints de autenticación OAuth Google + JWT."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response

from app.core.database import get_db, get_redis
from app.core.deps import CurrentUser
from app.models.usuario import AccessTokenResponse, GoogleAuthRequest, UsuarioMe
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/google", response_model=AccessTokenResponse)
async def auth_google(payload: GoogleAuthRequest, response: Response) -> AccessTokenResponse:
    """Login con id_token de Google; setea cookie refresh HttpOnly."""
    return await auth_service.login_with_google(
        get_db(), get_redis(), response, payload.id_token
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def auth_refresh(
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> AccessTokenResponse:
    """Renueva el access JWT leyendo la cookie (sin Bearer)."""
    return await auth_service.refresh_access(get_db(), get_redis(), response, refresh_token)


@router.post("/logout")
async def auth_logout(
    response: Response,
    _current: CurrentUser,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> dict[str, str]:
    """Invalida el refresh en Redis y borra la cookie."""
    return await auth_service.logout(get_redis(), response, refresh_token)


@router.get("/me", response_model=UsuarioMe)
async def auth_me(current: CurrentUser) -> UsuarioMe:
    """Identidad y roles para el arranque de la PWA."""
    return UsuarioMe(**current.model_dump(), permisos=[])
