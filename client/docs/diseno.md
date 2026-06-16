# Documentacion de Diseno — Cliente de Validacion de Transacciones

---

## 1. Proposito

Cliente interactivo por terminal que permite a un usuario construir y enviar
request de validacion de transacciones al API, y visualizar la respuesta
raw del servidor. Disenado con fines didacticos para entender el flujo
completo cliente-servidor HTTP.

---

## 2. Stack tecnologico

| Componente | Justificacion |
|---|---|
| **Python 3.11+** | Unico requisito |
| `uuid` (stdlib) | Generacion de UUID v4 |
| `datetime` (stdlib) | Generacion de timestamps ISO 8601 |
| `urllib.request` (stdlib) | Envio de request HTTP POST |
| `json` (stdlib) | Serializacion y pretty-print |
| `os` (stdlib) | Lectura de variables de entorno |

**Decision:** No se usan librerias externas. El cliente funciona con
Python puro para minimizar dependencias.

---

## 3. Estructura de archivos

```
client/
├── client.py        ← Script principal
├── .env             ← Puerto del servidor (opcional, default 7777)
├── docs/
│   ├── diseno.md    ← Esta documentacion
│   └── instrucciones.txt ← Tutorial paso a paso
└── README.md        ← Mini resumen
```

---

## 4. Flujo del programa

```
INICIO
  │
  ├─ Cargar .env (si existe) → API_PORT
  ├─ Mostrar banner
  │
  └─ Bucle principal (hasta que usuario decida salir)
       │
       ├─ [1/5] transactionId
       │    └─ ¿Manual? → input + aviso si invalido
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
       │    └─ ¿Manual? → input ISO 8601 + aviso si invalido
       │    └─ Auto → datetime.now(timezone.utc)
       │
       ├─ Mostrar resumen JSON (indentado)
       │
       ├─ ¿Enviar?
       │    └─ No → reinicia el bucle (vuelve a preguntar todo)
       │
       ├─ POST http://localhost:{port}/transactions/validate
       │    └─ Error de conexion → JSON de error simulado
       │
       ├─ Mostrar response RAW (JSON indentado)
       │
       └─ ¿Otra validacion?
            └─ Si → reinicia bucle
            └─ No → FIN
```

---

## 5. Formato del request

```json
{
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "50000",
  "currency": "COP",
  "payerId": "USR-00001",
  "timestamp": "2026-06-13T10:30:00Z"
}
```

Nota: `amount` se envia como string (input del usuario). Pydantic del
lado del servidor lo convertira a numero.

---

## 6. Codigos de error del servidor (visibles en la respuesta)

| HTTP | `code` | Significado |
|---|---|---|
| 400 | `INVALID_REQUEST` | Datos no cumplen formato requerido |
| 409 | `TRANSACTION_REJECTED` | Transaccion rechazada (moneda, usuario, fondos) |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |

---

## 7. Puerto configurable

El puerto se define en `client/.env`:

```env
API_PORT=7777
```

Si el archivo no existe o no tiene la variable, se usa `7777` por defecto.
Esto permite cambiar el puerto sin modificar el codigo.

**Importante:** Si ejecutas la API localmente sin Docker, Uvicorn corre en el
puerto `8000`. El cliente por defecto apunta al `7777` (para Docker). Debes
cambiar `client/.env` a `API_PORT=8000` para conectar el cliente con la API local.

---

## 8. Mecanica de campos manuales

| Campo | Validacion del cliente | Comportamiento |
|---|---|---|
| `transactionId` manual | Solo aviso si no es UUID valido | Se envia igual |
| `amount` | Solo aviso si no es numero | Se envia igual |
| `currency` | Ninguna | Se envia tal cual |
| `payerId` | Ninguna | Se envia tal cual |
| `timestamp` manual | Solo aviso si no es ISO 8601 | Se envia igual |

Esto permite al usuario probar intencionalmente datos invalidos y ver
como responde el servidor con errores 400/409.

---

## 9. Formato de respuesta

Toda respuesta del servidor se imprime con `json.dumps(indent=2)` para
facilitar la lectura:

```json
{
  "status": "APROVED",
  "message": "La transaccion fue procesada correctamente",
  "processedAt": "2026-06-13T10:30:01Z",
  "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

O en caso de error:

```json
{
  "error": {
    "code": "TRANSACTION_REJECTED",
    "message": "La transaccion no pudo completarse",
    "details": [
      "Saldo insuficiente. Balance: 500000, Requerido: 600000"
    ],
    "traceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```
