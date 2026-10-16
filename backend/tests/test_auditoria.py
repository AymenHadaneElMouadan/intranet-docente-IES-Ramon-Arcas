"""Tests del módulo de auditoría (requieren Mongo + Redis)."""

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "intranet_docente_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters!!")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ENVIRONMENT", "development")

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import get_db, get_redis
from app.main import app
from app.models.usuario import Role, UsuarioEstado, UsuarioPatch
from app.services import auth_service, usuario_service


def _google_claims(**overrides: object) -> dict:
    base = {
        "email": "docente@example.com",
        "sub": "google-sub-1",
        "name": "Docente Demo",
        "email_verified": True,
    }
    base.update(overrides)
    return base


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            db = get_db()
            await db["usuarios"].delete_many({})
            await db["auditoria"].delete_many({})
            redis = get_redis()
            async for key in redis.scan_iter("refresh:*"):
                await redis.delete(key)
            yield ac


async def _activate_as(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    email: str,
    sub: str,
    name: str,
    roles: list[Role],
) -> str:
    monkeypatch.setattr(
        auth_service,
        "verify_google_id_token",
        lambda _t: _google_claims(email=email, sub=sub, name=name),
    )
    login = await client.post("/api/v1/auth/google", json={"id_token": f"fake-{sub}"})
    access = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    await usuario_service.patch_usuario(
        get_db(),
        me.json()["id"],
        UsuarioPatch(roles=roles, estado=UsuarioEstado.activo),
    )
    login2 = await client.post("/api/v1/auth/google", json={"id_token": f"fake-{sub}"})
    return login2.json()["access_token"]


@pytest.mark.asyncio
async def test_auditoria_forbidden_for_docente(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="doc@example.com",
        sub="google-doc",
        name="Docente",
        roles=[Role.docente],
    )
    res = await client.get(
        "/api/v1/auditoria",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_auditoria_filters_and_invalid_range(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="admin@example.com",
        sub="google-admin-aud",
        name="Admin Aud",
        roles=[Role.admin],
    )
    headers = {"Authorization": f"Bearer {access}"}

    listed = await client.get("/api/v1/auditoria?accion=auth.login_google", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["limit"] == 10
    assert body["total"] >= 1
    assert all(item["accion"] == "auth.login_google" for item in body["items"])

    ahora = datetime.now(UTC)
    desde = (ahora - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    hasta = (ahora + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    ranged = await client.get(
        f"/api/v1/auditoria?desde={desde}&hasta={hasta}",
        headers=headers,
    )
    assert ranged.status_code == 200
    assert ranged.json()["total"] >= 1

    bad = await client.get(
        f"/api/v1/auditoria?desde={hasta}&hasta={desde}",
        headers=headers,
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_auditoria_put_roles_before_after(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="admin-roles@example.com",
        sub="google-admin-roles",
        name="Admin Roles",
        roles=[Role.admin],
    )
    headers = {"Authorization": f"Bearer {access}"}

    created = await client.post(
        "/api/v1/usuarios",
        headers=headers,
        json={
            "name": "Pepa",
            "email": "pepa-aud@example.com",
            "departamento": "FOL",
            "roles": ["docente"],
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    put = await client.put(
        f"/api/v1/usuarios/{user_id}/roles",
        headers=headers,
        json={"roles": ["docente", "tutor"]},
    )
    assert put.status_code == 200

    aud = await client.get(
        "/api/v1/auditoria?accion=usuarios.put_roles",
        headers=headers,
    )
    assert aud.status_code == 200
    items = aud.json()["items"]
    assert items
    detalle = items[0]["detalle"]
    assert detalle["antes"]["roles"] == ["docente"]
    assert set(detalle["despues"]["roles"]) == {"docente", "tutor"}


@pytest.mark.asyncio
async def test_auditoria_login_failed(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(_token: str) -> dict:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="id_token inválido")

    monkeypatch.setattr(auth_service, "verify_google_id_token", _raise)
    res = await client.post("/api/v1/auth/google", json={"id_token": "bad"})
    assert res.status_code == 401

    access = await _activate_as(
        client,
        monkeypatch,
        email="admin-fail@example.com",
        sub="google-admin-fail",
        name="Admin Fail",
        roles=[Role.admin],
    )
    aud = await client.get(
        "/api/v1/auditoria?accion=auth.login_failed",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert aud.status_code == 200
    assert aud.json()["total"] >= 1
    assert aud.json()["items"][0]["detalle"]["motivo"] == "id_token inválido"


@pytest.mark.asyncio
async def test_auditoria_logout_recorded(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="admin-out@example.com",
        sub="google-admin-out",
        name="Admin Out",
        roles=[Role.admin],
    )
    headers = {"Authorization": f"Bearer {access}"}
    logout = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200

    # Tras logout hace falta nuevo login para consultar.
    access2 = await _activate_as(
        client,
        monkeypatch,
        email="admin-out@example.com",
        sub="google-admin-out",
        name="Admin Out",
        roles=[Role.admin],
    )
    aud = await client.get(
        "/api/v1/auditoria?accion=auth.logout",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert aud.status_code == 200
    assert aud.json()["total"] >= 1
