import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, func, String, text, UUID
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from src.common.types import Currency, Status
from src.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[Currency] = mapped_column(ENUM(Currency), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[Status] = mapped_column(ENUM(Status), nullable=False)
    metadata_dict: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    idempotency_key: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    webhook_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(default=None)
