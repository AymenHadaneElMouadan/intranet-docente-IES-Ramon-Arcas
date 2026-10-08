"""Servicio de KPIs del dashboard."""

from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.dashboard import DashboardKpis
from app.models.ticket import TicketEstado
from app.models.usuario import UsuarioEstado


async def get_kpis(db: AsyncIOMotorDatabase) -> DashboardKpis:
    """Agrega contadores desde las colecciones existentes."""
    hoy = datetime.now(UTC).date().isoformat()

    ausencias_hoy = await db["ausencias"].count_documents(
        {"fecha_inicio": {"$lte": hoy}, "fecha_fin": {"$gte": hoy}}
    )
    guardias_pendientes = await db["guardias"].count_documents({"estado": "pendiente"})
    tickets_abiertos = await db["tickets"].count_documents(
        {"estado": {"$in": [TicketEstado.abierto.value, TicketEstado.en_proceso.value]}}
    )
    docentes_activos = await db["usuarios"].count_documents(
        {"estado": UsuarioEstado.activo.value}
    )
    alumnos_fem_activos = await db["fem_alumnos"].count_documents({"estado": "activo"})

    return DashboardKpis(
        ausencias_hoy=ausencias_hoy,
        guardias_pendientes=guardias_pendientes,
        tickets_abiertos=tickets_abiertos,
        docentes_activos=docentes_activos,
        alumnos_fem_activos=alumnos_fem_activos,
    )
