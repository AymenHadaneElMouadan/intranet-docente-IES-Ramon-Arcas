"""Endpoints de anuncios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.database import get_db
from app.core.deps import CurrentActiveUser, require_roles
from app.models.anuncio import Anuncio, AnuncioCreate, AnuncioFijar
from app.models.usuario import UsuarioPublic
from app.services import anuncio_service

router = APIRouter(prefix="/anuncios", tags=["Anuncios"])


@router.get("", response_model=list[Anuncio])
async def list_anuncios(
    current: CurrentActiveUser,
    departamento: str | None = None,
) -> list[Anuncio]:
    """Feed segmentado por departamento del usuario autenticado."""
    return await anuncio_service.list_anuncios(
        get_db(),
        departamento=departamento,
        viewer_departamento=current.departamento,
    )


@router.post("", response_model=Anuncio, status_code=status.HTTP_201_CREATED)
async def create_anuncio(
    payload: AnuncioCreate,
    response: Response,
    current: Annotated[UsuarioPublic, Depends(require_roles("admin", "directiva"))],
) -> Anuncio:
    """Publicar anuncio; admin o directiva."""
    anuncio = await anuncio_service.create_anuncio(
        get_db(), payload, autor_id=current.id
    )
    response.headers["Location"] = f"/api/v1/anuncios/{anuncio.id}"
    return anuncio


@router.patch("/{id}/fijar", response_model=Anuncio)
async def fijar_anuncio(
    id: str,
    payload: AnuncioFijar,
    _admin: Annotated[UsuarioPublic, Depends(require_roles("admin"))],
) -> Anuncio:
    """Fijar o desfijar anuncio (solo admin)."""
    return await anuncio_service.fijar_anuncio(get_db(), id, payload.fijado)
