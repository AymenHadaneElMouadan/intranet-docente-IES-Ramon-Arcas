"""Conexiones asíncronas a MongoDB (Motor) y Redis."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.config import settings

_mongo_client: AsyncIOMotorClient | None = None
_redis: Redis | None = None


async def connect_mongo() -> None:
    """Inicializa el cliente Motor al arrancar la app."""
    global _mongo_client
    _mongo_client = AsyncIOMotorClient(settings.mongodb_uri)


async def close_mongo() -> None:
    """Cierra el cliente Mongo al apagar la app."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


def get_db() -> AsyncIOMotorDatabase:
    """Devuelve la base de datos principal. Requiere connect_mongo previo."""
    if _mongo_client is None:
        raise RuntimeError("MongoDB no está conectado")
    return _mongo_client[settings.mongodb_db]


async def connect_redis() -> None:
    """Abre el cliente Redis asíncrono."""
    global _redis
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Cierra Redis."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis:
    """Cliente Redis para refresh tokens y caché futura."""
    if _redis is None:
        raise RuntimeError("Redis no está conectado")
    return _redis
