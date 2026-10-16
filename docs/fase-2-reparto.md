# Fase 2 — reparto equitativo (Intranet)

Acuerdo operativo entre **Adrian** y **Aymen**. Misma carga funcional, no mismo número de líneas. Un feature = una rama corta / un PR (dueño + revisor).

## Cimientos (cerrados antes de Fase 2)

| Pieza | Estado |
|-------|--------|
| Docker Compose (Mongo + Redis + API + healthchecks) | Hecho |
| Health + Auth Google/JWT + `GET /auth/me` | Hecho (API + front) |
| CRUD Usuarios (API) | Hecho (Adrian) |
| UI Usuarios (admin) | Hecho (vertical mínima en PWA) |

## Dueños por bloque

| Bloque | Dueño | Revisor | Entregable mínimo |
|--------|-------|---------|-------------------|
| Tablón de anuncios (API + UI) | Aymen | Adrian | Feed, caducidad, fijar destacado |
| Tickets genéricos (RMI + compras + RRSS/IA) | Aymen | Adrian | Una entidad; IA solo genera borrador de texto |
| FEM (listado + horas + mapa Leaflet) | Aymen | Adrian | Prefijo `/api/v1/fem`; progreso respecto a 500 h |
| Dashboard KPIs (esqueleto + datos disponibles) | Aymen | Adrian | Solo KPIs alimentables; umbral retrasos cuando exista API |
| PWA shell (layout desktop/móvil) + onboarding | Aymen | Adrian | Visual Aymen; Adrian debe poder explicar HTML/CSS |
| Roles/permisos capa completa + auditoría mínima | Adrian | Aymen | Matriz real; `GET /api/v1/auditoria` + registro login/CRUD usuarios (arranque hecho) |
| Retrasos (alta + histórico; sin stats al docente) | Adrian | Aymen | Stats solo vía Dashboard |
| Emplazamiento en aula | Adrian | Aymen | Diseños configurables + asociación a clase |
| Docker / CI básica / hardening `.env` | Adrian | Aymen | Continuación de infra |

## Flujo Git por feature

1. Dueño: `feature/<nombre>` → implementa → commits principales (mensajes en español).
2. Revisor: no toca los mismos ficheros a la vez; aporta tests, examples OpenAPI, docs o la otra capa.
3. Antes de merge: el revisor explica el diff (voz / Discord).
4. Rotad dueño/revisor entre sprints cuando un bloque lo permita.

## Fuera de Fase 2 (no abrir aún)

- Guardias (regla de rondas), ausencias + firma PDF, aula de convivencia
- Comisiones de servicio, notificaciones push/email completas
- RGPD profundo, Google Calendar, AutoFirma (Fase 3/4)

## Orden sugerido de arranque

1. **Aymen:** Anuncios (primer módulo visible post-cimientos).
2. **Adrian:** Roles/auditoría mínima (base para el resto) en paralelo.
3. Alternar Tickets ↔ Retrasos / Emplazamiento según carga.
4. FEM + Dashboard cuando haya datos suficientes.
5. PWA shell cuando haya 2–3 pantallas reales que navegar.
