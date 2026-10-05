"""Servicio de usuarios (persistencia Mongo + reglas simples)."""

from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.models.usuario import (
    DEFAULT_HORARIO_DIAS,
    Horario,
    PaginatedUsuarios,
    UsuarioCreate,
    UsuarioEstado,
    UsuarioPatch,
    UsuarioPublic,
    doc_to_usuario,
    utcnow,
)

COLLECTION = "usuarios"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Índice único de email para evitar altas duplicadas."""
    await db[COLLECTION].create_index("email", unique=True)


def _oid(user_id: str) -> ObjectId:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return ObjectId(user_id)


async def get_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UsuarioPublic | None:
    doc = await db[COLLECTION].find_one({"_id": _oid(user_id)})
    return doc_to_usuario(doc) if doc else None


async def get_by_email(db: AsyncIOMotorDatabase, email: str) -> dict[str, Any] | None:
    return await db[COLLECTION].find_one({"email": email.lower()})


async def get_by_google_sub(db: AsyncIOMotorDatabase, google_sub: str) -> dict[str, Any] | None:
    return await db[COLLECTION].find_one({"google_sub": google_sub})


async def create_from_google(
    db: AsyncIOMotorDatabase,
    *,
    email: str,
    name: str,
    google_sub: str,
) -> UsuarioPublic:
    """Alta vía OAuth: estado pendiente hasta que un admin apruebe."""
    doc = {
        "email": email.lower(),
        "name": name,
        "departamento": "",
        "roles": ["docente"],
        "estado": UsuarioEstado.pendiente.value,
        "google_sub": google_sub,
        "horario": DEFAULT_HORARIO_DIAS,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = await db[COLLECTION].insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El recurso ya existe") from exc
    doc["_id"] = result.inserted_id
    return doc_to_usuario(doc)


async def create_manual(db: AsyncIOMotorDatabase, payload: UsuarioCreate) -> UsuarioPublic:
    """Alta manual por administración (sin OAuth)."""
    role_values = [r.value for r in payload.roles] if payload.roles else ["docente"]
    doc = {
        "email": str(payload.email).lower(),
        "name": payload.name,
        "departamento": payload.departamento,
        "roles": role_values,
        "estado": payload.estado.value,
        "google_sub": None,
        "horario": DEFAULT_HORARIO_DIAS,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = await db[COLLECTION].insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El recurso ya existe") from exc
    doc["_id"] = result.inserted_id
    return doc_to_usuario(doc)


async def list_usuarios(
    db: AsyncIOMotorDatabase,
    *,
    departamento: str | None,
    page: int,
    limit: int,
) -> PaginatedUsuarios:
    query: dict[str, Any] = {}
    if departamento:
        query["departamento"] = departamento

    total = await db[COLLECTION].count_documents(query)
    skip = (page - 1) * limit
    cursor = db[COLLECTION].find(query).skip(skip).limit(limit).sort("name", 1)
    items = [doc_to_usuario(doc) async for doc in cursor]
    return PaginatedUsuarios(items=items, page=page, limit=limit, total=total)


async def patch_usuario(db: AsyncIOMotorDatabase, user_id: str, payload: UsuarioPatch) -> UsuarioPublic:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "estado" in updates and updates["estado"] is not None:
        updates["estado"] = updates["estado"].value if hasattr(updates["estado"], "value") else updates["estado"]
    if "roles" in updates and updates["roles"] is not None:
        updates["roles"] = [
            r.value if hasattr(r, "value") else r for r in updates["roles"]
        ]
    if not updates:
        user = await get_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    updates["updated_at"] = utcnow()
    result = await db[COLLECTION].find_one_and_update(
        {"_id": _oid(user_id)},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return doc_to_usuario(result)


async def get_horario(db: AsyncIOMotorDatabase, user_id: str) -> Horario:
    doc = await db[COLLECTION].find_one({"_id": _oid(user_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    dias = doc.get("horario") or DEFAULT_HORARIO_DIAS
    return Horario(usuario_id=str(doc["_id"]), dias=dias)
