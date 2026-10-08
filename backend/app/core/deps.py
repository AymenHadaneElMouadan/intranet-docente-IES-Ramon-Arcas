"""Dependencias FastAPI: usuario actual y control de roles."""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import UsuarioEstado, UsuarioPublic
from app.services import usuario_service

# Extrae el Bearer del header Authorization; no falla solo si falta (auto_error=False).
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UsuarioPublic:
    """
    Identidad de sesión: JWT Bearer válido + usuario aún en Mongo.
    Admite estado pendiente (p.ej. GET /auth/me); el negocio usa get_current_active_user.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    try:
        payload = decode_access_token(credentials.credentials)
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado") from None

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    # Roles del JWT no se confían: la fuente de verdad es Mongo.
    user = await usuario_service.get_by_id(get_db(), user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user


async def get_current_active_user(
    current_user: Annotated[UsuarioPublic, Depends(get_current_user)],
) -> UsuarioPublic:
    """Cuenta activa: alta OAuth pendiente no puede usar endpoints de negocio."""
    if current_user.estado != UsuarioEstado.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere una cuenta activa",
        )
    return current_user


def require_roles(*roles: str) -> Callable:
    """
    Factory: cuenta activa + al menos uno de los roles pedidos.
    Uso: Depends(require_roles("admin", "jefatura"))
    """

    async def _checker(
        current_user: Annotated[UsuarioPublic, Depends(get_current_active_user)],
    ) -> UsuarioPublic:
        if not set(roles).intersection(current_user.roles):
            needed = ", ".join(roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de estos roles: {needed}",
            )
        return current_user

    return _checker


CurrentUser = Annotated[UsuarioPublic, Depends(get_current_user)]
CurrentActiveUser = Annotated[UsuarioPublic, Depends(get_current_active_user)]
