"""Endpoints de tickets y comentarios."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.database import get_db
from app.core.deps import CurrentActiveUser, require_roles
from app.models.ticket import (
    Comentario,
    ComentarioCreate,
    Ticket,
    TicketCreate,
    TicketEstado,
    TicketPatch,
    TicketTipo,
)
from app.models.usuario import UsuarioPublic
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("", response_model=list[Ticket])
async def list_tickets(
    _current: CurrentActiveUser,
    tipo: TicketTipo | None = None,
    estado: TicketEstado | None = None,
) -> list[Ticket]:
    return await ticket_service.list_tickets(get_db(), tipo=tipo, estado=estado)


@router.post("", response_model=Ticket, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    response: Response,
    current: CurrentActiveUser,
) -> Ticket:
    ticket = await ticket_service.create_ticket(
        get_db(), payload, solicitante_id=current.id
    )
    response.headers["Location"] = f"/api/v1/tickets/{ticket.id}"
    return ticket


@router.patch("/{id}", response_model=Ticket)
async def patch_ticket(
    id: str,
    payload: TicketPatch,
    current: Annotated[
        UsuarioPublic, Depends(require_roles("admin", "responsable_ticket"))
    ],
) -> Ticket:
    ticket = await ticket_service.get_ticket(get_db(), id)
    if not ticket_service.puede_gestionar_ticket(current.roles, ticket, current.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permiso para gestionar este ticket",
        )
    return await ticket_service.patch_ticket(get_db(), id, payload)


@router.get("/{id}/comentarios", response_model=list[Comentario])
async def list_comentarios(id: str, current: CurrentActiveUser) -> list[Comentario]:
    ticket = await ticket_service.get_ticket(get_db(), id)
    if not ticket_service.puede_comentar(current.roles, ticket, current.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permiso para ver comentarios de este ticket",
        )
    return await ticket_service.list_comentarios(get_db(), id)


@router.post(
    "/{id}/comentarios",
    response_model=Comentario,
    status_code=status.HTTP_201_CREATED,
)
async def create_comentario(
    id: str,
    payload: ComentarioCreate,
    response: Response,
    current: CurrentActiveUser,
) -> Comentario:
    ticket = await ticket_service.get_ticket(get_db(), id)
    if not ticket_service.puede_comentar(current.roles, ticket, current.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin permiso para comentar este ticket",
        )
    comentario = await ticket_service.create_comentario(
        get_db(), id, payload, autor_id=current.id
    )
    response.headers["Location"] = f"/api/v1/tickets/{id}/comentarios/{comentario.id}"
    return comentario
