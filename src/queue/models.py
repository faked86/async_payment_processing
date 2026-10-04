import uuid

from pydantic import BaseModel


class PaymentNotification(BaseModel):
    payment_id: uuid.UUID
