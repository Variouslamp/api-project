# api-project

Proyecto universitario para la creación de un **Servicio de Validación de Transacciones** basado en un contrato OpenAPI 3.0.1.

## Stack tecnológico

| Componente | Herramienta |
|---|---|
| Framework | FastAPI |
| Servidor ASGI | Uvicorn |
| Validación | Pydantic |
| Logging | structlog (JSON Lines) |
| Contenedor | Docker |
| Tests | pytest + httpx |

## Estructura del proyecto

```
api-project/
├── api/                     # API (FastAPI)
│   ├── app/
│   │   ├── main.py          # Punto de entrada
│   │   ├── models.py        # Schemas Pydantic
│   │   ├── logging_config.py# Configuración de structlog
│   │   ├── users_db.py      # Diccionario de usuarios y saldos
│   │   ├── routers/         # Endpoints
│   │   └── services/        # Lógica de negocio
│   ├── tests/               # Tests automatizados
│   ├── docs/                # Contrato y documentación
│   ├── Dockerfile
│   └── requirements.txt
├── client/                  # Cliente (futuro)
├── docker-compose.yml       # Orquestación de servicios
└── .gitignore
```

## Endpoint

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/transactions/validate` | Valida una transacción |

## Códigos de respuesta

| Código | Significado |
|---|---|
| 200 | Transacción aprobada |
| 400 | Datos inválidos (formato) |
| 409 | Transacción rechazada (reglas de negocio) |
| 500 | Error interno del servidor |

## Ejecución local

```bash
# Con Docker
docker compose up api

# Sin Docker
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La documentación interactiva (Swagger UI) estará disponible en `http://localhost:8000/docs`.

## Documentación detallada

Ver `api/docs/documentacion.md` para información completa del proyecto.
