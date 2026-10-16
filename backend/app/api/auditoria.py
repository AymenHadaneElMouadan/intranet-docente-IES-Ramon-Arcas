"""Consulta de auditoría (admin y directiva)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.auditoria import RegistroAuditoriaPaginated
from app.models.usuario import UsuarioPublic
from app.services import auditoria_service

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("", response_model=RegistroAuditoriaPaginated)
async def list_auditoria(
    _actor: Annotated[UsuarioPublic, Depends(require_roles("admin", "directiva"))],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    usuario_id: str | None = None,
    accion: str | None = None,
    recurso_tipo: str | None = None,
    recurso_id: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> RegistroAuditoriaPaginated:
    """Listado paginado de acciones relevantes."""
    return await auditoria_service.list_entries(
        get_db(),
        page=page,
        limit=limit,
        usuario_id=usuario_id,
        accion=accion,
        recurso_tipo=recurso_tipo,
        recurso_id=recurso_id,
        desde=desde,
        hasta=hasta,
    )
