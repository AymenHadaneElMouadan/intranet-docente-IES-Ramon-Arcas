# Contrato API — Intranet Docente

Fuente canónica machine-readable: [openapi/openapi.yaml](../openapi/openapi.yaml).

Prefijo funcional: **`/api/v1`**.  
Health: sin prefijo de versión (`/health`, `/health/ready`).

Autenticación por defecto: header `Authorization: Bearer <access_token>`, salvo endpoints marcados como públicos o refresh.

## Convenciones de respuesta

| Caso | Formato |
|------|---------|
| Listados / detalle OK | Recurso JSON (objeto o array) |
| Mutación OK | `{ "code": 200\|201, "msg": "...", "data"?: ... }` |
| Error | `{ "code": <http>, "msg": "...", "details"?: ... }` |

Códigos habituales: `200`, `201`, `400`, `401`, `403`, `404`, `422`.

## Auth

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| POST | `/api/v1/auth/google` | Público | — | OAuth Google → access + refresh JWT |
| POST | `/api/v1/auth/refresh` | Refresh token | — | Renovar access token |
| POST | `/api/v1/auth/logout` | Auth | — | Invalidar refresh / sesión |
| GET | `/api/v1/auth/me` | Auth | — | Usuario autenticado y roles |

## Usuarios

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/usuarios` | Auth | `admin` | Listado del claustro (`?departamento=`) |
| GET | `/api/v1/usuarios/me` | Auth | — | Perfil del usuario autenticado |
| GET | `/api/v1/usuarios/me/horario` | Auth | — | Horario semanal propio |
| GET | `/api/v1/usuarios/{id}/horario` | Auth | admin / consulta autorizada | Horario de un docente |
| PATCH | `/api/v1/usuarios/{id}` | Auth | `admin` | Modificación parcial (ej. aprobar alta) |

## Anuncios

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/anuncios` | Auth | — | Feed segmentado por departamento |
| POST | `/api/v1/anuncios` | Auth | `admin`, `directiva` | Publicar (opción de expiración) |
| PATCH | `/api/v1/anuncios/{id}/fijar` | Auth | `admin` | Fijar / desfijar |

## Guardias

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/guardias` | Auth | — | Cuadrante (`?fecha=&franja=`) |
| POST | `/api/v1/guardias/asignar` | Auth | `jefatura` | Ejecutar algoritmo de asignación por rondas |
| PATCH | `/api/v1/guardias/{id}` | Auth | `jefatura` | Cambiar docente que cubre el hueco |

## Ausencias

| Método | Endpoint | Auth | Roles / propiedad | Descripción |
|--------|----------|------|-------------------|-------------|
| POST | `/api/v1/ausencias` | Auth | — | Registro (genérica, administrativa, extraescolar) |
| POST | `/api/v1/ausencias/{id}/justificante` | Auth | dueño | Subida de justificante |
| GET | `/api/v1/ausencias/{id}/pdf` | Auth | dueño | PDF autocompletado |
| POST | `/api/v1/ausencias/{id}/firma` | Auth | dueño | Firma manuscrita / electrónica |

## Tickets

| Método | Endpoint | Auth | Roles / propiedad | Descripción |
|--------|----------|------|-------------------|-------------|
| GET | `/api/v1/tickets` | Auth | — | Listado (`?tipo=&estado=`) |
| POST | `/api/v1/tickets` | Auth | — | Creación unificada (RMI, RRSS, Compras, …) |
| PATCH | `/api/v1/tickets/{id}` | Auth | `responsable_ticket` / `admin` | Transición de estado |
| GET | `/api/v1/tickets/{id}/comentarios` | Auth | involucrados | Hilo de comentarios |
| POST | `/api/v1/tickets/{id}/comentarios` | Auth | involucrados | Nuevo comentario |

### Máquina de estados de tickets

```
abierto → en_proceso → resuelto → cerrado
```

- Solo se aceptan transiciones válidas.
- Estados desconocidos → `422`.
- El servicio de dominio rechaza saltos ilegales.

## FEM (Formación en Empresas Murcia)

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/fem/alumnos` | Auth | `tutor` | Alumnado asignado (`?estado=`) |
| PATCH | `/api/v1/fem/alumnos/{id}/horas` | Auth | `tutor` | Actualizar horas cursadas (sobre 500) |

## Dashboard

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/dashboard/kpis` | Auth | `directiva`, `admin` | Métricas consolidadas del centro |

## Health

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/health` | Público | Liveness |
| GET | `/health/ready` | Público | Readiness (Mongo, Redis) |

## PENDIENTE DE DECISIÓN

- Cuerpo exacto de `POST /auth/google` (credential / id_token) y whitelist de dominio.
- Dónde viaja el refresh token (body vs cookie HttpOnly).
- Detalle del algoritmo de guardias por rondas.
- Campos definitivos de cada recurso al implementar (pueden refinarse en OpenAPI sin romper el path).
