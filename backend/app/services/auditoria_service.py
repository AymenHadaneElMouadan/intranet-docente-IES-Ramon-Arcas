"""Registro y consulta de auditoría."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.auditoria import RegistroAuditoria, RegistroAuditoriaPaginated
from app.models.usuario import utcnow

COLLECTION = "auditoria"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index([("fecha", -1)])
    await db[COLLECTION].create_index("usuario_id")
    await db[COLLECTION].create_index("accion")


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
    """Persiste una acción relevante (best-effort: no tumba el flujo principal)."""
    try:
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
    except Exception:
        pass


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
    limit: int = 20,
    usuario_id: str | None = None,
    accion: str | None = None,
    recurso_tipo: str | None = None,
    recurso_id: str | None = None,
) -> RegistroAuditoriaPaginated:
    query: dict[str, Any] = {}
    if usuario_id:
        query["usuario_id"] = usuario_id
    if accion:
        query["accion"] = accion
    if recurso_tipo:
        query["recurso_tipo"] = recurso_tipo
    if recurso_id:
        query["recurso_id"] = recurso_id

    skip = (page - 1) * limit
    total = await db[COLLECTION].count_documents(query)
    cursor = db[COLLECTION].find(query).sort("fecha", -1).skip(skip).limit(limit)
    items = [_to_entry(doc) async for doc in cursor]
    return RegistroAuditoriaPaginated(items=items, page=page, limit=limit, total=total)
