import { useCallback, useEffect, useState } from 'react'
import { GoogleLoginButton } from './components/GoogleLoginButton'
import { HomePage } from './pages/HomePage'
import { PendingPage } from './pages/PendingPage'
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
              <code>localhost:5173</code> o abre la app en Chrome/Edge del sistema (no en el
              preview embebido del editor).
            </p>
          </section>
        )}

        {!loading && user?.estado === 'pendiente' && (
          <PendingPage user={user} onLogout={() => void onLogout()} />
        )}

        {!loading && user?.estado === 'activo' && (
          <HomePage user={user} horario={horario} onLogout={() => void onLogout()} />
        )}

        {!loading && user && user.estado !== 'pendiente' && user.estado !== 'activo' && (
          <section className="card">
            <div className="row">
              <h2>Estado de cuenta</h2>
              <button type="button" onClick={() => void onLogout()}>
                Cerrar sesión
              </button>
            </div>
            <p>
              Tu cuenta tiene el estado <code>{user.estado}</code>, que no permite usar la
              intranet ahora mismo. Contacta con un administrador.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
