import { useCallback, useEffect, useState } from 'react'
import { GoogleLoginButton } from './components/GoogleLoginButton'
import {
  bootstrapSession,
  fetchMe,
  fetchMiHorario,
  logout,
  type Horario,
  type UsuarioMe,
} from './services/api'
import './App.css'

function App() {
  const [user, setUser] = useState<UsuarioMe | null>(null)
  const [horario, setHorario] = useState<Horario | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  /**
   * Arranque: refresh por cookie → auth/me.
   * Horario solo si la cuenta está activa (pendiente no puede llamar a /usuarios/me/horario).
   */
  const loadSession = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const ok = await bootstrapSession()
      if (!ok) {
        setUser(null)
        setHorario(null)
        return
      }
      const me = await fetchMe()
      setUser(me)
      if (me.estado === 'activo') {
        const h = await fetchMiHorario()
        setHorario(h)
      } else {
        setHorario(null)
      }
    } catch (err) {
      setUser(null)
      setHorario(null)
      setError(err instanceof Error ? err.message : 'Error de sesión')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadSession()
  }, [loadSession])

  const onLogout = async () => {
    await logout()
    setUser(null)
    setHorario(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Intranet Docente</h1>
        <p>IES Ramón Arcas Meca</p>
      </header>

      <main className="app-main">
        {loading && <p>Cargando…</p>}

        {!loading && !user && (
          <section className="card">
            <h2>Acceso</h2>
            <p>Inicia sesión con tu cuenta de Google.</p>
            <GoogleLoginButton onLoggedIn={loadSession} onError={setError} />
            {error && <p className="error">{error}</p>}
            <p className="hint">
              Si el login no abre o ves pantalla en blanco: permite ventanas emergentes para{' '}
              <code>localhost:5173</code> o abre la app en Chrome/Edge del sistema (no en el preview
              embebido del editor).
            </p>
          </section>
        )}

        {!loading && user && (
          <>
            <section className="card">
              <div className="row">
                <h2>Mi perfil</h2>
                <button type="button" onClick={() => void onLogout()}>
                  Cerrar sesión
                </button>
              </div>
              <dl className="profile">
                <dt>Nombre</dt>
                <dd>{user.name}</dd>
                <dt>Email</dt>
                <dd>{user.email}</dd>
                <dt>Estado</dt>
                <dd>{user.estado}</dd>
                <dt>Roles</dt>
                <dd>{user.roles.join(', ')}</dd>
                <dt>Departamento</dt>
                <dd>{user.departamento || '—'}</dd>
              </dl>
              {user.estado === 'pendiente' && (
                <p className="hint">
                  Tu alta está pendiente de confirmación por un administrador.
                </p>
              )}
            </section>

            {user.estado === 'activo' && (
              <section className="card">
                <h2>Mi horario</h2>
                {!horario && <p>Sin horario.</p>}
                {horario &&
                  Object.entries(horario.dias).map(([dia, bloques]) => (
                    <div key={dia} className="dia">
                      <h3>{dia}</h3>
                      {bloques.length === 0 && <p className="muted">Sin bloques</p>}
                      <ul>
                        {bloques.map((b, i) => (
                          <li key={`${dia}-${i}`}>
                            {b.inicio}–{b.fin} · {b.tipo}
                            {b.asignatura ? ` · ${b.asignatura}` : ''}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
