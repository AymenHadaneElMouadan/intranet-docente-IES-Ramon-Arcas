# Frontend (React + Vite + TypeScript)

PWA mínima de la Intranet Docente. Arranque: `auth/me` + `usuarios/me/horario`.

## Desarrollo

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Variables:

- `VITE_API_BASE_URL` — base del backend (default `http://localhost:8000`)
- `VITE_GOOGLE_CLIENT_ID` — Client ID de Google Identity Services

## Estructura

```
src/
├── components/   # UI (botón Google, …)
├── services/     # Cliente HTTP /api/v1
└── App.tsx       # Login + perfil + horario
```
