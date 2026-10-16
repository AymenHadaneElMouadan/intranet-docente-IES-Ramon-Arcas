# Intranet Docente — IES Ramón Arcas Meca

PWA de gestión interna para profesorado y equipo directivo. Forma parte del Proyecto Intermodular de 2º DAW y es **independiente** de la Web Pública del centro (otro repositorio, otra BD, otra sesión).

## Estado actual

Base ejecutable en `main` (auth/usuarios + módulos Aymen + cierre de sesión Google):

- Contrato API OpenAPI 3.x (`openapi/openapi.yaml`) alineado a la norma FastAPI (`detail`, paginación, `Location`)
- Backend FastAPI: health, auth Google + JWT + refresh HttpOnly (Redis), usuarios (+ RGPD), anuncios, tickets, FEM, dashboard, auditoría mínima
- Frontend Vite/React: login Google (GIS/FedCM), `auth/me`, perfil y horario propio, UI admin de usuarios (horario solo si la cuenta está `activo`)
- Docker Compose: MongoDB, Redis, backend (healthchecks + red `intranet`)
- **Runtime pendiente (contrato ya definido):** guardias, ausencias (+ justificante/PDF/firma), retrasos, notificaciones (runtime completo)

## Arranque rápido

```bash
# 1) Variables del backend (obligatorio: docker compose usa env_file)
copy backend\.env.example backend\.env
# Edita GOOGLE_CLIENT_ID y JWT_SECRET en backend\.env

# 2) Infra + API (Mongo, Redis y backend con healthchecks)
docker compose up --build

# 3) Frontend (otra terminal; no va en Compose)
cd frontend
copy .env.example .env
# Edita VITE_GOOGLE_CLIENT_ID (mismo Client ID que el backend)
npm install
npm run dev
```

- API: http://localhost:8000/docs  
- Front: http://localhost:5173  
- Health (liveness): http://localhost:8000/health  
- Ready (Mongo + Redis): http://localhost:8000/health/ready  

Compose espera a que Mongo y Redis estén healthy antes de arrancar el backend. El servicio `backend` expone su propio healthcheck sobre `/health`.

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

### Checklist de verificación (cimientos)

1. `docker compose ps` — `mongo`, `redis` y `backend` en estado healthy (o running con health ok).
2. `GET /health` → `{"status":"ok"}` (o equivalente 200).
3. `GET /health/ready` → mongo y redis ok.
4. Login Google en el front → `POST /api/v1/auth/google` ok.
5. Tras login (o F5 con cookie): `GET /api/v1/auth/me` devuelve identidad, roles y estado.

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
| [docs/verification-cimientos.md](docs/verification-cimientos.md) | Checklist health + auth + `/auth/me` |
| [docs/fase-2-reparto.md](docs/fase-2-reparto.md) | Dueños Fase 2 (Aymen / Adrian) |
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

1. **Fase 2** según [docs/fase-2-reparto.md](docs/fase-2-reparto.md) (Aymen: Anuncios/Tickets/FEM/Dashboard UI; Adrian: roles/retrasos/emplazamiento; auditoría runtime ya arrancada).
2. Fase 3 (rama `Adrian-guardias-ausencias`): guardias, ausencias, justificante, PDF y firma.
3. Runtime de notificaciones sobre la norma `{detail}`.
