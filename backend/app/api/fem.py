"""Endpoints FEM (Formación en Empresas Murcia)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.fem import FemAlumno, FemHorasPatch
from app.models.usuario import UsuarioPublic
from app.services import fem_service

router = APIRouter(prefix="/fem", tags=["FEM"])


@router.get("/alumnos", response_model=list[FemAlumno])
async def list_fem_alumnos(
    current: Annotated[UsuarioPublic, Depends(require_roles("tutor", "admin"))],
    estado: str | None = None,
) -> list[FemAlumno]:
    """Alumnado asignado al tutor (admin ve todos)."""
    is_admin = "admin" in current.roles
    return await fem_service.list_alumnos(
        get_db(),
        tutor_id=None if is_admin else current.id,
        is_admin=is_admin,
        estado=estado,
    )


@router.patch("/alumnos/{id}/horas", response_model=FemAlumno)
async def patch_fem_horas(
    id: str,
    payload: FemHorasPatch,
    current: Annotated[UsuarioPublic, Depends(require_roles("tutor", "admin"))],
) -> FemAlumno:
    """Actualizar horas cursadas (máx. 500)."""
    is_admin = "admin" in current.roles
    return await fem_service.patch_horas(
        get_db(),
        id,
        payload,
        tutor_id=None if is_admin else current.id,
        is_admin=is_admin,
    )
