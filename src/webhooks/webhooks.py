import asyncio
import logging
import uuid
from decimal import Decimal
from enum import Enum

import httpx
from pydantic import BaseModel

from src.common.types import Currency

logger = logging.getLogger("faststream")


class EventType(Enum):
    success = "payment.success"
    failed = "payment.failed"


class WebhookPayload(BaseModel):
    event: EventType
    payment_id: uuid.UUID
    amount: Decimal
    currency: Currency


class WebhookClient:
    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client

    async def send_notification(self, url: str, payload: WebhookPayload) -> bool:
        max_attempts = 3
        base_delay = 2.0

        for attempt in range(max_attempts):
            try:
                logger.info(
                    f"Sending webhook to {url} Attempt {attempt + 1}/{max_attempts}"
                )
                response = await self.httpx_client.post(
                    url, json=payload.model_dump_json(), timeout=5.0
                )

                response.raise_for_status()

                logger.info(f"Webhook successfully delivered to {url}")
                return True

            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1} failed. Error: {e}.")

                if attempt == max_attempts - 1:
                    logger.error(f"All {max_attempts} attempts to send webhook failed.")
                    return False

                sleep_time = base_delay * (2**attempt)
                logger.info(f"Waiting {sleep_time} seconds before next retry...")
                await asyncio.sleep(sleep_time)
        return False
