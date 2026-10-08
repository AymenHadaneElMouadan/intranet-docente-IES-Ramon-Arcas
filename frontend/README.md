# Frontend (React + Vite + TypeScript)

PWA mínima de la Intranet Docente: login Google, perfil vía `auth/me` y horario propio.

## Desarrollo

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Variables:

- `VITE_API_BASE_URL` — base del backend (default `http://localhost:8000`)
- `VITE_GOOGLE_CLIENT_ID` — mismo Client ID OAuth que `GOOGLE_CLIENT_ID` del backend

Tras cambiar el `.env`, reinicia Vite. Usa Chrome/Edge del sistema; el preview embebido suele bloquear el popup de Google. El botón GIS usa FedCM cuando el navegador lo permite.

## Sesión

- Access JWT solo en memoria del módulo (`services/api.ts`); no se guarda en `localStorage`.
- Refresh en cookie HttpOnly; al recargar se recupera con `POST /auth/refresh`.
- Arranque: refresh → `GET /auth/me`. El horario (`/usuarios/me/horario`) solo se pide si `estado === activo`.
- Cuentas `pendiente`: ven el perfil y el aviso de espera de admin; no hay UI de administración (la aprobación es por API).

## Estructura

```
src/
├── components/   # UI (botón Google GIS, …)
├── services/     # Cliente HTTP /api/v1
└── App.tsx       # Login + perfil + horario
```
