"""Endpoints del dashboard de KPIs."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.dashboard import DashboardKpis
from app.models.usuario import UsuarioPublic
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=DashboardKpis)
async def get_dashboard_kpis(
    _current: Annotated[UsuarioPublic, Depends(require_roles("directiva", "admin"))],
) -> DashboardKpis:
    """Indicadores consolidados del centro."""
    return await dashboard_service.get_kpis(get_db())
