"""Esquemas del dashboard de KPIs."""

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    ausencias_hoy: int = 0
    guardias_pendientes: int = 0
    tickets_abiertos: int = 0
    docentes_activos: int = 0
    alumnos_fem_activos: int = 0
