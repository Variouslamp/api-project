# Documentación del Proyecto: Servicio de Validación de Transacciones

---

## 1. Descripción General

API REST desarrollada con **FastAPI** para procesar solicitudes de validación de transacciones entre servicios en tiempo real. El sistema recibe una solicitud de transacción, valida su estructura, verifica reglas de negocio contra una base de datos simulada de usuarios, y retorna una respuesta de aprobación o rechazo con trazabilidad completa mediante logs. Incluye un **cliente interactivo por terminal** para consumir la API manualmente.

---

## 2. Stack Tecnológico

### API

| Componente | Elección | Justificación |
|---|---|---|
| **Framework** | FastAPI | Validación automática con Pydantic, generación nativa de OpenAPI/Swagger, async nativo |
| **Servidor ASGI** | Uvicorn | Servidor ligero y rápido para correr aplicaciones ASGI como FastAPI |
| **Validación de datos** | Pydantic (incluido en FastAPI) | Coerción automática de tipos, validación de formatos (UUID, datetime), mensajes de error detallados |
| **Tests** | pytest + httpx | Cliente HTTP async compatible con FastAPI TestClient |
| **Contenedor** | Docker + Docker Compose | Entorno reproducible, separación de servicios |

### Cliente

| Componente | Justificación |
|---|---|
| **Python 3.11+** | Único requisito |
| `uuid` (stdlib) | Generación de UUID v4 |
| `datetime` (stdlib) | Generación de timestamps ISO 8601 |
| `urllib.request` (stdlib) | Envío de request HTTP POST |
| `json` (stdlib) | Serialización y pretty-print |
| `os` (stdlib) | Lectura de variables de entorno |

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
├── api/                                  ← API (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       ← App FastAPI, exception handlers, startup
│   │   ├── models.py                     ← Schemas Pydantic
│   │   ├── logging_config.py             ← Configuración de logging (TransactionFormatter)
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
│   │   └── test_transactions.py          ← 16 tests de todos los escenarios
│   ├── docs/
│   │   ├── contrato.yaml                 ← Contrato OpenAPI
│   │   └── tutorial_despliegue.md        ← Tutorial paso a paso de despliegue
│   ├── logs/
│   │   └── transactions.log
│   ├── Dockerfile
│   └── requirements.txt
│
├── client/                               ← Cliente interactivo (CLI)
│   ├── client.py                         ← Script principal
│   ├── .env                              ← Puerto del servidor (API_PORT=7777)
│   ├── docs/
│   │   ├── diseno.md                     ← Documentación de diseño del cliente
│   │   └── instrucciones.txt             ← Tutorial paso a paso del cliente
│   └── README.md                         ← Mini resumen del cliente
│
├── logs/                                ← Volumen Docker (montado en /app/logs del contenedor)
├── documentacion.md                      ← Esta documentación (arquitectura global)
├── docker-compose.yml                    ← Orquestación de servicios
├── .gitignore
└── README.md                             ← README principal del proyecto
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

1. **Timestamp**: Si la diferencia con UTC actual supera 60 segundos o está en futuro → 400 `INVALID_REQUEST`
2. **Moneda soportada**: Si `currency != "COP"` → 409 `TRANSACTION_REJECTED`
3. **Usuario existe**: Si `payerId not in USERS` → 409 `TRANSACTION_REJECTED`
4. **Fondos suficientes**: Si `USERS[payerId] < amount` → 409 `TRANSACTION_REJECTED`
5. **Éxito**: Descuenta el saldo (`USERS[payerId] -= amount`) y retorna `TransactionApproved`

### 5.4 `app/routers/transactions.py` — Endpoint

1. Genera `trace_id = str(uuid4())` al recibir la request
2. Logea evento con `transaction.received`
3. Llama al servicio de validación
4. Logea `transaction.approved` o `transaction.rejected`
5. Retorna 200 con `TransactionApproved` o lanza excepción con `ErrorResponse`

El logging se realiza con un bloque `try/finally` que registra tanto la request como la response en un solo bloque multilínea por transacción, incluyendo el `traceId` como campo contextual.

### 5.5 `app/main.py` — Punto de entrada

- Crea la instancia de `FastAPI` con título "Servicio de Validación de Transacciones"
- Incluye el router de transacciones
- Sobrescribe el manejador de `RequestValidationError` de Pydantic para retornar **400** en lugar de 422
- Configura CORS
- Llama a `configure_logging()` en el startup mediante el ciclo de vida `lifespan`

### 5.6 `app/logging_config.py` — Logging multilínea

#### Formato de log (`TransactionFormatter`)

Se implementó un formateador personalizado que produce **bloques multilínea** en archivos `.log`. Cada bloque representa una transacción completa e incluye:

- **Request**: timestamp, traceId, transactionId, amount, currency, payerId
- **Response**: status HTTP, código de error (si aplica), mensaje, detalles

Ejemplo de archivo `logs/transactions.log`:

```
========================================
[2026-06-13 10:30:01] transaction.received
  traceId:      a1b2c3d4-e5f6-7890-abcd-ef1234567890
  transactionId: 550e8400-e29b-41d4-a716-446655440000
  amount:       50000
  currency:     COP
  payerId:      USR-00001
----------------------------------------
  -> Response: 200
  -> Status:   APROVED
  -> Message:  La transaccion fue procesada correctamente
========================================
```

#### Handlers

| Handler | Destino | Formato | Nivel mínimo |
|---|---|---|---|
| Consola | stdout | Texto plano | INFO |
| Archivo rotativo | `logs/transactions.log` | Bloques multilínea | INFO |

#### Eventos de log

| Evento | Nivel | Contexto adicional |
|---|---|---|
| `transaction.received` | INFO | transactionId, amount, currency, traceId |
| `transaction.approved` | INFO | traceId |
| `transaction.rejected` | WARNING | traceId, código, motivo, detalles |
| `transaction.error` | ERROR | traceId, traceback |

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
                          Log: transaction.received
                                            │
                          Router → Service.validate_transaction()
                           │
                           ├── ¿timestamp válido?        No → 400
                           ├── ¿currency == "COP"?       No → 409
                           ├── ¿payerId in USERS?        No → 409
                           ├── ¿balance >= amount?       No → 409
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

- **Logs**: Todos los eventos de log incluyen el `traceId` en el bloque correspondiente
- **Response 200**: Se devuelve en el body como campo `traceId`
- **Response de error**: Se devuelve dentro de `error.traceId`

Esto permite correlacionar los eventos de una misma transacción desde que llega hasta que se responde.

---

## 10. Logging

### Implementación

Se utiliza el módulo estándar `logging` de Python con un formateador personalizado (`TransactionFormatter`) que produce bloques de texto multilínea. Cada bloque corresponde a una transacción e incluye los datos de la request y la response, separados visualmente para facilitar la lectura en terminal y archivos.

### Archivo de logs

Los logs se escriben en `api/logs/transactions.log` con rotación diaria y se mantienen 7 días de historial.

### Comandos útiles

```bash
# Ver logs en tiempo real
tail -f api/logs/transactions.log

# Buscar por traceId
grep "a1b2c3d4" api/logs/transactions.log

# Buscar por transactionId
grep "550e8400" api/logs/transactions.log
```

---

## 11. Cliente interactivo

### Propósito

Cliente interactivo por terminal que permite construir y enviar requests de validación de transacciones al API, y visualizar la respuesta raw del servidor. Diseñado con fines didácticos para entender el flujo completo cliente-servidor HTTP.

### Flujo del programa

```
INICIO
  │
  ├─ Cargar .env (si existe) → API_PORT
  ├─ Mostrar banner
  │
  └─ Bucle principal (hasta que usuario decida salir)
       │
       ├─ [1/5] transactionId
       │    └─ ¿Manual? → input + aviso si inválido
       │    └─ Auto → uuid4()
       │
       ├─ [2/5] amount
       │    └─ Input libre + aviso de ≥ 1
       │
       ├─ [3/5] currency
       │    └─ Input libre + aviso de COP
       │
       ├─ [4/5] payerId
       │    └─ Input libre + aviso de USR-00001 a USR-00010
       │
       ├─ [5/5] timestamp
       │    └─ ¿Manual? → input ISO 8601 + aviso si inválido
       │    └─ Auto → datetime.now(timezone.utc)
       │
       ├─ Mostrar resumen JSON (indentado)
       │
       ├─ ¿Enviar?
       │    └─ No → reinicia el bucle
       │
       ├─ POST http://localhost:{port}/transactions/validate
       │
       ├─ Mostrar response RAW (JSON indentado)
       │
       └─ ¿Otra validación?
            └─ Sí → reinicia bucle
            └─ No → FIN
```

### Puerto y conexión

El puerto se define en `client/.env`:

```env
API_PORT=7777
```

Si el archivo no existe o no tiene la variable, se usa `7777` por defecto.

**Importante:** Si ejecutas la API localmente sin Docker, Uvicorn corre en el puerto `8000`. El cliente por defecto apunta al puerto `7777` (para Docker). Debes cambiar `client/.env` a `API_PORT=8000` para conectar el cliente con la API local.

### Estructura del cliente

```
client/
├── client.py              ← Script principal
├── .env                   ← Puerto del servidor (API_PORT=7777)
├── docs/
│   ├── diseno.md          ← Documentación de diseño
│   └── instrucciones.txt  ← Tutorial paso a paso
└── README.md              ← Mini resumen
```

---

## 12. Tests

Se implementaron 16 tests automatizados con `pytest` + `httpx`, cubriendo todos los escenarios de la matriz de validaciones:

| Test | Input | Expected |
|---|---|---|
| `test_approved` | Payload válido, usuario con fondos | 200 + saldo descontado |
| `test_approved_updates_balance` | Mismo usuario, 2 transacciones exitosas | Saldo disminuye correctamente |
| `test_missing_field` | Falta `amount` | 400 `INVALID_REQUEST` |
| `test_missing_multiple_fields` | Faltan 2 campos | 400 + lista de errores |
| `test_invalid_uuid` | `transactionId="abc"` | 400 `INVALID_REQUEST` |
| `test_amount_zero` | `amount=0` | 400 `INVALID_REQUEST` |
| `test_amount_negative` | `amount=-500` | 400 `INVALID_REQUEST` |
| `test_invalid_timestamp` | `timestamp="ayer"` | 400 `INVALID_REQUEST` |
| `test_stale_timestamp` | timestamp con > 1 min de antigüedad | 400 `INVALID_REQUEST` |
| `test_future_timestamp` | timestamp en el futuro | 400 `INVALID_REQUEST` |
| `test_unsupported_currency` | `currency="USD"` | 409 `TRANSACTION_REJECTED` |
| `test_user_not_found` | `payerId="USR-99999"` | 409 `TRANSACTION_REJECTED` |
| `test_insufficient_funds` | `amount > balance` | 409 `TRANSACTION_REJECTED` |
| `test_trace_id_in_response` | Payload válido | 200 + traceId presente |
| `test_trace_id_in_error` | Payload inválido | 400 + traceId presente |
| `test_balance_preserved_after_rejection` | Transacción rechazada | Saldo no se descuenta |

### Ejecución

```bash
python -m pytest api/tests/ -v
```

---

## 13. Docker

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
      - "127.0.0.1:7777:8000"
    volumes:
      - ./logs:/app/logs
```

> **Nota:** El directorio `logs/` en la raíz del proyecto es el punto de montaje del volumen Docker. No contiene código fuente. Cuando ejecutas la API localmente sin Docker, los logs se escriben en `api/logs/`.

### Comandos

```bash
# Construir y ejecutar en background
docker compose up -d

# Ver logs del contenedor
docker compose logs -f

# Detener
docker compose down
```

### Acceso a Swagger UI

| Contexto | URL |
|---|---|
| Via Docker | `http://localhost:7777/docs` |
| Via local (uvicorn) | `http://localhost:8000/docs` |

---

## 14. Ejecución local (sin Docker)

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Luego abrir `http://localhost:8000/docs` para acceder a Swagger UI.

---

## 15. Resumen de puertos

| Contexto | Puerto | Cómo acceder |
|---|---|---|
| API en Docker | `7777` (host) → `8000` (container) | `curl http://localhost:7777/...` |
| API local (uvicorn) | `8000` | `curl http://localhost:8000/...` |
| Cliente (default para Docker) | `7777` | `python client/client.py` |
| Cliente (para usar con local) | `8000` | Editar `client/.env` a `API_PORT=8000` |
| Swagger via Docker | `7777` | `http://localhost:7777/docs` |
| Swagger via local | `8000` | `http://localhost:8000/docs` |

---

*Documentación generada el 13 de junio de 2026.*
