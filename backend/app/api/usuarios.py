"""Endpoints de usuarios del claustro."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.core.database import get_db
from app.core.deps import CurrentActiveUser, require_roles
from app.models.usuario import (
    Horario,
    PaginatedUsuarios,
    Role,
    UsuarioCreate,
    UsuarioDatosPersonales,
    UsuarioEstado,
    UsuarioMePatch,
    UsuarioPatch,
    UsuarioPublic,
    UsuarioRolesPut,
)
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=PaginatedUsuarios)
async def list_usuarios(
    _admin: Annotated[UsuarioPublic, Depends(require_roles("admin"))],
    departamento: str | None = None,
    estado: UsuarioEstado | None = None,
    rol: Role | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PaginatedUsuarios:
    """Listado paginado; solo admin activo."""
    return await usuario_service.list_usuarios(
        get_db(),
        departamento=departamento,
        estado=estado,
        rol=rol,
        page=page,
        limit=limit,
    )


@router.post("", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    response: Response,
    _admin: Annotated[UsuarioPublic, Depends(require_roles("admin"))],
) -> UsuarioPublic:
    """Alta manual; el id lo asigna Mongo. Location apunta al GET por id."""
    user = await usuario_service.create_manual(get_db(), payload)
    response.headers["Location"] = f"/api/v1/usuarios/{user.id}"
    return user


@router.get("/me", response_model=UsuarioPublic)
async def get_me(current: CurrentActiveUser) -> UsuarioPublic:
    """Perfil del usuario autenticado (cuenta activa)."""
    return current


@router.patch("/me", response_model=UsuarioPublic)
async def patch_me(payload: UsuarioMePatch, current: CurrentActiveUser) -> UsuarioPublic:
    """Rectificar datos propios (RGPD)."""
    return await usuario_service.patch_me(get_db(), current.id, payload)


@router.get("/me/datos", response_model=UsuarioDatosPersonales)
async def get_me_datos(current: CurrentActiveUser) -> UsuarioDatosPersonales:
    """Exportar datos personales propios (RGPD)."""
    return await usuario_service.export_me_datos(get_db(), current)


@router.get("/me/horario", response_model=Horario)
async def get_me_horario(current: CurrentActiveUser) -> Horario:
    """Horario semanal propio (arranque PWA); requiere cuenta activa."""
    return await usuario_service.get_horario(get_db(), current.id)


@router.get("/{id}", response_model=UsuarioPublic)
async def get_usuario(
    current: CurrentActiveUser,
    id: Annotated[str, Path(description="Identificador del usuario")],
) -> UsuarioPublic:
    """Detalle: admin o el propio usuario."""
    if "admin" not in current.roles and current.id != id:
        raise HTTPException(status_code=403, detail="Se requiere uno de estos roles: admin")
    user = await usuario_service.get_by_id(get_db(), id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get("/{id}/horario", response_model=Horario)
async def get_usuario_horario(
    current: CurrentActiveUser,
    id: Annotated[str, Path()],
) -> Horario:
    """Horario de un docente: admin o self."""
    if "admin" not in current.roles and current.id != id:
        raise HTTPException(status_code=403, detail="Se requiere uno de estos roles: admin")
    return await usuario_service.get_horario(get_db(), id)


@router.patch("/{id}", response_model=UsuarioPublic)
async def patch_usuario(
    payload: UsuarioPatch,
    id: Annotated[str, Path()],
    _admin: Annotated[UsuarioPublic, Depends(require_roles("admin"))],
) -> UsuarioPublic:
    """Actualización parcial (aprobar alta, roles, departamento…)."""
    return await usuario_service.patch_usuario(get_db(), id, payload)


@router.put("/{id}/roles", response_model=UsuarioPublic)
async def put_usuario_roles(
    payload: UsuarioRolesPut,
    id: Annotated[str, Path()],
    _admin: Annotated[UsuarioPublic, Depends(require_roles("admin"))],
) -> UsuarioPublic:
    """Sustituye la lista completa de roles."""
    return await usuario_service.put_roles(get_db(), id, payload)
