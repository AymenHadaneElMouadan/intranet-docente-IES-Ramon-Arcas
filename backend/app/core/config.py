"""Configuración cargada desde variables de entorno / .env."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor solo permitido en development / tests locales.
_INSECURE_DEFAULT_SECRET = "dev-insecure-secret"


class Settings(BaseSettings):
    """Ajustes de la aplicación. No subir secretos reales a Git."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Intranet Docente"
    environment: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "intranet_docente"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = _INSECURE_DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 14

    # Client ID de Google OAuth (vacío en tests con mock).
    google_client_id: str = ""

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # En producción debe ser true (HTTPS). En local false para http://localhost.
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_name: str = "refresh_token"
    cookie_path: str = "/api/v1/auth"

    @model_validator(mode="after")
    def jwt_secret_must_be_strong_outside_dev(self) -> "Settings":
        """Fuera de development, exige un secreto JWT fuerte y no el default inseguro."""
        if self.environment == "development":
            return self
        secret = (self.jwt_secret or "").strip()
        if not secret or secret == _INSECURE_DEFAULT_SECRET or len(secret) < 32:
            raise ValueError(
                "JWT_SECRET debe definirse con al menos 32 caracteres "
                "cuando ENVIRONMENT no es 'development'"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cachea Settings para no releer el entorno en cada request."""
    return Settings()


settings = get_settings()
