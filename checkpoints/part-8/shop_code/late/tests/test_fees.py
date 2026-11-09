from datetime import datetime

from fees import late_fee

DUE = datetime(2026, 6, 1, 17, 0)


def test_on_time():
    assert late_fee(DUE, datetime(2026, 6, 1, 16, 50)) == 0.0


def test_part_of_an_hour():
    assert late_fee(DUE, datetime(2026, 6, 1, 17, 20)) == 5.0
    assert late_fee(DUE, datetime(2026, 6, 1, 18, 30)) == 10.0
