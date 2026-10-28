import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.common.types import Currency, Status
from src.core.exceptions import PaymentNotFoundError
from src.db.models.payments import Payment
from src.db.session import get_session
from src.server.api.v1.payments.views import payments_router


def build_payment(**kwargs) -> Payment:
    return Payment(
        id=kwargs.get("id", uuid.uuid4()),
        status=kwargs.get("status", Status.pending),
        amount=kwargs.get("amount", Decimal("100.00")),
        currency=kwargs.get("currency", Currency.USD),
        description=kwargs.get("description", "Test payment"),
        metadata_dict=kwargs.get("metadata_dict", {}),
        idempotency_key=kwargs.get("idempotency_key", "test-idempotency-key"),
        webhook_url=kwargs.get("webhook_url", "https://example.com"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def payment_service_mock(mocker):
    mock = mocker.patch("src.server.api.v1.payments.views.PaymentService")
    mock.create_payment = AsyncMock()
    mock.get_payment = AsyncMock()
    return mock


@pytest.fixture
def client(payment_service_mock):
    app = FastAPI()
    app.include_router(payments_router)
    app.dependency_overrides[get_session] = lambda: None

    with TestClient(app) as test_client:
        yield test_client


def test_create_payment_success(payment_service_mock, client):
    mock_payment = build_payment(
        status=Status.pending,
        amount=Decimal("100.00"),
        currency=Currency.USD,
        idempotency_key="test-idempotency-key",
        webhook_url="https://example.com/webhook",
        description="Test payment",
        metadata_dict={"source": "test"},
    )
    payment_service_mock.create_payment.return_value = mock_payment

    response = client.post(
        "/payments",
        json={
            "amount": 100.0,
            "currency": "USD",
            "description": "Test payment",
            "metadata_dict": {"source": "test"},
            "webhook_url": "https://example.com/webhook",
        },
        headers={"Idempotency-Key": "test-idempotency-key"},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["payment_id"] == str(mock_payment.id)
    assert data["status"] == "pending"
    assert data["created_at"] is not None

    payment_service_mock.create_payment.assert_awaited_once()
    dto_arg = payment_service_mock.create_payment.await_args[0][1]
    assert dto_arg.idempotency_key == "test-idempotency-key"
    assert dto_arg.amount == Decimal("100.00")
    assert dto_arg.currency == Currency.USD
    assert dto_arg.webhook_url == "https://example.com/webhook"


def test_create_payment_missing_idempotency_key_422(payment_service_mock, client):
    response = client.post(
        "/payments",
        json={
            "amount": 100.0,
            "currency": "USD",
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 422
    payment_service_mock.create_payment.assert_not_awaited()


def test_get_payment_success(payment_service_mock, client):
    mock_payment = build_payment(
        status=Status.pending,
        amount=Decimal("100.00"),
        currency=Currency.USD,
        idempotency_key="test-idempotency-key",
        webhook_url="https://example.com",
        description="Test payment",
        metadata_dict={"source": "test"},
    )
    payment_service_mock.get_payment.return_value = mock_payment

    response = client.get(f"/payments/{mock_payment.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(mock_payment.id)
    assert float(data["amount"]) == 100.0
    assert data["currency"] == "USD"
    assert data["description"] == "Test payment"
    assert data["status"] == "pending"
    assert data["metadata_dict"] == {"source": "test"}
    assert data["idempotency_key"] == "test-idempotency-key"
    assert data["webhook_url"] == "https://example.com/"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None

    payment_service_mock.get_payment.assert_awaited_once()
    dto_arg = payment_service_mock.get_payment.await_args[0][1]
    assert dto_arg.payment_id == mock_payment.id


def test_get_payment_not_found(payment_service_mock, client):
    payment_service_mock.get_payment.side_effect = PaymentNotFoundError(
        "No such payment exist."
    )

    response = client.get(f"/payments/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "No such payment exist."

    payment_service_mock.get_payment.assert_awaited_once()
