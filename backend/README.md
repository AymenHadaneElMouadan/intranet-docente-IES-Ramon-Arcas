# Backend (FastAPI)

API REST de la Intranet Docente.

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
