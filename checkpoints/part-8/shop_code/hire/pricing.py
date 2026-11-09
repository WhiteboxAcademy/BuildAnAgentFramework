"""Hire prices at Harbour Bikes."""

DAY_RATES = {"city": 18.00, "e-bike": 35.00, "kids": 12.00}
LONG_HIRE_DAYS = 3  # hires of this many days or more get the long-hire discount
LONG_HIRE_DISCOUNT = 0.10


def hire_price(bike, days):
    """The price of hiring one bike for a number of days, in pounds."""
    price = DAY_RATES[bike] * days
    if days > LONG_HIRE_DAYS:
        price *= 1 - LONG_HIRE_DISCOUNT
    return round(price, 2)
