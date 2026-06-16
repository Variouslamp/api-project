#!/usr/bin/env python3
import json
import os
import uuid as uuid_lib
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen



# ---------------------------------------------------------------------------
# funcion que carga del archivo de variables de entorno

def load_env() -> None:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# ---------------------------------------------------------------------------
# Funcion enfocada en cargar el puerto definido en el .env 

def get_port() -> int:
    raw = os.environ.get("API_PORT", "7777")
    try:
        return int(raw)
    except ValueError:
        return 7777


# ---------------------------------------------------------------------------
# Funcion que procesa la seleccion ingresada por el usuario [y/n]

def input_boolean(prompt: str, default: bool = False) -> bool:
    choices = "s/N" if not default else "S/n"
    raw = input(f"  {prompt} ({choices}): ").strip().lower()
    if raw == "":
        return default
    return raw in ("s", "si", "y", "yes")

# ---------------------------------------------------------------------------
# Funcion que valida o crea un UUID dependiendo de la decicion del usuario

def prompt_uuid(auto_generated: bool, manual: str) -> tuple[str, str]:
    if not auto_generated:
        return str(uuid_lib.uuid4()), ""
    try:
        uuid_lib.UUID(manual)
        return manual, ""
    except ValueError:
        return manual, "AVISO: el UUID ingresado no cumple con el formato UUID valido"


# ---------------------------------------------------------------------------
# Funcion que valida o crea un timestamp deacuerdo a la desicion del usuario

def prompt_timestamp(auto_generated: bool, manual: str) -> tuple[str, str]:

    if not auto_generated:
        return datetime.now(timezone.utc).isoformat(), ""
    try:
        datetime.fromisoformat(manual)
        return manual, ""
    except ValueError:
        return manual, "AVISO: el timestamp ingresado no cumple con el formato ISO 8601"


# ---------------------------------------------------------------------------
# Funcion que realiza el proceso de preguntas de la request al usuario

def collect_payload() -> dict | None:
    print()
    print("  [1/5] transactionId (UUID)")
    manual_uuid = input_boolean("  Desea ingresarlo manualmente", default=False)
    if manual_uuid:
        raw = input("  UUID: ").strip()
        value, warning = prompt_uuid(True, raw)
    else:
        value, warning = prompt_uuid(False, "")
    if warning:
        print(f"  {warning}")
    print()
    transaction_id = value

    print("  [2/5] Monto (amount)")
    print("  * Solo valores iguales o mayores a 1.")
    print("    Si desea probar errores, coloque otros valores bajo su propia responsabilidad.")
    monto = input("  Monto: ").strip()
    try:
        float(monto)
    except ValueError:
        print("  AVISO: el monto ingresado no es un numero valido")
    amount = monto

    print("  [3/5] Moneda (currency)")
    print("  * La unica divisa soportada por el servidor es COP.")
    print("    Si desea probar errores, puede ingresar otra bajo su propia responsabilidad.")
    currency = input("  Moneda: ").strip()
    print()

    print("  [4/5] Pagador (payerId)")
    print("  * Los usuarios registrados van de USR-00001 a USR-00010.")
    payer_id = input("  payerId: ").strip()
    print()

    print("  [5/5] Timestamp")
    manual_ts = input_boolean("  Desea ingresarlo manualmente", default=False)
    if manual_ts:
        raw = input("  Timestamp (ISO 8601, ej: 2026-06-13T10:30:00Z): ").strip()
        value, warning = prompt_timestamp(True, raw)
    else:
        value, warning = prompt_timestamp(False, "")
    if warning:
        print(f"  {warning}")
    print()
    timestamp = value

    payload = {
        "transactionId": transaction_id,
        "amount": amount,
        "currency": currency,
        "payerId": payer_id,
        "timestamp": timestamp,
    }

    print("=" * 58)
    print("  Resumen de la request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("=" * 58)

    if not input_boolean("  Enviar request", default=True):
        return None

    return payload


# ---------------------------------------------------------------------------
# Funcion encargada de la entrega de la request

def send_request(payload: dict, port: int) -> str:
    url = f"http://127.0.0.1:{port}/transactions/validate"
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.dumps(json.loads(body), indent=2, ensure_ascii=False)
    except HTTPError as e:
        body = e.read().decode("utf-8")
        return json.dumps(json.loads(body), indent=2, ensure_ascii=False)
    except URLError as e:
        return json.dumps({
            "error": {
                "code": "CONNECTION_ERROR",
                "message": f"No se pudo conectar al servidor: {e.reason}",
                "details": [],
                "traceId": "N/A",
            }
        }, indent=2, ensure_ascii=False)


def main() -> None:
    load_env()
    port = get_port()

    print("=" * 58)
    print("  Cliente de Validacion de Transacciones")
    print("=" * 58)
    print(f"  Servidor: http://localhost:{port}")
    print()

    while True:
        payload = collect_payload()
        if payload is None:
            print("  Cancelado. Volviendo a preguntar...\n")
            continue

        print("  Enviando request...")
        print()
        response_raw = send_request(payload, port)

        print("  " + "-" * 54)
        print("  RESPUESTA DEL SERVIDOR")
        print("  " + "-" * 54)
        print(response_raw)
        print("  " + "-" * 54)

        print()
        if not input_boolean("  Realizar otra validacion", default=True):
            break
        print()

    print("\n  Gracias por usar el cliente. Hasta luego!\n")


if __name__ == "__main__":
    main()
