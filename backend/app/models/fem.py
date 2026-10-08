"""Esquemas FEM (Formación en Empresas Murcia)."""

from typing import Any

from pydantic import BaseModel, Field


class FemAlumno(BaseModel):
    id: str
    nombre: str
    empresa: str | None = None
    estado: str | None = None
    horas_cursadas: float = 0
    horas_totales: float = 500
    tutor_id: str | None = None


class FemHorasPatch(BaseModel):
    horas_cursadas: float = Field(ge=0, le=500)


def doc_to_fem_alumno(doc: dict[str, Any]) -> FemAlumno:
    return FemAlumno(
        id=str(doc["_id"]),
        nombre=doc["nombre"],
        empresa=doc.get("empresa"),
        estado=doc.get("estado"),
        horas_cursadas=float(doc.get("horas_cursadas", 0)),
        horas_totales=float(doc.get("horas_totales", 500)),
        tutor_id=doc.get("tutor_id"),
    )
