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
├── client/                  # Cliente interactivo (CLI)
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

## Cliente interactivo

En `client/` hay un script CLI que permite probar la API manualmente:
- Pregunta campo por campo (UUID, monto, moneda, pagador, timestamp)
- Permite ingresar datos manuales para probar errores intencionalmente
- Muestra la respuesta del servidor en JSON indentado
- Puerto configurable via `client/.env`

```bash
python client/client.py
```

Ver `client/docs/instrucciones.txt` para una guía paso a paso.

## Documentación detallada

Ver `api/docs/documentacion.md` para información completa del proyecto.
