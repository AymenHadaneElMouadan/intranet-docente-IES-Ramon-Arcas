import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  createAnuncio,
  fijarAnuncio,
  listAnuncios,
  type Anuncio,
} from '../services/api'

type Props = {
  roles: string[]
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

/** Tablón de anuncios: feed + alta (admin/directiva) + fijar (admin). */
export function AnunciosPage({ roles }: Props) {
  const canCreate = roles.includes('admin') || roles.includes('directiva')
  const canFijar = roles.includes('admin')

  const [items, setItems] = useState<Anuncio[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [okMsg, setOkMsg] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [titulo, setTitulo] = useState('')
  const [cuerpo, setCuerpo] = useState('')
  const [departamento, setDepartamento] = useState('')
  const [expiraEn, setExpiraEn] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listAnuncios()
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el tablón')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setOkMsg(null)
    try {
      await createAnuncio({
        titulo: titulo.trim(),
        cuerpo: cuerpo.trim(),
        departamento: departamento.trim() || null,
        expira_en: expiraEn ? new Date(expiraEn).toISOString() : null,
      })
      setTitulo('')
      setCuerpo('')
      setDepartamento('')
      setExpiraEn('')
      setOkMsg('Anuncio publicado.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo publicar el anuncio')
    } finally {
      setSaving(false)
    }
  }

  const onToggleFijar = async (anuncio: Anuncio) => {
    setError(null)
    setOkMsg(null)
    try {
      await fijarAnuncio(anuncio.id, !anuncio.fijado)
      setOkMsg(anuncio.fijado ? 'Anuncio desfijado.' : 'Anuncio fijado.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar el anuncio')
    }
  }

  return (
    <section className="card">
      <h2>Tablón de anuncios</h2>
      <p className="hint">
        Feed del centro. Los caducados no aparecen (los filtra la API). Publicar requiere
        rol admin o directiva; fijar solo admin.
      </p>

      {canCreate && (
        <form className="anuncio-form" onSubmit={(e) => void onCreate(e)}>
          <h3>Publicar anuncio</h3>
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
            Cuerpo
            <textarea
              value={cuerpo}
              onChange={(e) => setCuerpo(e.target.value)}
              required
              minLength={1}
              rows={4}
            />
          </label>
          <label>
            Departamento (opcional)
            <input
              value={departamento}
              onChange={(e) => setDepartamento(e.target.value)}
              placeholder="Vacío = general"
            />
          </label>
          <label>
            Caduca el (opcional)
            <input
              type="datetime-local"
              value={expiraEn}
              onChange={(e) => setExpiraEn(e.target.value)}
            />
          </label>
          <button type="submit" disabled={saving}>
            {saving ? 'Publicando…' : 'Publicar'}
          </button>
        </form>
      )}

      {error && <p className="error">{error}</p>}
      {okMsg && <p className="ok">{okMsg}</p>}

      {loading && <p>Cargando anuncios…</p>}
      {!loading && items.length === 0 && <p className="muted">No hay anuncios visibles.</p>}

      <ul className="anuncios-list">
        {items.map((a) => (
          <li key={a.id} className={`anuncio-item${a.fijado ? ' anuncio-fijado' : ''}`}>
            <div className="row">
              <h3>{a.titulo}</h3>
              {a.fijado && <span className="badge badge-fijado">Fijado</span>}
            </div>
            <p className="anuncio-cuerpo">{a.cuerpo}</p>
            <p className="anuncio-meta muted">
              {a.departamento || 'General'} · Publicado: {formatFecha(a.creado_en)}
              {a.expira_en ? ` · Caduca: ${formatFecha(a.expira_en)}` : ''}
            </p>
            {canFijar && (
              <button type="button" onClick={() => void onToggleFijar(a)}>
                {a.fijado ? 'Desfijar' : 'Fijar destacado'}
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
