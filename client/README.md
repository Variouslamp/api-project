# Cliente de Validacion de Transacciones

Script CLI interactivo para probar el **Servicio de Validacion de Transacciones**.

## Uso

```bash
python client/client.py
```

## Configuracion

Editar `client/.env` para cambiar el puerto:

```env
API_PORT=7777
```

Si no existe `.env`, se usa el puerto 7777 por defecto.

## Requisitos

- Python 3.11+
- La API corriendo en `http://localhost:{port}`

## Documentacion

Ver `client/docs/instrucciones.txt` para una guia paso a paso.
Ver `client/docs/diseno.md` para detalles de diseno y decisiones tecnicas.
