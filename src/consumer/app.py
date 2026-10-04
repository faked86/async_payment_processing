import asyncio
import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from faststream import FastStream
from faststream.exceptions import RejectMessage
from faststream.rabbit import RabbitExchange, RabbitQueue
from sqlalchemy import select

from src.common.types import Status
from src.webhooks.webhooks import EventType, WebhookClient, WebhookPayload
from src.db.models.payments import Payment
from src.db.session import async_session
from src.queue.broker import broker
from src.queue.models import PaymentNotification

webhook_client: WebhookClient = None  # type: ignore


@asynccontextmanager
async def lifespan(**kwargs):
    global webhook_client
    async with httpx.AsyncClient() as httpx_client:
        webhook_client = WebhookClient(httpx_client)
        yield


logger = logging.getLogger("faststream")
app = FastStream(broker, lifespan=lifespan)

dlx_exchange = RabbitExchange("payments.dlx")
dlq_queue = RabbitQueue(
    name="payments.new.dlq", durable=True, routing_key="payments.new.dlq"
)

main_queue = RabbitQueue(
    name="payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.new.dlq",
    },
)


@broker.subscriber(main_queue)
async def handle_new_payment(payload: PaymentNotification):
    logger.info(f"Main queue received: {payload.payment_id}")
    async with async_session() as db:
        q = select(Payment).where(Payment.id == payload.payment_id)
        res = await db.execute(q)
        payment = res.scalar_one_or_none()

        if payment is None:
            logger.error(f"Payment {payload.payment_id} not found.")
            return

        if payment.status in (Status.failed, Status.succeeded):
            logger.info(
                f"Payment {payload.payment_id} already processed. Re-sending webhook..."
            )

            webhook_payload = WebhookPayload(
                event=(
                    EventType.success
                    if payment.status == Status.succeeded
                    else EventType.failed
                ),
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
            )

            webhook_success = await webhook_client.send_notification(
                payment.webhook_url, webhook_payload
            )
            if not webhook_success:
                raise RejectMessage()
            return

    await asyncio.sleep(random.uniform(2, 5))
    success = random.random() < 0.9

    async with async_session() as db:
        async with db.begin():
            q = select(Payment).where(Payment.id == payload.payment_id)
            res = await db.execute(q)
            payment = res.scalar_one()

            payment.updated_at = datetime.now(timezone.utc)
            payment.status = Status.succeeded if success else Status.failed

            amount = payment.amount
            currency = payment.currency
            webhook_url = payment.webhook_url
            event = EventType.success if success else EventType.failed

    webhook_payload = WebhookPayload(
        event=event,
        payment_id=payload.payment_id,
        amount=amount,
        currency=currency,
    )

    webhook_success = await webhook_client.send_notification(
        webhook_url, webhook_payload
    )

    if not webhook_success:
        raise RejectMessage()


@broker.subscriber(dlq_queue, exchange=dlx_exchange)
async def handle_dlq_messages(payload: PaymentNotification):
    logger.info(f"DLQ received broken message: {payload.payment_id}")
    # send dead messages to support staff
