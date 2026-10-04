import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from faststream.rabbit import RabbitBroker

from src.queue.broker import broker
from src.server.api import api_router
from src.server.tasks import outbox_relay_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()

    relay_task = asyncio.create_task(outbox_relay_task(broker))

    yield

    relay_task.cancel()
    try:
        await relay_task
    except asyncio.CancelledError:
        pass

    await broker.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
