import enum


class Currency(enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Status(enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
