# AGENTS.md — Intranet Docente IES Ramón Arcas Meca

## 1. Identidad del proyecto

Este repositorio es la **Intranet de Gestión Docente** del Proyecto Intermodular de 2º DAW (IES Ramón Arcas Meca).

Existen **dos sistemas independientes**. Este repo es solo la intranet. La Web Pública es otro repositorio.

**IMPORTANTE:**

- No compartir base de datos con la Web Pública.
- No compartir sesiones ni autenticación con la Web Pública.
- No asumir APIs, usuarios, tablas o modelos del otro sistema.
- No introducir dependencias arquitectónicas entre ambos sistemas sin aprobación explícita.

## 2. Fuente de verdad

Antes de modificar arquitectura, API, autenticación, persistencia o estructura de directorios:

1. Revisar [docs/architecture.md](docs/architecture.md).
2. Revisar [docs/api-contract.md](docs/api-contract.md) y [openapi/openapi.yaml](openapi/openapi.yaml) si el cambio afecta a endpoints.
3. Revisar [docs/roles-and-permissions.md](docs/roles-and-permissions.md) si el cambio afecta a autorización.

Si una petición entra en conflicto con estas decisiones, **no modificar silenciosamente** la arquitectura: explicar el conflicto y proponer el cambio.

La documentación del repositorio es la fuente de verdad. Las decisiones no deben depender de memoria conversacional.

## 3. Stack (fijo)

- Backend: Python, FastAPI (>=0.110), Uvicorn, PyJWT, python-multipart, python-dotenv, Pytest, Httpx.
- Persistencia: MongoDB (principal), Redis (caché / refresh tokens / colas).
- Frontend PWA: React + Vite + TypeScript.
- Autenticación: OAuth Google → JWT Bearer (`Depends()` en FastAPI).

No proponer stacks alternativos. No inventar requisitos.

## 4. API

- Versionado: `/api/v1`.
- Recursos en plural, nombres completos (sin abreviaturas: `justificante`, `comentarios`).
- Prefijo FEM: `/api/v1/fem` (Formación en Empresas Murcia). No renombrar a `/fct`.
- Routers finos; lógica de negocio en `services/`.
- Contrato canónico en OpenAPI: `openapi/openapi.yaml`.

## 5. Roles

Roles oficiales (ver matriz completa en docs):

`admin` | `directiva` | `jefatura` | `docente` | `tutor` | `responsable_ticket`

La propiedad de un recurso (dueño de una ausencia, asignado a un ticket) **no es un rol**.

## 6. Forma de trabajar

- Corrección, seguridad, claridad, mantenibilidad, simplicidad.
- No añadir frameworks o patrones no definidos en la arquitectura sin justificarlos.
- Al cambiar un endpoint: actualizar OpenAPI, `docs/api-contract.md`, esquemas y tests afectados.
- Marcar dudas reales como **PENDIENTE DE DECISIÓN** en la documentación; no inventar.
