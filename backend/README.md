# Backend (FastAPI)

API REST de la Intranet Docente.

## Módulos con runtime

Auth, usuarios (RGPD), anuncios, tickets, FEM, dashboard y health.  
Contrato sin implementar aún: guardias, ausencias, retrasos, notificaciones, auditoría.

## Arranque local (API en el host)

1. Levanta Mongo y Redis: `docker compose up mongo redis -d`
2. Entorno virtual e instalación:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Ajusta MONGODB_URI=mongodb://localhost:27017 y REDIS_URL=redis://localhost:6379/0
uvicorn app.main:app --reload --port 8000
```

## Arranque con Docker Compose (raíz del repo)

```bash
copy backend\.env.example backend\.env
docker compose up --build
```

API en `http://localhost:8000` — documentación interactiva en `/docs`.

## Seguridad de sesión (resumen)

- Access JWT: header Bearer; en el frontend solo en memoria (se recupera con cookie refresh).
- Refresh: cookie HttpOnly; Redis.
- Roles de autorización se leen de Mongo en cada request (no se confían los del JWT).
- JWT con `sub` inválido o usuario inexistente → **401** (no 404).
- Cuentas `pendiente` (alta OAuth): pueden `/auth/me` y logout; el negocio exige `activo`.
- Aprobar un alta: admin activo → `PATCH /api/v1/usuarios/{id}` con `{ "estado": "activo" }`.
- Fuera de development: `JWT_SECRET` obligatorio y ≥32 caracteres (falla al arrancar si no).
- `GOOGLE_CLIENT_ID` debe coincidir con el del frontend.

## Capas

```
app/
├── api/        # Routers (HTTP fino)
├── core/       # Config, seguridad JWT, Depends()
├── models/     # Esquemas Pydantic
├── services/   # Lógica de negocio
└── ...
tests/          # Pytest
```

## Tests

Con Mongo y Redis en marcha:

```bash
cd backend
pytest -q
```

Contrato: `../openapi/openapi.yaml` y `../docs/api-contract.md`.
