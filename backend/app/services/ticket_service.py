"""Servicio de tickets y comentarios."""

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.models.ticket import (
    TRANSICIONES_VALIDAS,
    Comentario,
    ComentarioCreate,
    Ticket,
    TicketCreate,
    TicketEstado,
    TicketPatch,
    TicketTipo,
    doc_to_comentario,
    doc_to_ticket,
)

COLLECTION = "tickets"
COMENTARIOS = "ticket_comentarios"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index([("estado", 1), ("tipo", 1)])
    await db[COLLECTION].create_index("solicitante_id")
    await db[COMENTARIOS].create_index("ticket_id")


def _oid(resource_id: str, detail: str = "Ticket no encontrado") -> ObjectId:
    if not ObjectId.is_valid(resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return ObjectId(resource_id)


async def get_ticket(db: AsyncIOMotorDatabase, ticket_id: str) -> Ticket:
    doc = await db[COLLECTION].find_one({"_id": _oid(ticket_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    return doc_to_ticket(doc)


async def list_tickets(
    db: AsyncIOMotorDatabase,
    *,
    tipo: TicketTipo | None,
    estado: TicketEstado | None,
) -> list[Ticket]:
    query: dict[str, Any] = {}
    if tipo is not None:
        query["tipo"] = tipo.value
    if estado is not None:
        query["estado"] = estado.value
    cursor = db[COLLECTION].find(query).sort("creado_en", -1)
    return [doc_to_ticket(doc) async for doc in cursor]


async def create_ticket(
    db: AsyncIOMotorDatabase,
    payload: TicketCreate,
    *,
    solicitante_id: str,
) -> Ticket:
    doc = {
        "tipo": payload.tipo.value,
        "titulo": payload.titulo,
        "descripcion": payload.descripcion,
        "estado": TicketEstado.abierto.value,
        "solicitante_id": solicitante_id,
        "asignado_id": None,
        "creado_en": datetime.now(UTC),
    }
    result = await db[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_ticket(doc)


async def patch_ticket(
    db: AsyncIOMotorDatabase,
    ticket_id: str,
    payload: TicketPatch,
) -> Ticket:
    current = await get_ticket(db, ticket_id)
    updates: dict[str, Any] = {}

    if payload.estado is not None:
        permitidos = TRANSICIONES_VALIDAS[current.estado]
        if payload.estado not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Transicion invalida: {current.estado.value} -> {payload.estado.value}"
                ),
            )
        updates["estado"] = payload.estado.value

    if payload.asignado_id is not None:
        updates["asignado_id"] = payload.asignado_id

    if not updates:
        return current

    updates["updated_at"] = datetime.now(UTC)
    result = await db[COLLECTION].find_one_and_update(
        {"_id": _oid(ticket_id)},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    return doc_to_ticket(result)


async def list_comentarios(db: AsyncIOMotorDatabase, ticket_id: str) -> list[Comentario]:
    await get_ticket(db, ticket_id)
    cursor = db[COMENTARIOS].find({"ticket_id": ticket_id}).sort("creado_en", 1)
    return [doc_to_comentario(doc) async for doc in cursor]


async def create_comentario(
    db: AsyncIOMotorDatabase,
    ticket_id: str,
    payload: ComentarioCreate,
    *,
    autor_id: str,
) -> Comentario:
    await get_ticket(db, ticket_id)
    doc = {
        "ticket_id": ticket_id,
        "autor_id": autor_id,
        "cuerpo": payload.cuerpo,
        "creado_en": datetime.now(UTC),
    }
    result = await db[COMENTARIOS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_comentario(doc)


def puede_gestionar_ticket(user_roles: list[str], ticket: Ticket, user_id: str) -> bool:
    """admin o responsable_ticket asignado (o sin asignar aún para responsable)."""
    if "admin" in user_roles:
        return True
    if "responsable_ticket" in user_roles:
        return ticket.asignado_id is None or ticket.asignado_id == user_id
    return False


def puede_comentar(user_roles: list[str], ticket: Ticket, user_id: str) -> bool:
    if "admin" in user_roles or "responsable_ticket" in user_roles:
        return True
    return ticket.solicitante_id == user_id or ticket.asignado_id == user_id
