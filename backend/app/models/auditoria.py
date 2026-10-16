"""Esquemas de auditoría (acciones relevantes)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RegistroAuditoria(BaseModel):
    """Alineado al contrato OpenAPI `RegistroAuditoria`."""

    id: str
    usuario_id: str
    usuario_nombre: str | None = None
    accion: str
    recurso_tipo: str
    recurso_id: str | None = None
    fecha: datetime
    detalle: dict[str, Any] | None = None


class RegistroAuditoriaPaginated(BaseModel):
    items: list[RegistroAuditoria]
    page: int
    limit: int
    total: int
