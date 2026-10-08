/**
 * Cliente HTTP hacia la API.
 * - Access JWT en memoria del módulo (no localStorage; reduce riesgo XSS).
 * - Refresh en cookie HttpOnly (credentials: 'include').
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/** Access token solo en RAM; se pierde al recargar y se recupera con refresh. */
let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

type ApiOptions = RequestInit & { skipAuth?: boolean }

/** Renueva el access usando la cookie HttpOnly de refresh. */
async function tryRefresh(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) {
    setAccessToken(null)
    return false
  }
  const data = (await res.json()) as { access_token: string }
  setAccessToken(data.access_token)
  return true
}

/**
 * Arranque de sesión tras F5: intenta recuperar access vía cookie refresh.
 * Devuelve true si hay access listo en memoria.
 */
export async function bootstrapSession(): Promise<boolean> {
  if (getAccessToken()) return true
  return tryRefresh()
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!options.skipAuth) {
    const token = getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  // Si el access caducó, intenta renovar una vez con la cookie refresh.
  if (res.status === 401 && !options.skipAuth) {
    const ok = await tryRefresh()
    if (ok) {
      const token = getAccessToken()
      if (token) headers.set('Authorization', `Bearer ${token}`)
      res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        credentials: 'include',
      })
    }
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const err = (await res.json()) as { detail?: unknown }
      if (err.detail) {
        detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export type UsuarioMe = {
  id: string
  name: string
  email: string
  departamento: string
  roles: string[]
  estado: string
}

export type Horario = {
  usuario_id: string
  dias: Record<string, Array<{ inicio: string; fin: string; tipo: string; asignatura?: string }>>
}

export async function loginWithGoogleIdToken(idToken: string): Promise<void> {
  const data = await apiFetch<{ access_token: string }>('/api/v1/auth/google', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken }),
    skipAuth: true,
  })
  setAccessToken(data.access_token)
}

export async function fetchMe(): Promise<UsuarioMe> {
  return apiFetch<UsuarioMe>('/api/v1/auth/me')
}

export async function fetchMiHorario(): Promise<Horario> {
  return apiFetch<Horario>('/api/v1/usuarios/me/horario')
}

export async function logout(): Promise<void> {
  try {
    await apiFetch('/api/v1/auth/logout', { method: 'POST' })
  } finally {
    setAccessToken(null)
  }
}
