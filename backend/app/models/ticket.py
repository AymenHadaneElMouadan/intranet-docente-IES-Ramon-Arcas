"""Esquemas de tickets y comentarios."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TicketTipo(str, Enum):
    rmi = "rmi"
    rrss = "rrss"
    compras = "compras"
    otro = "otro"


class TicketEstado(str, Enum):
    abierto = "abierto"
    en_proceso = "en_proceso"
    resuelto = "resuelto"
    cerrado = "cerrado"


# Transiciones válidas: abierto → en_proceso → resuelto → cerrado
TRANSICIONES_VALIDAS: dict[TicketEstado, set[TicketEstado]] = {
    TicketEstado.abierto: {TicketEstado.en_proceso},
    TicketEstado.en_proceso: {TicketEstado.resuelto},
    TicketEstado.resuelto: {TicketEstado.cerrado},
    TicketEstado.cerrado: set(),
}


class Ticket(BaseModel):
    id: str
    tipo: TicketTipo
    estado: TicketEstado
    titulo: str
    descripcion: str | None = None
    solicitante_id: str
    asignado_id: str | None = None
    creado_en: datetime | None = None


class TicketCreate(BaseModel):
    tipo: TicketTipo
    titulo: str = Field(min_length=1)
    descripcion: str | None = None


class TicketPatch(BaseModel):
    estado: TicketEstado | None = None
    asignado_id: str | None = None


class Comentario(BaseModel):
    id: str
    autor_id: str
    cuerpo: str
    creado_en: datetime
    ticket_id: str | None = None


class ComentarioCreate(BaseModel):
    cuerpo: str = Field(min_length=1)


def doc_to_ticket(doc: dict[str, Any]) -> Ticket:
    return Ticket(
        id=str(doc["_id"]),
        tipo=TicketTipo(doc["tipo"]),
        estado=TicketEstado(doc["estado"]),
        titulo=doc["titulo"],
        descripcion=doc.get("descripcion"),
        solicitante_id=doc["solicitante_id"],
        asignado_id=doc.get("asignado_id"),
        creado_en=doc.get("creado_en"),
    )


def doc_to_comentario(doc: dict[str, Any]) -> Comentario:
    return Comentario(
        id=str(doc["_id"]),
        autor_id=doc["autor_id"],
        cuerpo=doc["cuerpo"],
        creado_en=doc["creado_en"],
        ticket_id=doc.get("ticket_id"),
    )
