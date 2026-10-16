"""Registro y consulta de auditoría."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.auditoria import RegistroAuditoria, RegistroAuditoriaPaginated
from app.models.usuario import utcnow

logger = logging.getLogger(__name__)

COLLECTION = "auditoria"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index([("fecha", -1)])
    await db[COLLECTION].create_index("usuario_id")
    await db[COLLECTION].create_index("accion")


async def _insert(
    db: AsyncIOMotorDatabase,
    *,
    accion: str,
    usuario_id: str,
    recurso_tipo: str,
    recurso_id: str | None = None,
    usuario_nombre: str | None = None,
    detalle: dict[str, Any] | None = None,
) -> None:
    await db[COLLECTION].insert_one(
        {
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "accion": accion,
            "recurso_tipo": recurso_tipo,
            "recurso_id": recurso_id,
            "detalle": detalle,
            "fecha": utcnow(),
        }
    )


async def record(
    db: AsyncIOMotorDatabase,
    *,
    accion: str,
    usuario_id: str,
    recurso_tipo: str,
    recurso_id: str | None = None,
    usuario_nombre: str | None = None,
    detalle: dict[str, Any] | None = None,
) -> None:
    """Best-effort: no tumba el flujo principal (login, fallos de auth)."""
    try:
        await _insert(
            db,
            accion=accion,
            usuario_id=usuario_id,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            usuario_nombre=usuario_nombre,
            detalle=detalle,
        )
    except Exception:
        logger.warning(
            "No se pudo persistir auditoría best-effort accion=%s usuario_id=%s",
            accion,
            usuario_id,
            exc_info=True,
        )


async def record_required(
    db: AsyncIOMotorDatabase,
    *,
    accion: str,
    usuario_id: str,
    recurso_tipo: str,
    recurso_id: str | None = None,
    usuario_nombre: str | None = None,
    detalle: dict[str, Any] | None = None,
) -> None:
    """Persistencia obligatoria para mutaciones críticas (usuarios/roles)."""
    try:
        await _insert(
            db,
            accion=accion,
            usuario_id=usuario_id,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            usuario_nombre=usuario_nombre,
            detalle=detalle,
        )
    except Exception as exc:
        logger.exception(
            "Fallo al persistir auditoría requerida accion=%s usuario_id=%s",
            accion,
            usuario_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo registrar la auditoría de la operación",
        ) from exc


def _to_entry(doc: dict[str, Any]) -> RegistroAuditoria:
    return RegistroAuditoria(
        id=str(doc["_id"]),
        usuario_id=str(doc.get("usuario_id") or ""),
        usuario_nombre=doc.get("usuario_nombre"),
        accion=doc["accion"],
        recurso_tipo=doc.get("recurso_tipo") or doc.get("recurso") or "desconocido",
        recurso_id=doc.get("recurso_id"),
        fecha=doc.get("fecha") or doc.get("created_at") or utcnow(),
        detalle=doc.get("detalle"),
    )


async def list_entries(
    db: AsyncIOMotorDatabase,
    *,
    page: int = 1,
    limit: int = 10,
    usuario_id: str | None = None,
    accion: str | None = None,
    recurso_tipo: str | None = None,
    recurso_id: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> RegistroAuditoriaPaginated:
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El intervalo de fechas es inválido: desde debe ser anterior o igual a hasta",
        )

    query: dict[str, Any] = {}
    if usuario_id:
        query["usuario_id"] = usuario_id
    if accion:
        query["accion"] = accion
    if recurso_tipo:
        query["recurso_tipo"] = recurso_tipo
    if recurso_id:
        query["recurso_id"] = recurso_id
    if desde is not None or hasta is not None:
        fecha_q: dict[str, Any] = {}
        if desde is not None:
            fecha_q["$gte"] = desde
        if hasta is not None:
            fecha_q["$lte"] = hasta
        query["fecha"] = fecha_q

    skip = (page - 1) * limit
    total = await db[COLLECTION].count_documents(query)
    cursor = db[COLLECTION].find(query).sort("fecha", -1).skip(skip).limit(limit)
    items = [_to_entry(doc) async for doc in cursor]
    return RegistroAuditoriaPaginated(items=items, page=page, limit=limit, total=total)
