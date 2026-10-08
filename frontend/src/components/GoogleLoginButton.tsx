import { useEffect, useRef } from 'react'
import { loginWithGoogleIdToken } from '../services/api'

type Props = {
  onLoggedIn: () => void
  onError?: (message: string) => void
}

/**
 * Botón oficial de Google Identity Services.
 * Requiere VITE_GOOGLE_CLIENT_ID y el script GIS en index.html.
 * FedCM evita el popup en Chrome cuando está disponible.
 */
export function GoogleLoginButton({ onLoggedIn, onError }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const onLoggedInRef = useRef(onLoggedIn)
  const onErrorRef = useRef(onError)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  onLoggedInRef.current = onLoggedIn
  onErrorRef.current = onError

  useEffect(() => {
    if (!clientId || !hostRef.current) return

    const render = () => {
      if (!window.google || !hostRef.current) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        use_fedcm_for_button: true,
        callback: async (response) => {
          if (!response.credential) {
            onErrorRef.current?.(
              'Google no devolvió credencial. Permite ventanas emergentes o usa Chrome/Edge del sistema.',
            )
            return
          }
          try {
            await loginWithGoogleIdToken(response.credential)
            onLoggedInRef.current()
          } catch (err) {
            onErrorRef.current?.(err instanceof Error ? err.message : 'Error al iniciar sesión')
          }
        },
      })
      hostRef.current.innerHTML = ''
      window.google.accounts.id.renderButton(hostRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        width: 280,
      })
    }

    if (window.google) {
      render()
      return
    }

    const timer = window.setInterval(() => {
      if (window.google) {
        window.clearInterval(timer)
        render()
      }
    }, 200)
    return () => window.clearInterval(timer)
  }, [clientId])

  if (!clientId) {
    return (
      <p className="hint">
        Configura <code>VITE_GOOGLE_CLIENT_ID</code> en <code>frontend/.env</code> para habilitar el
        login.
      </p>
    )
  }

  return <div ref={hostRef} />
}
