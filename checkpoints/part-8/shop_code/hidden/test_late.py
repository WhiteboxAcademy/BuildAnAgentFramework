from datetime import datetime

from fees import late_fee

DUE = datetime(2026, 6, 1, 17, 0)


def test_more():
    assert late_fee(DUE, DUE) == 0.0
    assert late_fee(DUE, datetime(2026, 6, 1, 18, 0)) == 5.0
    assert late_fee(DUE, datetime(2026, 6, 1, 18, 1)) == 10.0
    assert late_fee(DUE, datetime(2026, 6, 2, 9, 0)) == 80.0
