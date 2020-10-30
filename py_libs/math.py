def upper_bound(value: int, divisor: int):
    remaining = value % divisor
    if remaining:
        return value + divisor - remaining
    return value


def lower_bound(value: int, divisor: int):
    return value - (value % divisor)
