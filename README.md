# Intranet Docente — IES Ramón Arcas Meca

PWA de gestión interna para profesorado y equipo directivo. Forma parte del Proyecto Intermodular de 2º DAW y es **independiente** de la Web Pública del centro (otro repositorio, otra BD, otra sesión).

## Estado actual

Cimientos ejecutables (base Adrián + módulos Aymen en esta rama):

- Contrato API OpenAPI 3.x (`openapi/openapi.yaml`) alineado a la norma FastAPI (`detail`, paginación, `Location`)
- Backend FastAPI: health, auth Google+JWT+refresh HttpOnly (Redis), usuarios (+ RGPD), anuncios, tickets, FEM, dashboard
- Contrato preparado: retrasos, notificaciones, auditoría (runtime pendiente)
- Frontend Vite/React: login Google, `auth/me`, horario propio
- Docker Compose: MongoDB, Redis, backend

## Arranque rápido

```bash
# 1) Variables del backend
copy backend\.env.example backend\.env

# 2) Infra + API
docker compose up --build

# 3) Frontend (otra terminal)
cd frontend
copy .env.example .env
npm install
npm run dev
```

- API: http://localhost:8000/docs  
- Front: http://localhost:5173  
- Health: http://localhost:8000/health  

Configura `GOOGLE_CLIENT_ID` (backend) y `VITE_GOOGLE_CLIENT_ID` (frontend) para el login real con Google.

## Ver el contrato en Swagger Editor

1. Abre [https://editor.swagger.io](https://editor.swagger.io)
2. File → Import file (`openapi/openapi.yaml`)
3. Tags: Auth, Usuarios, Anuncios, Guardias, Ausencias, Tickets, FEM, Dashboard, Health

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [AGENTS.md](AGENTS.md) | Contexto permanente para agentes / Cursor |
| [docs/architecture.md](docs/architecture.md) | Stack y capas |
| [docs/api-contract.md](docs/api-contract.md) | Tabla oficial de endpoints |
| [docs/roles-and-permissions.md](docs/roles-and-permissions.md) | Roles y permisos |
| [openapi/openapi.yaml](openapi/openapi.yaml) | Contrato OpenAPI |

## Estructura

```
├── frontend/          # React + Vite + TypeScript
├── backend/           # FastAPI
├── openapi/
├── docs/
└── docker-compose.yml
```

## Próximos pasos

1. Validar contrato con el profesorado.
2. Módulos Aymen (en curso en rama `Aymen`): anuncios, tickets, FEM, dashboard + contrato RGPD/retrasos/notificaciones/auditoría.
3. Módulos Adrian (siguientes): guardias, ausencias, firma PDF.
4. Implementar runtime de retrasos, notificaciones y auditoría sobre la norma `{detail}`.
