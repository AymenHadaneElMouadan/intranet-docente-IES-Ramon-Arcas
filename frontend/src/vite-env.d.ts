/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_GOOGLE_CLIENT_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface CredentialResponse {
  credential?: string
}

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string
    callback: (response: CredentialResponse) => void
    /** Usa FedCM en el botón (Chrome) para evitar popup bloqueado. */
    use_fedcm_for_button?: boolean
  }) => void
  renderButton: (
    parent: HTMLElement,
    options: { theme?: string; size?: string; text?: string; width?: number },
  ) => void
}

interface Window {
  google?: {
    accounts: {
      id: GoogleAccountsId
    }
  }
}
