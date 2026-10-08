# Intranet Docente — IES Ramón Arcas Meca

PWA de gestión interna para profesorado y equipo directivo. Forma parte del Proyecto Intermodular de 2º DAW y es **independiente** de la Web Pública del centro (otro repositorio, otra BD, otra sesión).

## Estado actual

Base ejecutable en `main` (auth/usuarios + módulos Aymen + cierre de sesión Google):

- Contrato API OpenAPI 3.x (`openapi/openapi.yaml`) alineado a la norma FastAPI (`detail`, paginación, `Location`)
- Backend FastAPI: health, auth Google + JWT + refresh HttpOnly (Redis), usuarios (+ RGPD), anuncios, tickets, FEM, dashboard
- Frontend Vite/React: login Google (GIS/FedCM), `auth/me`, perfil y horario propio (horario solo si la cuenta está `activo`)
- Docker Compose: MongoDB, Redis, backend
- **Runtime pendiente (contrato ya definido):** guardias, ausencias (+ justificante/PDF/firma), retrasos, notificaciones, auditoría

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

### Login Google

1. Crea un OAuth Client ID (aplicación web) en Google Cloud.
2. Orígenes de JavaScript autorizados: `http://localhost:5173` y `http://127.0.0.1:5173`.
3. Pon el **mismo** Client ID en:
   - `GOOGLE_CLIENT_ID` → `backend/.env`
   - `VITE_GOOGLE_CLIENT_ID` → `frontend/.env`
4. Recrea el backend (`docker compose up -d --force-recreate backend`) y reinicia Vite.
5. Abre el front en **Chrome o Edge del sistema** (el preview embebido del editor suele bloquear el popup de Google). Si hace falta, permite ventanas emergentes para `localhost:5173`.

### Altas y aprobación admin

- El primer login OAuth crea el usuario en estado `pendiente` (puede ver `/auth/me`, no el resto de negocio).
- Un **admin activo** aprueba con `PATCH /api/v1/usuarios/{id}` y cuerpo `{ "estado": "activo" }` (Swagger en `/docs` + Bearer).
- En local, si aún no hay admin: promover un usuario en Mongo (`estado: activo`, roles `admin` + `docente`) y volver a iniciar sesión.

## Ramas de trabajo

- Integrar cambios a **`main` mediante Pull Request** (mismo repo, sin forks).
- Features grandes en ramas propias (p. ej. `Adrian-guardias-ausencias`).
- Antes de seguir o de abrir PR: `git fetch` y `git merge origin/main` en tu rama para evitar conflictos grandes.

## Ver el contrato en Swagger Editor

1. Abre [https://editor.swagger.io](https://editor.swagger.io)
2. File → Import file (`openapi/openapi.yaml`)
3. Tags: Auth, Usuarios, Anuncios, Guardias, Ausencias, Tickets, FEM, Dashboard, Health (y Retrasos, Notificaciones, Auditoria en contrato)

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [AGENTS.md](AGENTS.md) | Contexto permanente para agentes / Cursor |
| [docs/architecture.md](docs/architecture.md) | Stack y capas |
| [docs/api-contract.md](docs/api-contract.md) | Tabla oficial de endpoints |
| [docs/roles-and-permissions.md](docs/roles-and-permissions.md) | Roles y permisos |
| [openapi/openapi.yaml](openapi/openapi.yaml) | Contrato OpenAPI |
| [backend/README.md](backend/README.md) | Arranque API, auth, tests |
| [frontend/README.md](frontend/README.md) | Arranque PWA y sesión |

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
2. **Adrian** (rama `Adrian-guardias-ausencias`): guardias, ausencias, justificante, PDF y firma (formato de firma: PENDIENTE DE DECISIÓN / Autofirma).
3. Runtime de retrasos, notificaciones y auditoría sobre la norma `{detail}`.
