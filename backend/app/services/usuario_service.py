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
    OrigenAlta,
    PaginatedUsuarios,
    Role,
    UsuarioCreate,
    UsuarioDatosPersonales,
    UsuarioEstado,
    UsuarioMePatch,
    UsuarioPatch,
    UsuarioPublic,
    UsuarioRolesPut,
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
    """
    Busca por id. Devuelve None si el id es inválido o no existe
    (así auth puede mapear JWT.sub malo a 401, no a 404).
    """
    if not ObjectId.is_valid(user_id):
        return None
    doc = await db[COLLECTION].find_one({"_id": ObjectId(user_id)})
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
        "origen_alta": OrigenAlta.oauth.value,
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
        "origen_alta": OrigenAlta.manual.value,
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
    estado: UsuarioEstado | None,
    rol: Role | None,
    page: int,
    limit: int,
) -> PaginatedUsuarios:
    query: dict[str, Any] = {}
    if departamento:
        query["departamento"] = departamento
    if estado is not None:
        query["estado"] = estado.value
    if rol is not None:
        query["roles"] = rol.value

    total = await db[COLLECTION].count_documents(query)
    skip = (page - 1) * limit
    cursor = db[COLLECTION].find(query).skip(skip).limit(limit).sort("name", 1)
    items = [doc_to_usuario(doc) async for doc in cursor]
    return PaginatedUsuarios(items=items, page=page, limit=limit, total=total)


async def _count_admins(db: AsyncIOMotorDatabase, *, exclude_id: str | None = None) -> int:
    query: dict[str, Any] = {"roles": Role.admin.value}
    if exclude_id is not None:
        query["_id"] = {"$ne": _oid(exclude_id)}
    return await db[COLLECTION].count_documents(query)


async def patch_usuario(db: AsyncIOMotorDatabase, user_id: str, payload: UsuarioPatch) -> UsuarioPublic:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "estado" in updates and updates["estado"] is not None:
        updates["estado"] = updates["estado"].value if hasattr(updates["estado"], "value") else updates["estado"]
    if "roles" in updates and updates["roles"] is not None:
        role_values = [r.value if hasattr(r, "value") else r for r in updates["roles"]]
        current = await get_by_id(db, user_id)
        if current is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if Role.admin.value in current.roles and Role.admin.value not in role_values:
            if await _count_admins(db, exclude_id=user_id) == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede eliminar el ultimo admin",
                )
        updates["roles"] = role_values
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


async def patch_me(
    db: AsyncIOMotorDatabase, user_id: str, payload: UsuarioMePatch
) -> UsuarioPublic:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
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


async def export_me_datos(db: AsyncIOMotorDatabase, user: UsuarioPublic) -> UsuarioDatosPersonales:
    tickets = [
        {
            "id": str(doc["_id"]),
            "titulo": doc.get("titulo"),
            "estado": doc.get("estado"),
            "tipo": doc.get("tipo"),
        }
        async for doc in db["tickets"].find({"solicitante_id": user.id})
    ]
    ausencias = [
        {
            "id": str(doc["_id"]),
            "tipo": doc.get("tipo"),
            "fecha_inicio": doc.get("fecha_inicio"),
            "fecha_fin": doc.get("fecha_fin"),
        }
        async for doc in db["ausencias"].find({"usuario_id": user.id})
    ]
    return UsuarioDatosPersonales(
        usuario=user,
        exportado_en=utcnow(),
        ausencias=ausencias,
        tickets=tickets,
        suscripciones_push=[],
    )


async def put_roles(
    db: AsyncIOMotorDatabase, user_id: str, payload: UsuarioRolesPut
) -> UsuarioPublic:
    return await patch_usuario(
        db, user_id, UsuarioPatch(roles=payload.roles)
    )


async def get_horario(db: AsyncIOMotorDatabase, user_id: str) -> Horario:
    doc = await db[COLLECTION].find_one({"_id": _oid(user_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    dias = doc.get("horario") or DEFAULT_HORARIO_DIAS
    return Horario(usuario_id=str(doc["_id"]), dias=dias)
