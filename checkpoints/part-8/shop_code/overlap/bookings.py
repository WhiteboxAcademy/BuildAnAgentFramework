"""Bike bookings at Harbour Bikes. A booking is (start, end) in hours of the day; a bike is free again at its end hour."""


def clash(first, second):
    """True if two bookings of the same bike overlap."""
    return first[0] <= second[1] and second[0] <= first[1]


def can_book(bookings, new):
    """True if new doesn't clash with any of a bike's bookings."""
    return not any(clash(booking, new) for booking in bookings)
