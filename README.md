# Intranet Docente — IES Ramón Arcas Meca

PWA de gestión interna para profesorado y equipo directivo. Forma parte del Proyecto Intermodular de 2º DAW y es **independiente** de la Web Pública del centro (otro repositorio, otra BD, otra sesión).

## Estado actual

Estructura base del repositorio:

- Contrato API OpenAPI 3.x (`openapi/openapi.yaml`)
- Documentación canónica (`docs/`)
- Reglas Cursor (`AGENTS.md`, `.cursor/rules/`)
- Esqueleto de carpetas `frontend/` y `backend/`
- Stub de `docker-compose.yml`

**Aún no** hay lógica de negocio ni UI implementada.

## Ver el contrato en Swagger Editor

1. Abre [https://editor.swagger.io](https://editor.swagger.io)
2. File → Import file (o pega el contenido de `openapi/openapi.yaml`)
3. Revisa los tags (grupos): Auth, Usuarios, Anuncios, Guardias, Ausencias, Tickets, FEM, Dashboard, Health

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [AGENTS.md](AGENTS.md) | Contexto permanente para agentes / Cursor |
| [docs/architecture.md](docs/architecture.md) | Stack y capas |
| [docs/api-contract.md](docs/api-contract.md) | Tabla oficial de endpoints |
| [docs/roles-and-permissions.md](docs/roles-and-permissions.md) | Roles y permisos |
| [openapi/openapi.yaml](openapi/openapi.yaml) | Contrato OpenAPI (fuente Swagger) |

## Estructura prevista

```
intranet-docente-ies/
├── frontend/          # React + Vite + TypeScript (PWA)
├── backend/           # FastAPI
│   ├── app/
│   └── tests/
├── openapi/
├── docs/
└── docker-compose.yml # MongoDB, Redis, backend
```

## Próximos pasos (fuera de este commit)

1. Scaffold ejecutable: FastAPI con `/health` + Vite app vacía.
2. Auth Google + JWT + Redis para refresh tokens.
3. Implementar endpoints por grupos según el contrato OpenAPI.
