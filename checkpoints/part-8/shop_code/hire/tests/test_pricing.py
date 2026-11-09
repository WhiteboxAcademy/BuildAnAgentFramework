from pricing import hire_price


def test_one_day():
    assert hire_price("e-bike", 1) == 35.00


def test_three_days_get_the_discount():
    assert hire_price("e-bike", 3) == 94.50
