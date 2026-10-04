import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.common.types import Currency


@dataclass(frozen=True)
class PaymentCreateDTO:
    amount: Decimal
    currency: Currency
    idempotency_key: str
    webhook_url: str
    description: str | None = None
    metadata_dict: dict | None = None


@dataclass(frozen=True)
class PaymentGetDTO:
    payment_id: uuid.UUID
