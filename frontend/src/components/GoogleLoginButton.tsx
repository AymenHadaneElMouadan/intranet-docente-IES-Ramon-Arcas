import { useEffect, useRef } from 'react'
import { loginWithGoogleIdToken } from '../services/api'

type Props = {
  onLoggedIn: () => void
}

/**
 * Botón oficial de Google Identity Services.
 * Requiere VITE_GOOGLE_CLIENT_ID y el script GIS en index.html.
 */
export function GoogleLoginButton({ onLoggedIn }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  useEffect(() => {
    if (!clientId || !hostRef.current) return

    const render = () => {
      if (!window.google || !hostRef.current) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          if (!response.credential) return
          await loginWithGoogleIdToken(response.credential)
          onLoggedIn()
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

    if (window.google) render()
    else {
      const timer = window.setInterval(() => {
        if (window.google) {
          window.clearInterval(timer)
          render()
        }
      }, 200)
      return () => window.clearInterval(timer)
    }
  }, [clientId, onLoggedIn])

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
