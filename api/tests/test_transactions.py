from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.users_db import USERS
from tests.conftest import make_valid_payload, reset_users

client = TestClient(app)


def setup_function():
    reset_users()


def test_valid_transaction_returns_200():
    payload = make_valid_payload()
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 200


def test_response_has_expected_structure():
    payload = make_valid_payload()
    response = client.post("/transactions/validate", json=payload)
    body = response.json()
    assert body["status"] == "APROVED"
    assert body["message"] == "La transaccion fue procesada correctamente"
    assert "processedAt" in body
    assert "traceId" in body


def test_balance_is_deducted_on_success():
    payload = make_valid_payload(overrides={
        "payerId": "USR-00003",
        "amount": 250000,
    })
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 200
    assert USERS["USR-00003"] == 750000


def test_multiple_transactions_deduct_accumulatively():
    for _ in range(3):
        payload = make_valid_payload(overrides={
            "payerId": "USR-00004",
            "amount": 100000,
        })
        response = client.post("/transactions/validate", json=payload)
        assert response.status_code == 200
    assert USERS["USR-00004"] == 700000


def test_missing_field_returns_400():
    payload = make_valid_payload()
    del payload["amount"]
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "INVALID_REQUEST"


def test_invalid_uuid_returns_400():
    payload = make_valid_payload(overrides={"transactionId": "not-a-uuid"})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_amount_zero_returns_400():
    payload = make_valid_payload(overrides={"amount": 0})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_negative_amount_returns_400():
    payload = make_valid_payload(overrides={"amount": -500})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_invalid_timestamp_format_returns_400():
    payload = make_valid_payload(overrides={"timestamp": "ayer"})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_future_timestamp_returns_400():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    payload = make_valid_payload(overrides={"timestamp": future})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_stale_timestamp_returns_400():
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    payload = make_valid_payload(overrides={"timestamp": past})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_error_response_has_trace_id():
    payload = make_valid_payload(overrides={"amount": 0})
    response = client.post("/transactions/validate", json=payload)
    body = response.json()
    assert "traceId" in body["error"]
    assert len(body["error"]["traceId"]) > 0


def test_unsupported_currency_returns_409():
    payload = make_valid_payload(overrides={"currency": "USD"})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "TRANSACTION_REJECTED"
    assert "USD" in body["error"]["details"][0]


def test_user_not_found_returns_409():
    payload = make_valid_payload(overrides={"payerId": "USR-99999"})
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "TRANSACTION_REJECTED"
    assert "USR-99999" in body["error"]["details"][0]


def test_insufficient_funds_returns_409():
    payload = make_valid_payload(overrides={
        "payerId": "USR-00001",
        "amount": 999999999,
    })
    response = client.post("/transactions/validate", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "TRANSACTION_REJECTED"
    assert "Saldo insuficiente" in body["error"]["details"][0]


def test_balance_not_deducted_on_rejection():
    payload = make_valid_payload(overrides={
        "payerId": "USR-00001",
        "amount": 999999999,
    })
    client.post("/transactions/validate", json=payload)
    assert USERS["USR-00001"] == 1_000_000
