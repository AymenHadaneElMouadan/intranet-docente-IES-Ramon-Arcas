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
- python-multipart, python-dotenv
- Pytest, Httpx
- Driver MongoDB (Motor) y cliente Redis

### Frontend (PWA)

- React + Vite + TypeScript
- Service worker / manifest (plugin PWA de Vite)

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

## Autenticación (visión)

```
POST /api/v1/auth/google
        ↓
access token (JWT) + refresh token
        ↓
GET /api/v1/auth/me
        ↓
POST /api/v1/auth/refresh  → nuevo access token
        ↓
POST /api/v1/auth/logout   → invalidación del refresh (Redis)
```

- Endpoints protegidos: header `Authorization: Bearer <access_token>`.
- El backend valida siempre identidad y roles; no confiar en datos de autorización del frontend.
- `/auth/refresh` no usa el access token; usa el mecanismo de refresh (detalle de transporte pendiente).

## Frontend

```
pages/ → hooks/ + services/ → API HTTP (Bearer JWT)
components/ → UI reutilizable
```

Priorizar para el arranque de la PWA:

- `GET /api/v1/auth/me`
- `GET /api/v1/usuarios/me/horario`

## Health

Endpoints operativos (fuera del contrato de negocio):

- `GET /health` — proceso vivo
- `GET /health/ready` — dependencias (Mongo, Redis) disponibles

## PENDIENTE DE DECISIÓN

- Payload exacto de `POST /auth/google` y restricción de dominio Google del centro.
- Transporte del refresh token: body JSON vs cookie HttpOnly.
- Algoritmo concreto de asignación de guardias “por rondas”.
- Librerías concretas: generación PDF, email, push (VAPID), AutoFirma, cualquier módulo de “IA”.
- Versiones exactas de React / Vite / TypeScript tras comprobar registro npm.
