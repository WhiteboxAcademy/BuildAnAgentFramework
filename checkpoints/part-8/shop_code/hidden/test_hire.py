from pricing import hire_price


def test_more():
    assert hire_price("city", 2) == 36.00
    assert hire_price("city", 3) == 48.60
    assert hire_price("kids", 5) == 54.00
