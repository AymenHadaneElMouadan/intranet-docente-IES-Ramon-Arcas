# Roles y permisos

## Roles oficiales

Un usuario puede tener **uno o varios** roles.

| Rol | Descripción |
|-----|-------------|
| `admin` | Gestión completa del sistema: usuarios, configuración, administración |
| `directiva` | Anuncios, dashboard KPIs, visión directiva |
| `jefatura` | Asignación y modificación de guardias |
| `docente` | Uso cotidiano: anuncios, ausencias, tickets, información propia |
| `tutor` | Alumnado FEM asignado al docente |
| `responsable_ticket` | Gestión de tickets que tiene asignados |

**No inventar nombres de roles distintos** a los de esta lista.

## Propiedad (no es rol)

Algunas comprobaciones son de **propiedad**, no de rol:

| Regla | Significado |
|-------|-------------|
| Dueño de ausencia | El usuario autenticado es el titular de esa ausencia (`/ausencias/{id}/…`) |
| Asignado a ticket | El usuario es el responsable asignado del ticket |

Ejemplo: `GET /ausencias/{id}/pdf` requiere autenticación **y** ser el dueño (o un rol con privilegio explícito si se define después).

## Matriz resumida (rol × capacidad)

| Capacidad | admin | directiva | jefatura | docente | tutor | responsable_ticket |
|-----------|:-----:|:---------:|:--------:|:-------:|:-----:|:------------------:|
| Listar / gestionar usuarios | sí | — | — | — | — | — |
| Ver / publicar anuncios | sí | sí | leer | leer; publicar según política | leer | leer |
| Fijar anuncios | sí | — | — | — | — | — |
| Consultar guardias | sí | sí | sí | sí | sí | sí |
| Asignar / modificar guardias | sí | — | sí | — | — | — |
| Registrar ausencias propias | sí | sí | sí | sí | sí | sí |
| Justificante / PDF / firma (propias) | sí* | sí* | sí* | sí* | sí* | sí* |
| Crear / ver tickets | sí | sí | sí | sí | sí | sí |
| Transicionar estado de ticket | sí | — | — | — | — | sí (asignados) |
| Comentarios en ticket | sí | — | — | sí (propios) | — | sí |
| FEM alumnos / horas | sí | — | — | — | sí | — |
| Dashboard KPIs | sí | sí | — | — | — | — |
| `GET /auth/me` | sí | sí | sí | sí | sí | sí |

\* Sobre recursos de los que es dueño, salvo que un rol superior tenga permiso administrativo explícito (por definir al implementar).

## Convención en el contrato API

En tablas y OpenAPI:

- `Auth` = cualquier usuario autenticado con JWT válido.
- Roles concretos = además del JWT, el backend comprueba el rol (o la propiedad).

## Autorización

- Nunca autorizar solo con datos enviados por el cliente.
- Identidad y roles se obtienen del contexto de autenticación (JWT / sesión Redis asociado).
- Transiciones de tickets inválidas deben rechazarse en servicio de dominio (no aceptar estados inventados).
