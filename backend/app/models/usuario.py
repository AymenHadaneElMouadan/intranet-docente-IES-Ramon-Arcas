"""Esquemas de usuario y horario."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    admin = "admin"
    directiva = "directiva"
    jefatura = "jefatura"
    docente = "docente"
    tutor = "tutor"
    responsable_ticket = "responsable_ticket"


class UsuarioEstado(str, Enum):
    pendiente = "pendiente"
    activo = "activo"
    inactivo = "inactivo"


class BloqueHorario(BaseModel):
    inicio: str
    fin: str
    tipo: str = Field(description="clase | guardia | reduccion")
    asignatura: str | None = None
    grupo: str | None = None
    aula: str | None = None


class UsuarioPublic(BaseModel):
    """Representación pública del usuario (sin secretos internos)."""

    id: str
    name: str
    email: EmailStr
    departamento: str
    roles: list[str]
    estado: UsuarioEstado


class UsuarioMe(UsuarioPublic):
    permisos: list[str] = Field(default_factory=list)


class UsuarioCreate(BaseModel):
    name: str
    email: EmailStr
    departamento: str
    roles: list[str] = Field(default_factory=lambda: [Role.docente.value])
    estado: UsuarioEstado = UsuarioEstado.activo


class UsuarioPatch(BaseModel):
    name: str | None = None
    departamento: str | None = None
    roles: list[str] | None = None
    estado: UsuarioEstado | None = None


class PaginatedUsuarios(BaseModel):
    items: list[UsuarioPublic]
    page: int
    limit: int
    total: int


class Horario(BaseModel):
    usuario_id: str
    dias: dict[str, list[BloqueHorario]] = Field(default_factory=dict)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GoogleAuthRequest(BaseModel):
    id_token: str


def doc_to_usuario(doc: dict[str, Any]) -> UsuarioPublic:
    """Convierte un documento Mongo a UsuarioPublic."""
    return UsuarioPublic(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        departamento=doc.get("departamento", ""),
        roles=list(doc.get("roles", [])),
        estado=UsuarioEstado(doc.get("estado", UsuarioEstado.pendiente.value)),
    )


# Semilla de horario de ejemplo para demos locales.
DEFAULT_HORARIO_DIAS: dict[str, list[dict[str, Any]]] = {
    "lunes": [
        {"inicio": "08:00", "fin": "09:00", "tipo": "clase", "asignatura": "DWES", "grupo": "2DAW", "aula": "A1"},
        {"inicio": "11:00", "fin": "12:00", "tipo": "guardia"},
    ],
    "martes": [
        {"inicio": "09:00", "fin": "10:00", "tipo": "clase", "asignatura": "DWEC", "grupo": "2DAW", "aula": "A1"},
    ],
    "miercoles": [],
    "jueves": [
        {"inicio": "10:00", "fin": "11:00", "tipo": "reduccion"},
    ],
    "viernes": [
        {"inicio": "08:00", "fin": "09:00", "tipo": "clase", "asignatura": "DIW", "grupo": "2DAW", "aula": "B2"},
    ],
}


def utcnow() -> datetime:
    return datetime.now(UTC)
