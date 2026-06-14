from uuid import uuid4
from datetime import datetime, timezone

from app.users_db import USERS


def make_valid_payload(overrides: dict | None = None) -> dict:
    payload = {
        "transactionId": str(uuid4()),
        "amount": 1000,
        "currency": "COP",
        "payerId": "USR-00001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if overrides:
        payload.update(overrides)
    return payload


def reset_users() -> None:
    for user in USERS:
        USERS[user] = 1_000_000
