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
async def test_auth_me_invalid_jwt_sub_is_401(client: AsyncClient) -> None:
    """sub que no es ObjectId (o no existe) → 401, nunca 404."""
    from app.core.security import create_access_token

    token, _ = create_access_token(user_id="not-a-valid-objectid", roles=["docente"])
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.json()["detail"] == "No autenticado"


@pytest.mark.asyncio
async def test_google_rejects_unverified_email(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        auth_service,
        "verify_google_id_token",
        lambda _t: _google_claims(email_verified=False),
    )
    res = await client.post("/api/v1/auth/google", json={"id_token": "fake"})
    assert res.status_code == 401
    assert "verificado" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_login_refresh_logout(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Flujo completo con Google mockeado (sin llamada real a Google)."""

    monkeypatch.setattr(auth_service, "verify_google_id_token", lambda _t: _google_claims())

    login = await client.post("/api/v1/auth/google", json={"id_token": "fake"})
    assert login.status_code == 200
    access = login.json()["access_token"]
    assert login.cookies.get("refresh_token")

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "docente@example.com"
    assert me.json()["estado"] == "pendiente"

    # Pendiente: puede /auth/me pero no endpoints de negocio.
    horario = await client.get(
        "/api/v1/usuarios/me/horario",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert horario.status_code == 403

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
    monkeypatch.setattr(
        auth_service,
        "verify_google_id_token",
        lambda _t: _google_claims(email="admin@example.com", sub="google-admin", name="Admin"),
    )

    login = await client.post("/api/v1/auth/google", json={"id_token": "fake-admin"})
    access = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    admin_id = me.json()["id"]

    # Pendiente → 403 (cuenta no activa), aunque tuviera roles.
    listed = await client.get("/api/v1/usuarios", headers={"Authorization": f"Bearer {access}"})
    assert listed.status_code == 403

    await usuario_service.patch_usuario(
        get_db(),
        admin_id,
        UsuarioPatch(roles=[Role.admin, Role.docente], estado=UsuarioEstado.activo),
    )

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

    # Rol inválido → 422
    bad_role = await client.post(
        "/api/v1/usuarios",
        headers={"Authorization": f"Bearer {access2}"},
        json={
            "name": "X",
            "email": "x@example.com",
            "departamento": "FOL",
            "roles": ["superadmin"],
        },
    )
    assert bad_role.status_code == 422

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


async def _activate_as(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    email: str,
    sub: str,
    name: str,
    roles: list[Role],
) -> str:
    """Login Google mock + activar cuenta con roles; devuelve access token."""
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
async def test_anuncios_flow(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="directiva@example.com",
        sub="google-dir",
        name="Directiva",
        roles=[Role.directiva, Role.docente],
    )
    headers = {"Authorization": f"Bearer {access}"}

    created = await client.post(
        "/api/v1/anuncios",
        headers=headers,
        json={"titulo": "Claustro", "cuerpo": "Mañana a las 12", "departamento": None},
    )
    assert created.status_code == 201
    assert created.headers.get("location", "").startswith("/api/v1/anuncios/")
    anuncio_id = created.json()["id"]

    feed = await client.get("/api/v1/anuncios", headers=headers)
    assert feed.status_code == 200
    assert any(a["id"] == anuncio_id for a in feed.json())

    # Fijar requiere admin
    fijar = await client.patch(
        f"/api/v1/anuncios/{anuncio_id}/fijar",
        headers=headers,
        json={"fijado": True},
    )
    assert fijar.status_code == 403

    admin_access = await _activate_as(
        client,
        monkeypatch,
        email="admin2@example.com",
        sub="google-admin2",
        name="Admin2",
        roles=[Role.admin],
    )
    fijar_ok = await client.patch(
        f"/api/v1/anuncios/{anuncio_id}/fijar",
        headers={"Authorization": f"Bearer {admin_access}"},
        json={"fijado": True},
    )
    assert fijar_ok.status_code == 200
    assert fijar_ok.json()["fijado"] is True


@pytest.mark.asyncio
async def test_tickets_state_machine(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="docente-t@example.com",
        sub="google-doc-t",
        name="Docente T",
        roles=[Role.docente],
    )
    headers = {"Authorization": f"Bearer {access}"}

    created = await client.post(
        "/api/v1/tickets",
        headers=headers,
        json={"tipo": "rmi", "titulo": "Proyector roto", "descripcion": "Aula A1"},
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert created.json()["estado"] == "abierto"

    # Docente no puede transicionar
    bad = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        headers=headers,
        json={"estado": "en_proceso"},
    )
    assert bad.status_code == 403

    resp_access = await _activate_as(
        client,
        monkeypatch,
        email="resp@example.com",
        sub="google-resp",
        name="Resp",
        roles=[Role.responsable_ticket, Role.docente],
    )
    resp_headers = {"Authorization": f"Bearer {resp_access}"}

    step1 = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        headers=resp_headers,
        json={"estado": "en_proceso"},
    )
    assert step1.status_code == 200
    assert step1.json()["estado"] == "en_proceso"

    # Transición inválida abierto saltando
    invalid = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        headers=resp_headers,
        json={"estado": "cerrado"},
    )
    assert invalid.status_code == 422

    comment = await client.post(
        f"/api/v1/tickets/{ticket_id}/comentarios",
        headers=headers,
        json={"cuerpo": "Gracias"},
    )
    assert comment.status_code == 201
    assert comment.json()["cuerpo"] == "Gracias"


@pytest.mark.asyncio
async def test_fem_and_dashboard(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import fem_service

    tutor_access = await _activate_as(
        client,
        monkeypatch,
        email="tutor@example.com",
        sub="google-tutor",
        name="Tutor",
        roles=[Role.tutor, Role.docente],
    )
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tutor_access}"},
    )
    tutor_id = me.json()["id"]
    alumno = await fem_service.seed_alumno_demo(
        get_db(), nombre="Ana FEM", tutor_id=tutor_id
    )

    listed = await client.get(
        "/api/v1/fem/alumnos",
        headers={"Authorization": f"Bearer {tutor_access}"},
    )
    assert listed.status_code == 200
    assert any(a["id"] == alumno.id for a in listed.json())

    patched = await client.patch(
        f"/api/v1/fem/alumnos/{alumno.id}/horas",
        headers={"Authorization": f"Bearer {tutor_access}"},
        json={"horas_cursadas": 120},
    )
    assert patched.status_code == 200
    assert patched.json()["horas_cursadas"] == 120

    admin_access = await _activate_as(
        client,
        monkeypatch,
        email="admin-kpi@example.com",
        sub="google-kpi",
        name="KPI Admin",
        roles=[Role.admin, Role.directiva],
    )
    kpis = await client.get(
        "/api/v1/dashboard/kpis",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert kpis.status_code == 200
    body = kpis.json()
    assert body["docentes_activos"] >= 1
    assert body["alumnos_fem_activos"] >= 1


@pytest.mark.asyncio
async def test_usuarios_rgpd_me(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    access = await _activate_as(
        client,
        monkeypatch,
        email="rgpd@example.com",
        sub="google-rgpd",
        name="Nombre Viejo",
        roles=[Role.docente],
    )
    headers = {"Authorization": f"Bearer {access}"}

    patched = await client.patch(
        "/api/v1/usuarios/me",
        headers=headers,
        json={"name": "Nombre Nuevo"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Nombre Nuevo"

    datos = await client.get("/api/v1/usuarios/me/datos", headers=headers)
    assert datos.status_code == 200
    assert datos.json()["usuario"]["email"] == "rgpd@example.com"
    assert "exportado_en" in datos.json()
