"""Punto de entrada de la API FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, usuarios
from app.core.config import settings
from app.core.database import close_mongo, close_redis, connect_mongo, connect_redis, get_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Abre conexiones al arrancar y las cierra al parar el proceso."""
    await connect_mongo()
    await connect_redis()
    # Índices únicos (email) al arrancar.
    from app.services.usuario_service import ensure_indexes

    await ensure_indexes(get_db())
    yield
    await close_redis()
    await close_mongo()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# La cookie de refresh exige credentials; el origen debe coincidir con el frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health fuera de /api/v1 (chequeos operativos, no negocio).
app.include_router(health.router)

# Routers de negocio versionados.
app.include_router(auth.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
