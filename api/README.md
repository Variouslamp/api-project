# API — Servicio de Validación de Transacciones

API REST desarrollada con **FastAPI** para validar transacciones financieras en tiempo real. Recibe una solicitud de transacción, valida su estructura y reglas de negocio contra una base de usuarios simulada, y retorna una respuesta de aprobación o rechazo con trazabilidad mediante logs.

## Requisitos

- Python 3.11+
- pip

## Instalación y ejecución local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La API corre en `http://localhost:8000`.
Swagger UI disponible en `http://localhost:8000/docs`.

## Tests

```bash
python -m pytest tests/ -v
```

## Estructura

```
app/
├── main.py              # Punto de entrada, exception handlers
├── models.py            # Schemas Pydantic
├── logging_config.py    # Configuración de logging multilínea
├── users_db.py          # Diccionario de usuarios y saldos
├── routers/
│   └── transactions.py  # Endpoint POST /transactions/validate
└── services/
    └── validation.py    # Lógica de validación y descuento
tests/
└── test_transactions.py # 16 tests automatizados
```

## Documentación completa

Ver `../documentacion.md` para documentación detallada del proyecto.
