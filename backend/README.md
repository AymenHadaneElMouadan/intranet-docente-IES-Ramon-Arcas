# Backend (FastAPI)

Esqueleto vacío. La implementación de endpoints vendrá en commits posteriores.

## Capas previstas

```
app/
├── api/        # Routers (HTTP fino)
├── core/       # Config, seguridad JWT, Depends()
├── models/     # Esquemas Pydantic / documentos MongoDB
├── services/   # Lógica de negocio
└── utils/      # Helpers
tests/          # Pytest
```

Contrato: `../openapi/openapi.yaml` y `../docs/api-contract.md`.
