import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.dtos import PaymentCreateDTO, PaymentGetDTO
from src.core.exceptions import PaymentNotFoundError
from src.core.payments import PaymentService
from src.db.session import get_session
from src.server.api.v1.payments.schemas import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentGetResponse,
)

payments_router = APIRouter(prefix="/payments", tags=["payments"])


@payments_router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentCreateResponse,
    summary="Create new payment.",
)
async def payment_create_view(
    payment_in: PaymentCreateRequest,
    db: AsyncSession = Depends(get_session),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    dto = PaymentCreateDTO(
        idempotency_key=idempotency_key,
        amount=payment_in.amount,
        currency=payment_in.currency,
        description=payment_in.description,
        metadata_dict=payment_in.metadata_dict,
        webhook_url=str(payment_in.webhook_url),
    )
    return await PaymentService.create_payment(db, dto)


@payments_router.get(
    "/{payment_id}",
    status_code=status.HTTP_200_OK,
    response_model=PaymentGetResponse,
    summary="Get payment info.",
)
async def payment_get_view(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
):
    dto = PaymentGetDTO(payment_id)
    try:
        return await PaymentService.get_payment(db, dto)
    except PaymentNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="No such payment exist."
        )
