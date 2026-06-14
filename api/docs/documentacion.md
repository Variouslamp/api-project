# Documentación del Proyecto: Servicio de Validación de Transacciones

---

## 1. Descripción General

API REST desarrollada con **FastAPI** para procesar solicitudes de validación de transacciones entre servicios en tiempo real. El sistema recibe una solicitud de transacción, valida su estructura, verifica reglas de negocio contra una base de datos simulada de usuarios, y retorna una respuesta de aprobación o rechazo con trazabilidad completa mediante logs estructurados.

---

## 2. Stack Tecnológico

| Componente | Elección | Justificación |
|---|---|---|
| **Framework** | FastAPI | Validación automática con Pydantic, generación nativa de OpenAPI/Swagger, async nativo |
| **Servidor ASGI** | Uvicorn | Servidor ligero y rápido para correr aplicaciones ASGI como FastAPI |
| **Validación de datos** | Pydantic (incluido en FastAPI) | Coerción automática de tipos, validación de formatos (UUID, datetime), mensajes de error detallados |
| **Logging** | structlog | Logging estructurado en formato JSON Lines, binding de contexto por request, pipeline de procesadores |
| **Tests** | pytest + httpx | Cliente HTTP async compatible con FastAPI TestClient |
| **Contenedor** | Docker + Docker Compose | Entorno reproducible, separación de servicios |

---

## 3. Contrato OpenAPI

El contrato se encuentra en `api/docs/contrato.yaml` (OpenAPI 3.0.1).

### Endpoint único

```
POST /transactions/validate
```

### Request body — `TransactionRequest`

| Campo | Tipo | Requerido | Restricciones |
|---|---|---|---|
| `transactionId` | string (UUID) | Sí | Debe ser un UUID válido |
| `amount` | number | Sí | Mínimo: 1 |
| `currency` | string | Sí | Solo se acepta "COP" |
| `payerId` | string | Sí | Formato: USR-XXXXX |
| `timestamp` | string (date-time) | Sí | ISO 8601, ≤ 1 minuto de antigüedad, no futuro |

### Response 200 — `TransactionApproved`

```json
{
  "status": "APROVED",
  "message": "La transaccion fue procesada correctamente",
  "processedAt": "2026-06-13T10:30:01Z",
  "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Response 400/409/500 — `ErrorResponse`

```json
{
  "error": {
    "code": "TRANSACTION_REJECTED",
    "message": "La transaccion no pudo completarse",
    "details": ["Saldo insuficiente. Balance: 500000, Requerido: 600000"],
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

## 4. Estructura del Proyecto

```
api-project/                              ← Raíz del proyecto
│
├── api/                                  ← API (imagen Docker 1)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       ← App FastAPI, exception handlers, startup
│   │   ├── models.py                     ← Schemas Pydantic (TransactionRequest, TransactionApproved, ErrorResponse)
│   │   ├── logging_config.py             ← Configuración de structlog (procesadores, handlers, formato)
│   │   ├── users_db.py                   ← Diccionario simulado de usuarios y saldos
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── transactions.py           ← Endpoint POST /transactions/validate
│   │   └── services/
│   │       ├── __init__.py
│   │       └── validation.py             ← Lógica de validación y descuento de saldo
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                   ← Fixtures (cliente de prueba, payloads)
│   │   └── test_transactions.py          ← Tests de todos los escenarios
│   ├── docs/
│   │   ├── contrato.yaml                 ← Contrato OpenAPI
│   │   └── documentacion.md              ← Esta documentación
│   ├── logs/
│   │   └── .gitkeep
│   ├── Dockerfile
│   └── requirements.txt
│
├── client/                               ← Cliente (imagen Docker 2, futura)
│   └── (pendiente)
│
├── docker-compose.yml                    ← Orquestación de servicios
├── .gitignore
└── README.md
```

---

## 5. Responsabilidad de cada capa

### 5.1 `app/models.py` — Schemas Pydantic

Define tres modelos que reflejan exactamente el contrato OpenAPI:

- **`TransactionRequest`**: `transactionId` (UUID), `amount` (float ≥ 1), `currency` (str), `payerId` (str), `timestamp` (datetime)
- **`TransactionApproved`**: `status` (str, "APROVED"), `message` (str), `processedAt` (datetime), `traceId` (str)
- **`ErrorResponse`**: `error` → `ErrorDetail` con `code`, `message`, `details` (list[str]), `traceId`

La validación de tipos, formatos y restricciones (`minimum: 1`, `format: uuid`, `format: date-time`) la maneja Pydantic automáticamente.

### 5.2 `app/users_db.py` — Base de datos simulada

Diccionario en memoria con 10 usuarios, cada uno con un saldo inicial de 1,000,000 COP:

| ID | Saldo inicial |
|---|---|
| USR-00001 | 1,000,000 |
| USR-00002 | 1,000,000 |
| USR-00003 | 1,000,000 |
| USR-00004 | 1,000,000 |
| USR-00005 | 1,000,000 |
| USR-00006 | 1,000,000 |
| USR-00007 | 1,000,000 |
| USR-00008 | 1,000,000 |
| USR-00009 | 1,000,000 |
| USR-00010 | 1,000,000 |

### 5.3 `app/services/validation.py` — Lógica de negocio

Función `validate_transaction(request: TransactionRequest, trace_id: str) -> TransactionApproved`

Orden de validación:

1. **Moneda soportada**: Si `currency != "COP"` → 409 `TRANSACTION_REJECTED`
2. **Usuario existe**: Si `payerId not in USERS` → 409 `TRANSACTION_REJECTED`
3. **Fondos suficientes**: Si `USERS[payerId] < amount` → 409 `TRANSACTION_REJECTED`
4. **Éxito**: Descuenta el saldo (`USERS[payerId] -= amount`) y retorna `TransactionApproved`

### 5.4 `app/routers/transactions.py` — Endpoint

1. Genera `trace_id = str(uuid4())` al recibir la request
2. Bindea `trace_id` y `transaction_id` al logger con structlog
3. Logea evento `transaction.received`
4. Llama al servicio de validación
5. Logea `transaction.approved` o `transaction.rejected`
6. Retorna 200 con `TransactionApproved` o lanza `HTTPException` con `ErrorResponse`

### 5.5 `app/main.py` — Punto de entrada

- Crea la instancia de `FastAPI` con título "Servicio de Validación de Transacciones"
- Incluye el router de transacciones
- Sobrescribe el manejador de `RequestValidationError` de Pydantic para retornar **400** en lugar de 422
- Configura CORS
- Llama a `configure_logging()` en el startup

### 5.6 `app/logging_config.py` — Logging estructurado

#### Pipeline de procesadores structlog

1. `TimeStamper(fmt="iso")` → Añade timestamp ISO 8601
2. `add_log_level` → Añade el nivel del log
3. `JSONRenderer()` → Serializa el diccionario a JSON

#### Handlers

| Handler | Destino | Formato | Nivel mínimo |
|---|---|---|---|
| Consola | stdout | JSON | INFO |
| Archivo rotativo | `logs/transactions.jsonl` | JSON | INFO |

#### Eventos de log

| Evento | Nivel | Contexto adicional |
|---|---|---|
| `transaction.received` | INFO | transaction_id, amount, currency, trace_id |
| `transaction.validating` | DEBUG | Reglas aplicadas |
| `transaction.approved` | INFO | trace_id, elapsed_ms |
| `transaction.rejected` | WARNING | trace_id, motivo, detalles |
| `transaction.error` | ERROR | trace_id, traceback |

Cada línea del archivo `logs/transactions.jsonl` tiene este formato:

```jsonl
{"timestamp":"2026-06-13T10:30:01Z","level":"INFO","event":"transaction.received","transaction_id":"550e8400-e29b-41d4-a716-446655440000","amount":150.0,"currency":"COP","trace_id":"a1b2c3d4-..."}
{"timestamp":"2026-06-13T10:30:01Z","level":"INFO","event":"transaction.approved","transaction_id":"550e8400-...","trace_id":"a1b2c3d4-...","elapsed_ms":4}
```

---

## 6. Matriz de Validaciones vs Respuestas

| # | Validación | Responsable | HTTP | `code` | `message` | `details` |
|---|---|---|---|---|---|---|
| 1 | Campos faltantes | Pydantic | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["El campo amount es requerido"]` |
| 2 | `transactionId` no es UUID | Pydantic | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["transactionId debe ser un UUID válido"]` |
| 3 | `amount` < 1 | Pydantic | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["amount debe ser mayor o igual a 1"]` |
| 4 | `timestamp` mal formateado | Pydantic | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["timestamp no tiene un formato de fecha válido"]` |
| 5 | `timestamp` > 1 min en pasado | Servicio | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["timestamp supera el límite de 1 minuto de antigüedad"]` |
| 6 | `timestamp` en el futuro | Servicio | 400 | `INVALID_REQUEST` | `Los datos enviados no cumplen con el formato requerido` | `["timestamp no puede estar en el futuro"]` |
| 7 | `currency != "COP"` | Servicio | 409 | `TRANSACTION_REJECTED` | `La transaccion no pudo completarse` | `["Moneda no soportada: X. Solo se acepta COP"]` |
| 8 | `payerId` no existe | Servicio | 409 | `TRANSACTION_REJECTED` | `La transaccion no pudo completarse` | `["El usuario X no existe"]` |
| 9 | Saldo insuficiente | Servicio | 409 | `TRANSACTION_REJECTED` | `La transaccion no pudo completarse` | `["Saldo insuficiente. Balance: X, Requerido: Y"]` |
| 10 | **Éxito** → descuenta saldo | Servicio | 200 | — | `La transaccion fue procesada correctamente` | — |
| 11 | Error inesperado | FastAPI | 500 | `INTERNAL_ERROR` | `Ocurrio un error inesperado al procesar la solicitud` | `[]` |

---

## 7. Flujo de una request exitosa

```
Cliente ──POST /transactions/validate──→ FastAPI
                                            │
                          Pydantic valida estructura y tipos
                           Si falla ──→ 400 INVALID_REQUEST
                                            │
                          Router genera traceId = uuid4()
                          Router bindea traceId + transactionId al logger
                          Log: transaction.received
                                            │
                          Router → Service.validate_transaction()
                           │
                           ├── ¿currency == "COP"?    No → 409
                           ├── ¿payerId in USERS?     No → 409
                           ├── ¿balance >= amount?    No → 409
                           └── Sí → descuenta saldo, retorna ✅
                                            │
                          Log: transaction.approved
                          Response 200 + TransactionApproved
```

---

## 8. Formato de Responses

### 200 OK — Transacción aprobada

```json
{
  "status": "APROVED",
  "message": "La transaccion fue procesada correctamente",
  "processedAt": "2026-06-13T10:30:01Z",
  "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 400 Bad Request — Error de formato

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Los datos enviados no cumplen con el formato requerido",
    "details": ["El campo amount debe ser mayor o igual a 1"],
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

### 409 Conflict — Transacción rechazada

```json
{
  "error": {
    "code": "TRANSACTION_REJECTED",
    "message": "La transaccion no pudo completarse",
    "details": ["Saldo insuficiente. Balance: 500000, Requerido: 600000"],
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Ocurrio un error inesperado al procesar la solicitud",
    "details": [],
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

## 9. Trazabilidad con `traceId`

El `traceId` se genera con `uuid4()` al recibir cada request y se utiliza para:

- **Logs**: Todos los eventos de log incluyen el `traceId` como campo contextual
- **Response 200**: Se devuelve en el body como campo `traceId`
- **Response de error**: Se devuelve dentro de `error.traceId`

Esto permite correlacionar todos los eventos de una misma transacción desde que llega hasta que se responde.

---

## 10. Logging con structlog

### ¿Qué es structlog?

Librería de logging para Python que trata cada entrada de log como un **diccionario** (event dict) en lugar de una cadena de texto. Los diccionarios pasan por una cadena de procesadores que los transforman y enriquecen antes de serializarlos a JSON.

### Características principales

- **Binding de contexto**: `log.bind(transaction_id=id)` — todos los logs siguientes incluyen ese campo sin repetirlo
- **Procesadores en cadena**: Funciones que reciben y devuelven diccionarios (timestamp, nivel, serialización)
- **Múltiples handlers**: Consola y archivo simultáneamente
- **Formato JSON Lines**: Cada línea es un objeto JSON válido, permitiendo usar `grep` y `jq` para filtrar

### Comandos útiles para consultar logs

```bash
# Buscar por traceId (como grep tradicional)
cat logs/transactions.jsonl | grep "a1b2c3d4-..."

# Buscar por transactionId
cat logs/transactions.jsonl | grep "550e8400-..."

# Filtrar solo eventos rechazados
jq 'select(.event == "transaction.rejected")' logs/transactions.jsonl

# Ver campos específicos
jq '{event, transaction_id, amount}' logs/transactions.jsonl

# Contar ocurrencias por evento
jq -r '.event' logs/transactions.jsonl | sort | uniq -c

# Filtrar por rango de tiempo
jq 'select(.timestamp > "2026-06-13T10:00:00" and .timestamp < "2026-06-13T11:00:00")' logs/transactions.jsonl
```

---

## 11. Tests planificados

| Test | Input | Expected |
|---|---|---|
| `test_approved` | Payload válido, usuario con fondos | 200 + saldo descontado |
| `test_missing_field` | Falta `amount` | 400 `INVALID_REQUEST` |
| `test_invalid_uuid` | `transactionId="abc"` | 400 `INVALID_REQUEST` |
| `test_amount_zero` | `amount=0` | 400 `INVALID_REQUEST` |
| `test_invalid_timestamp` | `timestamp="ayer"` | 400 `INVALID_REQUEST` |
| `test_stale_timestamp` | timestamp con > 1 min de antigüedad | 400 `INVALID_REQUEST` |
| `test_future_timestamp` | timestamp en el futuro | 400 `INVALID_REQUEST` |
| `test_unsupported_currency` | `currency="USD"` | 409 `TRANSACTION_REJECTED` |
| `test_user_not_found` | `payerId="USR-99999"` | 409 `TRANSACTION_REJECTED` |
| `test_insufficient_funds` | `amount > balance` | 409 `TRANSACTION_REJECTED` |

---

## 12. Docker

### Dockerfile (`api/Dockerfile`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (`docker-compose.yml`)

```yaml
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - ./api/logs:/app/logs

  client:
    build: ./client
    profiles:
      - donotstart
```

### Comandos

```bash
# Construir y ejecutar solo la API
docker compose up api

# Construir y ejecutar en background
docker compose up -d api

# Ver logs del contenedor
docker compose logs -f api
```

---

## 13. Ejecución local (sin Docker)

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Luego abrir `http://localhost:8000/docs` para acceder a Swagger UI.

---

## 14. Desarrollo futuro

- **`client/`**: Cliente que consuma la API para simular el envío de transacciones
- **Base de datos real**: Reemplazar `users_db.py` con una BD persistente
- **Autenticación**: Agregar mecanismos de seguridad
- **Más endpoints**: Ampliar el contrato con nuevas funcionalidades

---

*Documentación generada el 13 de junio de 2026.*
