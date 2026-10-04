import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.common.types import Currency, Status


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: Currency = Field(...)
    description: str | None = Field(None)
    metadata_dict: dict | None = Field(None)
    webhook_url: HttpUrl = Field(...)


class PaymentCreateResponse(BaseModel):
    payment_id: uuid.UUID = Field(..., validation_alias="id")
    status: Status = Field(...)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class PaymentGetResponse(BaseModel):
    id: uuid.UUID = Field(...)
    amount: Decimal = Field(...)
    currency: Currency = Field(...)
    description: str | None = Field(...)
    status: Status = Field(...)
    metadata_dict: dict | None = Field(...)
    idempotency_key: str = Field(...)
    webhook_url: HttpUrl = Field(...)

    created_at: datetime = Field(...)
    updated_at: datetime | None = Field(...)

    model_config = ConfigDict(from_attributes=True)
