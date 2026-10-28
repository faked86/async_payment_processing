import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.dtos import PaymentCreateDTO, PaymentGetDTO
from src.common.types import Currency, Status
from src.core.exceptions import PaymentNotFoundError
from src.core.payments import PaymentService
from src.db.models.outbox import Outbox
from src.db.models.payments import Payment


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.execute.return_value = MagicMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.begin = MagicMock()
    return db


def build_create_dto() -> PaymentCreateDTO:
    return PaymentCreateDTO(
        idempotency_key="test-idempotency-key",
        amount=Decimal("100.00"),
        currency=Currency.USD,
        webhook_url="https://example.com/webhook",
        description="Test payment",
        metadata_dict={"source": "test"},
    )


def build_payment(**kwargs) -> Payment:
    return Payment(
        id=kwargs.get("id", uuid.uuid4()),
        status=kwargs.get("status", Status.pending),
        amount=kwargs.get("amount", Decimal("100.00")),
        currency=kwargs.get("currency", Currency.USD),
        idempotency_key=kwargs.get("idempotency_key", "test-idempotency-key"),
        webhook_url=kwargs.get("webhook_url", "https://example.com"),
        description=kwargs.get("description", "Test payment"),
        metadata_dict=kwargs.get("metadata_dict", {}),
    )


@pytest.mark.asyncio
async def test_create_payment_success(mock_db):
    dto = build_create_dto()
    new_payment = build_payment(
        status=Status.pending,
        amount=dto.amount,
        currency=dto.currency,
        idempotency_key=dto.idempotency_key,
        webhook_url=dto.webhook_url,
        description=dto.description,
        metadata_dict=dto.metadata_dict,
    )
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_db.refresh.return_value = new_payment

    result = await PaymentService.create_payment(mock_db, dto)

    assert result is not None
    assert result.status == Status.pending
    assert result.amount == dto.amount
    assert result.currency == dto.currency
    assert result.idempotency_key == dto.idempotency_key

    mock_db.begin.assert_called_once()
    mock_db.execute.assert_awaited_once()
    assert mock_db.add.call_count == 2

    added_payment = mock_db.add.call_args_list[0].args[0]
    added_outbox = mock_db.add.call_args_list[1].args[0]
    assert isinstance(added_payment, Payment)
    assert isinstance(added_outbox, Outbox)
    assert added_outbox.event_type == "payments.new"
    assert added_outbox.payload == {"payment_id": str(added_payment.id)}
    assert added_outbox.processed is False

    mock_db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_payment_idempotency_hit(mock_db):
    dto = build_create_dto()
    existing_payment = build_payment(
        status=Status.succeeded,
        amount=dto.amount,
        currency=dto.currency,
        idempotency_key=dto.idempotency_key,
        webhook_url=dto.webhook_url,
        description=dto.description,
        metadata_dict=dto.metadata_dict,
    )
    mock_db.execute.return_value.scalar_one_or_none.return_value = existing_payment

    result = await PaymentService.create_payment(mock_db, dto)

    assert result is existing_payment
    mock_db.add.assert_not_called()
    mock_db.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_payment_success(mock_db):
    payment = build_payment()
    mock_db.execute.return_value.scalar_one_or_none.return_value = payment

    result = await PaymentService.get_payment(mock_db, PaymentGetDTO(payment_id=payment.id))

    assert result is payment
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_payment_not_found(mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(PaymentNotFoundError) as exc_info:
        await PaymentService.get_payment(mock_db, PaymentGetDTO(payment_id=uuid.uuid4()))

    assert str(exc_info.value) == "No such payment exist."
