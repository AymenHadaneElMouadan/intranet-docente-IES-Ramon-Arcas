# Contrato API — Intranet Docente

Fuente canónica machine-readable: [openapi/openapi.yaml](../openapi/openapi.yaml).

Prefijo funcional: **`/api/v1`**.  
Health: sin prefijo de versión (`/health`, `/health/ready`).

Autenticación por defecto: header `Authorization: Bearer <access_token>`, salvo endpoints públicos y refresh (cookie).

## Convenciones de respuesta (norma del repo)

Alineadas a los apuntes del profesorado (FastAPI + diseño REST):

| Caso | Formato |
|------|--------|
| Error | `{"detail": "..."}` o lista de errores de validación 422 |
| Listados | `{ "items": [...], "page": 1, "limit": 10, "total": N }` |
| Detalle / recurso | Objeto JSON del recurso |
| POST creado | `201` + cuerpo del recurso + cabecera `Location: /api/v1/.../{id}` |
| Mutación OK | Recurso actualizado (sin wrapper `{code, msg}`) |

Códigos habituales: `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `503`.

Paginación: `page` (default 1), `limit` (default 10, máx. 50).

Identificadores: `string` (ObjectId de MongoDB en hex). El cliente **nunca** envía el `id` en el alta; lo asigna el servidor.

## Auth

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| POST | `/api/v1/auth/google` | Público | — | Body `{ "id_token" }` → access JWT + cookie HttpOnly refresh |
| POST | `/api/v1/auth/refresh` | Cookie refresh | — | Renueva access; no usa Bearer |
| POST | `/api/v1/auth/logout` | Auth | — | Invalida refresh en Redis y borra cookie |
| GET | `/api/v1/auth/me` | Auth | — | Usuario autenticado, roles y estado |

- Access token: header Bearer.
- Refresh token: cookie HttpOnly `refresh_token` (path `/api/v1/auth`), almacenada en Redis.
- Sin restricción de dominio Google. Alta OAuth deja al usuario en estado `pendiente` hasta aprobación admin.

## Usuarios

| Método | Endpoint | Auth | Roles / regla | Descripción |
|--------|----------|------|---------------|-------------|
| GET | `/api/v1/usuarios` | Auth | `admin` | Listado paginado (`?departamento=&estado=&rol=&page=&limit=`) |
| POST | `/api/v1/usuarios` | Auth | `admin` | Alta manual; `201` + `Location` |
| GET | `/api/v1/usuarios/me` | Auth | — | Perfil propio |
| PATCH | `/api/v1/usuarios/me` | Auth | — | Rectificar datos propios (RGPD) |
| GET | `/api/v1/usuarios/me/datos` | Auth | — | Exportar datos personales propios (RGPD) |
| GET | `/api/v1/usuarios/me/horario` | Auth | — | Horario semanal propio |
| GET | `/api/v1/usuarios/{id}` | Auth | `admin` o propio | Detalle |
| GET | `/api/v1/usuarios/{id}/horario` | Auth | `admin` o propio | Horario de un docente |
| PATCH | `/api/v1/usuarios/{id}` | Auth | `admin` | Parcial (aprobar, roles, departamento…) |
| PUT | `/api/v1/usuarios/{id}/roles` | Auth | `admin` | Sustituir lista de roles; `409` si se elimina el último admin |

## Anuncios

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/anuncios` | Auth | — | Feed segmentado por departamento |
| POST | `/api/v1/anuncios` | Auth | `admin`, `directiva` | Publicar; `201` + `Location` |
| PATCH | `/api/v1/anuncios/{id}/fijar` | Auth | `admin` | Fijar / desfijar |

## Guardias

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/guardias` | Auth | — | Cuadrante (`?fecha=&franja=`) |
| POST | `/api/v1/guardias/asignar` | Auth | `jefatura` | Algoritmo de asignación por rondas |
| PATCH | `/api/v1/guardias/{id}` | Auth | `jefatura` | Cambiar docente que cubre el hueco |

## Ausencias

| Método | Endpoint | Auth | Roles / propiedad | Descripción |
|--------|----------|------|-------------------|-------------|
| POST | `/api/v1/ausencias` | Auth | — | Registro; `201` + `Location` |
| POST | `/api/v1/ausencias/{id}/justificante` | Auth | dueño | Subida de justificante |
| GET | `/api/v1/ausencias/{id}/pdf` | Auth | dueño | PDF autocompletado |
| POST | `/api/v1/ausencias/{id}/firma` | Auth | dueño | Firma manuscrita / electrónica |

## Tickets

| Método | Endpoint | Auth | Roles / propiedad | Descripción |
|--------|----------|------|-------------------|-------------|
| GET | `/api/v1/tickets` | Auth | — | Listado (`?tipo=&estado=`) |
| POST | `/api/v1/tickets` | Auth | — | Creación; `201` + `Location` |
| PATCH | `/api/v1/tickets/{id}` | Auth | `responsable_ticket` / `admin` | Transición de estado |
| GET | `/api/v1/tickets/{id}/comentarios` | Auth | involucrados | Hilo de comentarios |
| POST | `/api/v1/tickets/{id}/comentarios` | Auth | involucrados | Nuevo comentario; `201` + `Location` |

### Máquina de estados de tickets

```
abierto → en_proceso → resuelto → cerrado
```

- Solo se aceptan transiciones válidas.
- Transición inválida → `422` con `{"detail": "..."}`.

## FEM (Formación en Empresas Murcia)

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/fem/alumnos` | Auth | `tutor`, `admin` | Alumnado asignado |
| PATCH | `/api/v1/fem/alumnos/{id}/horas` | Auth | `tutor`, `admin` | Actualizar horas cursadas |

## Dashboard

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/dashboard/kpis` | Auth | `directiva`, `admin` | Indicadores del centro |

## Retrasos

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| POST | `/api/v1/retrasos` | Auth | `docente`, `admin` | Registrar retraso; `201` + `Location` |
| GET | `/api/v1/retrasos/{id}` | Auth | `docente`, `admin` | Detalle |
| GET | `/api/v1/alumnos/{id}/retrasos` | Auth | `docente`, `admin` | Histórico paginado (`?curso_escolar=&page=&limit=`) |

## Notificaciones

| Método | Endpoint | Auth | Roles / regla | Descripción |
|--------|----------|------|---------------|-------------|
| GET | `/api/v1/notificaciones` | Auth | solo propias | Bandeja paginada (`?leida=&page=&limit=`) + `no_leidas` |
| PATCH | `/api/v1/notificaciones/{id}` | Auth | destinatario | Marcar leída / no leída |
| POST | `/api/v1/notificaciones/suscripciones` | Auth | — | Registrar Web Push (`201` o `200` si ya existía) |
| DELETE | `/api/v1/notificaciones/suscripciones/{id}` | Auth | dueño | Eliminar suscripción (`204`) |

Las notificaciones **no se crean desde la API**: las generan los servicios ante eventos de negocio.

## Auditoría

| Método | Endpoint | Auth | Roles | Descripción |
|--------|----------|------|-------|-------------|
| GET | `/api/v1/auditoria` | Auth | `admin`, `directiva` | Registro paginado (solo lectura) |

## Health

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/health` | Público | Liveness (proceso vivo) |
| GET | `/health/ready` | Público | Readiness (Mongo, Redis) |

## Decisiones cerradas

- `POST /auth/google`: body `{ "id_token": "..." }`; sin whitelist de dominio.
- Refresh token: cookie HttpOnly (no body JSON).
- Errores y listados: norma FastAPI / apuntes del profesorado (arriba).

## Pendiente de decisión (módulos posteriores)

- Detalle del algoritmo de guardias por rondas.
- Formato exacto del payload de firma PDF.
- Librerías concretas de PDF, email y Web Push.
- Campos de `UsuarioMePatch` para autocompletar PDF sin OAuth.
- Si el autor puede corregir o borrar un retraso mal registrado, y en qué plazo.
- Preferencias de canal de notificación y plazo de conservación de notificaciones/auditoría.
- Fuente canónica de alumnado (`alumno_id`) compartida con FEM/retrasos.
