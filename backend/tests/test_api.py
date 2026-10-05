"""Tests de health, auth y usuarios (requieren Mongo + Redis locales o Docker)."""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Forzar entorno de test antes de importar la app.
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "intranet_docente_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters!!")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("COOKIE_SECURE", "false")

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import get_db, get_redis
from app.main import app
from app.services import auth_service


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Cliente HTTP async con lifespan real (Mongo/Redis)."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await get_db()["usuarios"].delete_many({})
            redis = get_redis()
            async for key in redis.scan_iter("refresh:*"):
                await redis.delete(key)
            yield ac


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient) -> None:
    res = await client.get("/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["mongo"] is True
    assert body["redis"] is True


@pytest.mark.asyncio
async def test_auth_me_unauthorized(client: AsyncClient) -> None:
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"] == "No autenticado"


@pytest.mark.asyncio
async def test_google_login_refresh_logout(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Flujo completo con Google mockeado (sin llamada real a Google)."""

    def fake_verify(_token: str) -> dict:
        return {
            "email": "docente@example.com",
            "sub": "google-sub-1",
            "name": "Docente Demo",
        }

    monkeypatch.setattr(auth_service, "verify_google_id_token", fake_verify)

    login = await client.post("/api/v1/auth/google", json={"id_token": "fake"})
    assert login.status_code == 200
    access = login.json()["access_token"]
    assert login.cookies.get("refresh_token")

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "docente@example.com"
    assert me.json()["estado"] == "pendiente"

    refresh = await client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200
    new_access = refresh.json()["access_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert logout.status_code == 200

    again = await client.post("/api/v1/auth/refresh")
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_usuarios_admin_flow(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify(_token: str) -> dict:
        return {"email": "admin@example.com", "sub": "google-admin", "name": "Admin"}

    monkeypatch.setattr(auth_service, "verify_google_id_token", fake_verify)

    login = await client.post("/api/v1/auth/google", json={"id_token": "fake-admin"})
    access = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    admin_id = me.json()["id"]

    # Sin rol admin → 403 al listar
    listed = await client.get("/api/v1/usuarios", headers={"Authorization": f"Bearer {access}"})
    assert listed.status_code == 403

    # Promueve a admin
    from app.models.usuario import UsuarioEstado, UsuarioPatch
    from app.services import usuario_service

    await usuario_service.patch_usuario(
        get_db(),
        admin_id,
        UsuarioPatch(roles=["admin", "docente"], estado=UsuarioEstado.activo),
    )

    # Re-login para claims actualizados en JWT
    login2 = await client.post("/api/v1/auth/google", json={"id_token": "fake-admin"})
    access2 = login2.json()["access_token"]

    created = await client.post(
        "/api/v1/usuarios",
        headers={"Authorization": f"Bearer {access2}"},
        json={
            "name": "Pepa",
            "email": "pepa@example.com",
            "departamento": "FOL",
            "roles": ["docente"],
        },
    )
    assert created.status_code == 201
    assert created.headers.get("location", "").startswith("/api/v1/usuarios/")
    assert created.json()["name"] == "Pepa"

    page = await client.get(
        "/api/v1/usuarios?page=1&limit=10",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert page.status_code == 200
    body = page.json()
    assert "items" in body and body["total"] >= 2

    horario = await client.get(
        "/api/v1/usuarios/me/horario",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert horario.status_code == 200
    assert "dias" in horario.json()
