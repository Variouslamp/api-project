# Tutorial de Despliegue — Servicio de Validación de Transacciones

## Despliegue Usando Docker (Recomendado)

En la carpeta raiz del proyecto ejecutar con docker y docker compose instalados:

```bash
docker compose up -d
```
y verificamos si el docker esta activo con 


```bash
docker ps
```
y si notamos algo como 

```bash
CONTAINER ID   IMAGE             COMMAND                  CREATED          STATUS          PORTS                      NAMES
7d4456f6670d   api-project-api   "uvicorn app.main:ap…"   10 seconds ago   Up 5 seconds    127.0.0.1:7777->8000/tcp   api-project-api-1
```
significa que esta corriendo.

La API queda en: `http://localhost:7777`

Si usas Swagger UI via Docker: `http://localhost:7777/docs`

---
# Despliegue local
---
## Requisitos

- Python 3.11 o superior instalado
- pip instalado

---

## Paso 1: Abrir terminal y ubicarse en la carpeta de la API

```bash
cd api-project/api
```

## Paso 2: Crear y activar un entorno virtual (opcional pero recomendado)

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

## Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instala: fastapi, uvicorn, pytest, httpx.

## Paso 4: Iniciar el servidor (modo desarrollo)

```bash
uvicorn app.main:app --reload
```

| Componente | Significado |
|---|---|
| `uvicorn` | El servidor ASGI |
| `app.main:app` | "Ve al archivo `app/main.py` y busca la variable `app`" |
| `--reload` | Reinicia automáticamente al cambiar código (solo desarrollo) |

La API se levanta en: `http://localhost:8000`

## Paso 5: Probar el endpoint

```bash
curl -X POST http://localhost:8000/transactions/validate \
  -H "Content-Type: application/json" \
  -d '{
    "transactionId": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 50000,
    "currency": "COP",
    "payerId": "USR-00001",
    "timestamp": "2026-06-13T10:30:00Z"
  }'
```

Respuesta exitosa (200):
```json
{"status":"APROVED","message":"La transaccion fue procesada correctamente","processedAt":"...","traceId":"..."}
```

## Paso 6: Ver la documentación interactiva (Swagger UI)

Abrir en el navegador: `http://localhost:8000/docs`

Ahí puedes probar el endpoint con botones y formularios.

## Paso 7: Ejecutar los tests

```bash
python -m pytest tests/ -v
```

Deberían salir 16 tests pasando.

## Paso 8: Ver los logs

Los logs se guardan en `api/logs/transactions.log`.

```bash
# Ver en tiempo real
tail -f logs/transactions.log

# Buscar por traceId
cat logs/transactions.log | grep "el-trace-id"
```

## Paso 9: Iniciar el servidor (modo producción, sin `--reload`)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` permite conexiones desde otras máquinas (no solo localhost).


## Troubleshooting

| Error | Solución |
|---|---|
| `pip: command not found` | `python -m ensurepip --upgrade` |
| `Address already in use` | El puerto 8000 ya está ocupado. Usa otro: `uvicorn app.main:app --port 8001` |
| `ModuleNotFoundError: No module named 'app'` | Asegúrate de estar en la carpeta `api/` (donde está `app/`) |
