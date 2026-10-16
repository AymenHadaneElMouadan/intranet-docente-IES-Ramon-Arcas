import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  createUsuario,
  listUsuarios,
  patchUsuario,
  type UsuarioCreatePayload,
  type UsuarioPublic,
} from '../services/api'

const ROLES = [
  'admin',
  'directiva',
  'jefatura',
  'docente',
  'tutor',
  'responsable_ticket',
] as const

type Props = {
  /** Se muestra solo si el usuario actual es admin activo (lo decide el padre). */
  enabled: boolean
}

/**
 * UI mínima de administración de usuarios (CRUD vertical).
 * Listado paginado, alta manual y cambio de estado/roles (API ya existente).
 */
export function UsuariosAdmin({ enabled }: Props) {
  const [items, setItems] = useState<UsuarioPublic[]>([])
  const [page, setPage] = useState(1)
  const [limit] = useState(10)
  const [total, setTotal] = useState(0)
  const [departamento, setDepartamento] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [form, setForm] = useState<UsuarioCreatePayload>({
    name: '',
    email: '',
    departamento: '',
    roles: ['docente'],
    estado: 'activo',
  })

  const load = useCallback(async () => {
    if (!enabled) return
    setLoading(true)
    setError(null)
    try {
      const data = await listUsuarios({
        page,
        limit,
        departamento: departamento.trim() || undefined,
      })
      setItems(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al listar usuarios')
      setItems([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [enabled, page, limit, departamento])

  useEffect(() => {
    void load()
  }, [load])

  if (!enabled) return null

  const totalPages = Math.max(1, Math.ceil(total / limit))

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await createUsuario(form)
      setMessage('Usuario creado.')
      setForm({
        name: '',
        email: '',
        departamento: '',
        roles: ['docente'],
        estado: 'activo',
      })
      setPage(1)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear')
    }
  }

  const onApprove = async (id: string) => {
    setError(null)
    setMessage(null)
    try {
      await patchUsuario(id, { estado: 'activo' })
      setMessage('Usuario aprobado (activo).')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al aprobar')
    }
  }

  const onToggleRole = (role: string) => {
    setForm((prev) => {
      const has = prev.roles.includes(role)
      const roles = has ? prev.roles.filter((r) => r !== role) : [...prev.roles, role]
      return { ...prev, roles: roles.length ? roles : ['docente'] }
    })
  }

  return (
    <section className="card">
      <h2>Usuarios (admin)</h2>
      <p className="muted">Listado, alta manual y aprobación de cuentas pendientes.</p>

      <div className="toolbar">
        <label>
          Departamento
          <input
            type="text"
            value={departamento}
            onChange={(e) => {
              setPage(1)
              setDepartamento(e.target.value)
            }}
            placeholder="Filtrar…"
          />
        </label>
        <button type="button" onClick={() => void load()} disabled={loading}>
          Actualizar
        </button>
      </div>

      {loading && <p>Cargando usuarios…</p>}
      {error && <p className="error">{error}</p>}
      {message && <p className="ok">{message}</p>}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Depto.</th>
              <th>Estado</th>
              <th>Roles</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.departamento || '—'}</td>
                <td>{u.estado}</td>
                <td>{u.roles.join(', ')}</td>
                <td>
                  {u.estado === 'pendiente' && (
                    <button type="button" onClick={() => void onApprove(u.id)}>
                      Aprobar
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  Sin usuarios en esta página.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pager">
        <button
          type="button"
          disabled={page <= 1 || loading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Anterior
        </button>
        <span>
          Página {page} / {totalPages} ({total} total)
        </span>
        <button
          type="button"
          disabled={page >= totalPages || loading}
          onClick={() => setPage((p) => p + 1)}
        >
          Siguiente
        </button>
      </div>

      <h3>Alta manual</h3>
      <form className="usuario-form" onSubmit={(e) => void onCreate(e)}>
        <label>
          Nombre
          <input
            required
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
        </label>
        <label>
          Email
          <input
            required
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          />
        </label>
        <label>
          Departamento
          <input
            required
            value={form.departamento}
            onChange={(e) => setForm((f) => ({ ...f, departamento: e.target.value }))}
          />
        </label>
        <fieldset>
          <legend>Roles</legend>
          <div className="role-grid">
            {ROLES.map((role) => (
              <label key={role} className="role-check">
                <input
                  type="checkbox"
                  checked={form.roles.includes(role)}
                  onChange={() => onToggleRole(role)}
                />
                {role}
              </label>
            ))}
          </div>
        </fieldset>
        <label>
          Estado
          <select
            value={form.estado}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                estado: e.target.value as UsuarioCreatePayload['estado'],
              }))
            }
          >
            <option value="activo">activo</option>
            <option value="pendiente">pendiente</option>
            <option value="inactivo">inactivo</option>
          </select>
        </label>
        <button type="submit">Crear usuario</button>
      </form>
    </section>
  )
}
