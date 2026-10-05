# Arquitectura — Intranet Docente

## Sistemas

El Proyecto Intermodular DAW del IES Ramón Arcas Meca tiene **dos sistemas independientes**:

| Sistema | Stack | Este repo |
|---------|-------|-----------|
| Web Pública | PHP nativo + MySQL/MariaDB | No |
| Intranet Docente | FastAPI + MongoDB + Redis + React PWA | **Sí** |

No comparten base de datos, sesión ni autenticación.

## Stack tecnológico

### Backend

- Python 3.x
- FastAPI (>= 0.110)
- Uvicorn (>= 0.29)
- PyJWT (>= 2.8)
- google-auth (verificación de `id_token`)
- python-multipart, python-dotenv / pydantic-settings
- Pytest, Httpx
- Driver MongoDB (Motor) y cliente Redis

### Frontend (PWA)

- React + Vite + TypeScript
- Service worker / manifest (plugin PWA de Vite; arranque mínimo sin PWA completa)

### Infraestructura local

- Docker Compose: MongoDB, Redis, backend

## Capas del backend

```
Router (api/) → Service (services/) → Persistencia (models / acceso a datos)
```

- **Routers**: HTTP fino — validación de entrada vía esquemas, llamada al servicio, respuesta.
- **Services**: reglas de negocio (guardias, ausencias, tickets, PDF, etc.).
- **Models**: esquemas Pydantic / documentos MongoDB.
- **Core**: configuración, seguridad JWT, dependencias FastAPI (`Depends()`).
- **Utils**: helpers (email, push, etc.) cuando existan.

La lógica de negocio **no** vive en el router.

## Autenticación

```
POST /api/v1/auth/google  { "id_token": "..." }
        ↓
access token (JWT en JSON) + refresh (cookie HttpOnly)
        ↓
GET /api/v1/auth/me
        ↓
POST /api/v1/auth/refresh  → lee cookie, emite nuevo access
        ↓
POST /api/v1/auth/logout   → invalidación del refresh (Redis) + borra cookie
```

- Endpoints protegidos: header `Authorization: Bearer <access_token>`.
- El backend valida siempre identidad y roles; no confiar en datos de autorización del frontend.
- Refresh: cookie HttpOnly `refresh_token`; valor opaco guardado en Redis.
- OAuth Google sin restricción de dominio; usuarios nuevos quedan en estado `pendiente` hasta aprobación admin.

## Frontend

```
pages/ → hooks/ + services/ → API HTTP (Bearer JWT + credentials include)
components/ → UI reutilizable
```

Priorizar para el arranque de la PWA:

- `GET /api/v1/auth/me`
- `GET /api/v1/usuarios/me/horario`

## Health

Endpoints operativos (fuera del contrato de negocio):

- `GET /health` — proceso vivo
- `GET /health/ready` — dependencias (Mongo, Redis) disponibles

## Decisiones cerradas

- Payload `POST /auth/google`: `id_token`.
- Sin whitelist de dominio Google.
- Refresh token en cookie HttpOnly (no body).
- Errores API: `{"detail": "..."}` (norma FastAPI / apuntes).
- Listados paginados: `{ items, page, limit, total }`.

## Pendiente de decisión

- Algoritmo concreto de asignación de guardias “por rondas”.
- Librerías concretas: generación PDF, email, push (VAPID), AutoFirma, módulo de IA para RRSS.
