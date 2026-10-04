import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.dtos import PaymentCreateDTO, PaymentGetDTO
from src.common.types import Status
from src.db.models.payments import Payment
from src.db.models.outbox import Outbox


class PaymentService:
    @classmethod
    async def create_payment(cls, db: AsyncSession, dto: PaymentCreateDTO) -> Payment:
        async with db.begin():
            payment_idempotency_query = select(Payment).where(
                Payment.idempotency_key == dto.idempotency_key
            )
            res = await db.execute(payment_idempotency_query)
            payment_from_db = res.scalar_one_or_none()
            if payment_from_db is not None:
                return payment_from_db

            payment_id = uuid.uuid4()
            new_payment = Payment(
                id=payment_id,
                status=Status.pending,
                amount=dto.amount,
                currency=dto.currency,
                idempotency_key=dto.idempotency_key,
                webhook_url=dto.webhook_url,
                description=dto.description,
                metadata_dict=dto.metadata_dict,
            )
            db.add(new_payment)

            new_outbox = Outbox(
                event_type="payments.new",
                payload={"payment_id": str(payment_id)},
                processed=False,
            )
            db.add(new_outbox)

        await db.refresh(new_payment)
        return new_payment

    @classmethod
    async def get_payment(cls, db: AsyncSession, dto: PaymentGetDTO) -> Payment:
        payment_query = select(Payment).where(Payment.id == dto.payment_id)
        res = await db.execute(payment_query)
        payment_from_db = res.scalar_one_or_none()
        if payment_from_db is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="No such payment exist."
            )

        return payment_from_db
