import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  createTicket,
  createTicketComentario,
  listTicketComentarios,
  listTickets,
  patchTicket,
  type Ticket,
  type TicketComentario,
  type TicketEstado,
  type TicketTipo,
} from '../services/api'

type Props = {
  roles: string[]
  userId: string
}

const TIPOS: TicketTipo[] = ['rmi', 'compras', 'rrss', 'otro']
const ESTADOS: TicketEstado[] = ['abierto', 'en_proceso', 'resuelto', 'cerrado']

const SIGUIENTE_ESTADO: Record<TicketEstado, TicketEstado | null> = {
  abierto: 'en_proceso',
  en_proceso: 'resuelto',
  resuelto: 'cerrado',
  cerrado: null,
}

function formatFecha(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('es-ES', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

/** Cola de tickets (RMI / compras / RRSS / otro) sobre la API existente. */
export function TicketsPage({ roles, userId }: Props) {
  const canManage = roles.includes('admin') || roles.includes('responsable_ticket')

  const [items, setItems] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [okMsg, setOkMsg] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [filtroTipo, setFiltroTipo] = useState<TicketTipo | ''>('')
  const [filtroEstado, setFiltroEstado] = useState<TicketEstado | ''>('')

  const [tipo, setTipo] = useState<TicketTipo>('rmi')
  const [titulo, setTitulo] = useState('')
  const [descripcion, setDescripcion] = useState('')

  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [comentarios, setComentarios] = useState<TicketComentario[]>([])
  const [comentariosError, setComentariosError] = useState<string | null>(null)
  const [nuevoComentario, setNuevoComentario] = useState('')
  const [loadingComentarios, setLoadingComentarios] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listTickets({
        tipo: filtroTipo || undefined,
        estado: filtroEstado || undefined,
      })
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar la cola de tickets')
    } finally {
      setLoading(false)
    }
  }, [filtroTipo, filtroEstado])

  useEffect(() => {
    void load()
  }, [load])

  const loadComentarios = async (ticketId: string) => {
    setLoadingComentarios(true)
    setComentariosError(null)
    try {
      const data = await listTicketComentarios(ticketId)
      setComentarios(data)
    } catch (err) {
      setComentarios([])
      setComentariosError(
        err instanceof Error ? err.message : 'No se pudieron cargar los comentarios',
      )
    } finally {
      setLoadingComentarios(false)
    }
  }

  const onToggleExpand = async (ticket: Ticket) => {
    if (expandedId === ticket.id) {
      setExpandedId(null)
      setComentarios([])
      setComentariosError(null)
      setNuevoComentario('')
      return
    }
    setExpandedId(ticket.id)
    setNuevoComentario('')
    await loadComentarios(ticket.id)
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setOkMsg(null)
    try {
      await createTicket({
        tipo,
        titulo: titulo.trim(),
        descripcion: descripcion.trim() || null,
      })
      setTitulo('')
      setDescripcion('')
      setTipo('rmi')
      setOkMsg('Ticket creado.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el ticket')
    } finally {
      setSaving(false)
    }
  }

  const onAvanzarEstado = async (ticket: Ticket) => {
    const siguiente = SIGUIENTE_ESTADO[ticket.estado]
    if (!siguiente) return
    setError(null)
    setOkMsg(null)
    try {
      await patchTicket(ticket.id, { estado: siguiente })
      setOkMsg(`Ticket pasado a «${siguiente}».`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cambiar el estado')
    }
  }

  const onAsignarme = async (ticket: Ticket) => {
    setError(null)
    setOkMsg(null)
    try {
      await patchTicket(ticket.id, { asignado_id: userId })
      setOkMsg('Ticket asignado.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo asignar el ticket')
    }
  }

  const onAddComentario = async (ticketId: string, e: FormEvent) => {
    e.preventDefault()
    setComentariosError(null)
    try {
      await createTicketComentario(ticketId, nuevoComentario.trim())
      setNuevoComentario('')
      await loadComentarios(ticketId)
    } catch (err) {
      setComentariosError(
        err instanceof Error ? err.message : 'No se pudo añadir el comentario',
      )
    }
  }

  const descLabel =
    tipo === 'rrss' ? 'Borrador de publicación (RRSS)' : 'Descripción (opcional)'

  return (
    <section className="card">
      <h2>Cola de tickets</h2>
      <p className="hint">
        Solicitudes RMI, compras, RRSS u otras. Estados: abierto → en_proceso → resuelto →
        cerrado. La generación automática con IA para RRSS aún no tiene endpoint; el borrador se
        escribe a mano en la descripción.
      </p>

      <div className="toolbar ticket-filters">
        <label>
          Tipo
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value as TicketTipo | '')}
          >
            <option value="">Todos</option>
            {TIPOS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value as TicketEstado | '')}
          >
            <option value="">Todos</option>
            {ESTADOS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => void load()}>
          Actualizar
        </button>
      </div>

      <form className="ticket-form" onSubmit={(e) => void onCreate(e)}>
        <h3>Nueva solicitud</h3>
        <label>
          Tipo
          <select value={tipo} onChange={(e) => setTipo(e.target.value as TicketTipo)}>
            {TIPOS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label>
          Título
          <input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            required
            minLength={1}
          />
        </label>
        <label>
          {descLabel}
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={4}
            placeholder={
              tipo === 'rrss'
                ? 'Texto borrador para redes (sin publicación automática)'
                : undefined
            }
          />
        </label>
        {tipo === 'rrss' && (
          <p className="hint">
            Por ahora el borrador RRSS es manual. Cuando exista API de IA, se podrá generar aquí.
          </p>
        )}
        <button type="submit" disabled={saving}>
          {saving ? 'Creando…' : 'Crear ticket'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {okMsg && <p className="ok">{okMsg}</p>}

      {loading && <p>Cargando tickets…</p>}
      {!loading && items.length === 0 && <p className="muted">No hay tickets con esos filtros.</p>}

      <ul className="tickets-list">
        {items.map((t) => {
          const siguiente = SIGUIENTE_ESTADO[t.estado]
          const expanded = expandedId === t.id
          return (
            <li key={t.id} className="ticket-item">
              <div className="row">
                <h3>{t.titulo}</h3>
                <div className="ticket-badges">
                  <span className={`badge badge-tipo badge-tipo-${t.tipo}`}>{t.tipo}</span>
                  <span className={`badge badge-estado badge-estado-${t.estado}`}>
                    {t.estado}
                  </span>
                </div>
              </div>
              {t.descripcion && <p className="ticket-desc">{t.descripcion}</p>}
              <p className="ticket-meta muted">
                Creado: {formatFecha(t.creado_en)} · Solicitante: {t.solicitante_id}
                {t.asignado_id ? ` · Asignado: ${t.asignado_id}` : ' · Sin asignar'}
              </p>
              <div className="ticket-actions">
                <button type="button" onClick={() => void onToggleExpand(t)}>
                  {expanded ? 'Ocultar detalle' : 'Ver comentarios'}
                </button>
                {canManage && !t.asignado_id && (
                  <button type="button" onClick={() => void onAsignarme(t)}>
                    Asignarme
                  </button>
                )}
                {canManage && siguiente && (
                  <button type="button" onClick={() => void onAvanzarEstado(t)}>
                    Pasar a {siguiente}
                  </button>
                )}
              </div>

              {expanded && (
                <div className="ticket-comentarios">
                  <h4>Comentarios</h4>
                  {loadingComentarios && <p className="muted">Cargando…</p>}
                  {comentariosError && <p className="error">{comentariosError}</p>}
                  {!loadingComentarios && !comentariosError && comentarios.length === 0 && (
                    <p className="muted">Sin comentarios.</p>
                  )}
                  <ul className="comentarios-list">
                    {comentarios.map((c) => (
                      <li key={c.id}>
                        <p className="comentario-cuerpo">{c.cuerpo}</p>
                        <p className="muted">
                          {c.autor_id} · {formatFecha(c.creado_en)}
                        </p>
                      </li>
                    ))}
                  </ul>
                  <form
                    className="comentario-form"
                    onSubmit={(e) => void onAddComentario(t.id, e)}
                  >
                    <label>
                      Nuevo comentario
                      <textarea
                        value={nuevoComentario}
                        onChange={(e) => setNuevoComentario(e.target.value)}
                        required
                        minLength={1}
                        rows={2}
                      />
                    </label>
                    <button type="submit">Añadir</button>
                  </form>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
