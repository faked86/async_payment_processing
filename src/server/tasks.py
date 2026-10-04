import asyncio
from datetime import datetime, timezone

from faststream.rabbit import RabbitBroker
from sqlalchemy import select

from src.db.models.outbox import Outbox
from src.db.session import async_session


async def outbox_relay_task(broker: RabbitBroker):
    while True:
        try:
            async with async_session() as db:
                async with db.begin():
                    query = (
                        select(Outbox)
                        .where(Outbox.processed == False)
                        .limit(10)
                        .with_for_update(skip_locked=True)
                    )

                    res = await db.execute(query)
                    messages = res.scalars().all()

                    for message in messages:
                        await broker.publish(message.payload, queue="payments.new")

                        message.processed = True
                        message.processed_at = datetime.now(timezone.utc)

            await asyncio.sleep(2)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in outbox relay: {e}")
            await asyncio.sleep(5)
