"""Esquemas de anuncios del tablón."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Anuncio(BaseModel):
    id: str
    titulo: str
    cuerpo: str
    departamento: str | None = None
    fijado: bool = False
    expira_en: datetime | None = None
    creado_en: datetime | None = None
    autor_id: str | None = None


class AnuncioCreate(BaseModel):
    titulo: str = Field(min_length=1)
    cuerpo: str = Field(min_length=1)
    departamento: str | None = None
    expira_en: datetime | None = None


class AnuncioFijar(BaseModel):
    fijado: bool


def doc_to_anuncio(doc: dict[str, Any]) -> Anuncio:
    return Anuncio(
        id=str(doc["_id"]),
        titulo=doc["titulo"],
        cuerpo=doc["cuerpo"],
        departamento=doc.get("departamento"),
        fijado=bool(doc.get("fijado", False)),
        expira_en=doc.get("expira_en"),
        creado_en=doc.get("creado_en"),
        autor_id=doc.get("autor_id"),
    )
