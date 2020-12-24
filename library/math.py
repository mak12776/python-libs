def upper_bound(value: int, divisor: int):
    remaining = value % divisor
    if remaining:
        return value + divisor - remaining
    return value


def lower_bound(value: int, divisor: int):
    return value - (value % divisor)


def ceil_module(value: int, divisor: int):
    return (value // divisor) + (1 if value % divisor else 0)


def floor_module(value: int, divisor: int):
    return value // divisor


def min_max_average(numbers):
    iterable = iter(numbers)
    try:
        min_value = max_value = average = next(iterable)
    except StopIteration:
        raise ValueError('empty list of numbers')
    total = 1
    for value in iterable:
        if value > max_value:
            max_value = value
        if value < min_value:
            min_value = value
        average += value
        total += 1
    return min_value, max_value, (average / total)
