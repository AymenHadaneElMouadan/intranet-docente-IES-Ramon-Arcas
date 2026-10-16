# Checklist de verificación — cimientos

Ejecutar tras `docker compose up --build` (y front con `npm run dev` si se prueba el login).

| # | Comprobación | Resultado esperado |
|---|--------------|--------------------|
| 1 | `docker compose ps` | `mongo`, `redis`, `backend` healthy / up |
| 2 | `GET http://localhost:8000/health` | 200, `{"status":"ok"}` |
| 3 | `GET http://localhost:8000/health/ready` | 200, `mongo` y `redis` true |
| 4 | Front: botón Google con `VITE_GOOGLE_CLIENT_ID` = `GOOGLE_CLIENT_ID` | Login sin error 503 |
| 5 | Tras login: perfil en UI | Datos de `GET /api/v1/auth/me` |
| 6 | Recarga (F5) | Sesión recuperada vía cookie refresh → `/auth/me` |
| 7 | Logout | Cookie invalidada; vuelve a pantalla de acceso |
| 8 | Cuenta `pendiente` | Ve perfil; no horario ni listado admin de usuarios |
| 9 | Cuenta `activo` + rol `admin` | Puede abrir listado de usuarios (UI admin) |

Endpoints de referencia: [`backend/app/api/health.py`](../backend/app/api/health.py), [`backend/app/api/auth.py`](../backend/app/api/auth.py).

Si Docker no está instalado en la máquina, usar arranque local del backend (`backend/README.md`) con Mongo/Redis en Compose o nativos, y aplicar las filas 2–9 igual.
