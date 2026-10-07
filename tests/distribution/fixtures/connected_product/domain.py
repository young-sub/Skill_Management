"""Business rule shared by every API path that stores a quantity."""


def validate_quantity(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Quantity must be an integer")
    if value < 0:
        raise ValueError("Quantity cannot be negative")
    return value
