from bookings import can_book


def test_clash():
    assert can_book([(9, 12)], (11, 14)) is False


def test_back_to_back():
    assert can_book([(9, 12)], (12, 15)) is True
