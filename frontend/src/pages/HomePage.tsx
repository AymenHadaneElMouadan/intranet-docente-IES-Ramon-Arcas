import type { Horario, UsuarioMe } from '../services/api'

type Props = {
  user: UsuarioMe
  horario: Horario | null
  onLogout: () => void
}

/** Home mínimo de Fase 1: identidad, roles y horario de prueba. */
export function HomePage({ user, horario, onLogout }: Props) {
  return (
    <>
      <section className="card">
        <div className="row">
          <h2>Inicio</h2>
          <button type="button" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
        <p className="lead">
          Sesión activa. Este es el núcleo mínimo de la intranet (auth + roles).
        </p>
        <dl className="profile">
          <dt>Nombre</dt>
          <dd>{user.name}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
          <dt>Estado</dt>
          <dd>
            <span className="badge badge-activo">{user.estado}</span>
          </dd>
          <dt>Roles</dt>
          <dd>
            <ul className="roles-list">
              {user.roles.map((rol) => (
                <li key={rol}>
                  <span className="badge badge-rol">{rol}</span>
                </li>
              ))}
            </ul>
          </dd>
          <dt>Departamento</dt>
          <dd>{user.departamento || '—'}</dd>
        </dl>
        <p className="hint modules-placeholder">
          El tablón de anuncios está más abajo en esta misma página. Tickets, FEM y el resto
          de módulos de Fase 2 se irán añadiendo después.
        </p>
      </section>

      <section className="card">
        <h2>Mi horario</h2>
        <p className="hint">Prueba de que la API responde para un usuario activo.</p>
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
    </>
  )
}
