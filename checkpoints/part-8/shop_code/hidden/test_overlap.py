from bookings import can_book, clash


def test_more():
    assert can_book([(9, 12), (15, 18)], (12, 15)) is True
    assert can_book([(9, 12)], (8, 9)) is True
    assert can_book([(9, 12)], (10, 11)) is False
    assert clash((9, 12), (11, 13)) is True
