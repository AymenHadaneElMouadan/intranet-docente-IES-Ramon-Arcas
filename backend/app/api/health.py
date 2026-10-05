"""Chequeos de liveness y readiness (Docker / monitorización)."""

from fastapi import APIRouter, HTTPException, status

from app.core.database import get_db, get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_live() -> dict[str, str]:
    """El proceso responde: no comprueba bases de datos."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready() -> dict[str, bool | str]:
    """Comprueba MongoDB y Redis antes de aceptar tráfico real."""
    mongo_ok = False
    redis_ok = False
    try:
        await get_db().command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False
    try:
        redis_ok = bool(await get_redis().ping())
    except Exception:
        redis_ok = False

    if not (mongo_ok and redis_ok):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependencias no disponibles",
        )
    return {"status": "ready", "mongo": mongo_ok, "redis": redis_ok}
