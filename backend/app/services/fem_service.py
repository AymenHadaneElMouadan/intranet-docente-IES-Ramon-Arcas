"""Servicio FEM (Formación en Empresas Murcia)."""

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.models.fem import FemAlumno, FemHorasPatch, doc_to_fem_alumno

COLLECTION = "fem_alumnos"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index("tutor_id")
    await db[COLLECTION].create_index("estado")


def _oid(resource_id: str) -> ObjectId:
    if not ObjectId.is_valid(resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno FEM no encontrado")
    return ObjectId(resource_id)


async def list_alumnos(
    db: AsyncIOMotorDatabase,
    *,
    tutor_id: str | None,
    is_admin: bool,
    estado: str | None,
) -> list[FemAlumno]:
    query: dict[str, Any] = {}
    if not is_admin:
        if tutor_id is None:
            return []
        query["tutor_id"] = tutor_id
    if estado:
        query["estado"] = estado
    cursor = db[COLLECTION].find(query).sort("nombre", 1)
    return [doc_to_fem_alumno(doc) async for doc in cursor]


async def patch_horas(
    db: AsyncIOMotorDatabase,
    alumno_id: str,
    payload: FemHorasPatch,
    *,
    tutor_id: str | None,
    is_admin: bool,
) -> FemAlumno:
    doc = await db[COLLECTION].find_one({"_id": _oid(alumno_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno FEM no encontrado")
    if not is_admin and doc.get("tutor_id") != tutor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Alumno no asignado a este tutor")

    result = await db[COLLECTION].find_one_and_update(
        {"_id": _oid(alumno_id)},
        {
            "$set": {
                "horas_cursadas": payload.horas_cursadas,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno FEM no encontrado")
    return doc_to_fem_alumno(result)


async def seed_alumno_demo(
    db: AsyncIOMotorDatabase,
    *,
    nombre: str,
    tutor_id: str,
    empresa: str = "Empresa Demo",
) -> FemAlumno:
    """Utilidad de tests / demos locales."""
    doc = {
        "nombre": nombre,
        "empresa": empresa,
        "estado": "activo",
        "horas_cursadas": 0,
        "horas_totales": 500,
        "tutor_id": tutor_id,
        "creado_en": datetime.now(UTC),
    }
    result = await db[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_fem_alumno(doc)
