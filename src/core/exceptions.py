class PaymentNotFoundError(Exception):
    """Raised when a payment with the given identifier cannot be found."""

    def __str__(self) -> str:
        return "No such payment exist."
