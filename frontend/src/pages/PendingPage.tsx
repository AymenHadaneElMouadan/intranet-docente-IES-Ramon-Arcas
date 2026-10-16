import type { UsuarioMe } from '../services/api'

type Props = {
  user: UsuarioMe
  onLogout: () => void
}

/** Cuenta autenticada pero aún no aprobada por un admin. */
export function PendingPage({ user, onLogout }: Props) {
  return (
    <section className="card card-pending">
      <div className="row">
        <h2>Alta pendiente</h2>
        <button type="button" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
      <p>
        Hola, <strong>{user.name}</strong>. Tu cuenta (<code>{user.email}</code>) está
        registrada, pero un administrador debe confirmarla antes de usar el resto de la
        intranet.
      </p>
      <dl className="profile">
        <dt>Estado</dt>
        <dd>
          <span className="badge badge-pendiente">{user.estado}</span>
        </dd>
        <dt>Roles provisionales</dt>
        <dd>{user.roles.length ? user.roles.join(', ') : '—'}</dd>
        <dt>Departamento</dt>
        <dd>{user.departamento || '—'}</dd>
      </dl>
      <p className="hint">
        Cuando te aprueben (estado <code>activo</code>), vuelve a entrar o recarga la página
        para ver el inicio de la intranet.
      </p>
    </section>
  )
}
