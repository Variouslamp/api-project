from datetime import datetime, timezone

from app.models import TransactionRequest, TransactionApproved
from app.users_db import USERS


class InvalidRequestError(Exception):
    def __init__(self, details: list[str]) -> None:
        self.details = details


class TransactionRejectedError(Exception):
    def __init__(self, details: list[str]) -> None:
        self.details = details


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


MAX_TIMESTAMP_AGE_SECONDS = 60


def validate_transaction(
    request: TransactionRequest, trace_id: str
) -> TransactionApproved:
    now = datetime.now(timezone.utc)
    client_ts = _ensure_aware(request.timestamp)

    if client_ts > now:
        raise InvalidRequestError(
            ["El timestamp no puede estar en el futuro"]
        )

    age = (now - client_ts).total_seconds()
    if age > MAX_TIMESTAMP_AGE_SECONDS:
        raise InvalidRequestError(
            [
                f"El timestamp supera el límite de {MAX_TIMESTAMP_AGE_SECONDS} "
                f"segundos de antigüedad"
            ]
        )

    if request.currency != "COP":
        raise TransactionRejectedError(
            [
                f"Moneda no soportada: {request.currency}. "
                f"Solo se acepta COP"
            ]
        )

    if request.payerId not in USERS:
        raise TransactionRejectedError(
            [f"El usuario {request.payerId} no existe"]
        )

    balance = USERS[request.payerId]
    if balance < request.amount:
        raise TransactionRejectedError(
            [
                f"Saldo insuficiente. "
                f"Balance: {int(balance)}, Requerido: {int(request.amount)}"
            ]
        )

    USERS[request.payerId] -= request.amount

    return TransactionApproved(
        processedAt=now,
        traceId=trace_id,
    )
