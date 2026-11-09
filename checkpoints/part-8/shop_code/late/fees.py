"""Late return fees at Harbour Bikes."""
from datetime import datetime

FEE_PER_HOUR = 5.00  # charged for every hour or part of an hour late


def late_fee(due, returned):
    """The late fee in pounds, for a bike due back at due and returned at returned (both datetimes)."""
    if returned <= due:
        return 0.0
    minutes = (returned - due).total_seconds() / 60
    hours = int(minutes // 60)
    return hours * FEE_PER_HOUR
