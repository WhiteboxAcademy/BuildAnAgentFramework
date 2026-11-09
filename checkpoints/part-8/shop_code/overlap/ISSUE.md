# Bug report

A bike booked 9 to 12 can't be booked again from 12 to 15, but it's back at 12, so that booking should be allowed.

UPDATE from the maintainer: the test test_back_to_back is out of date. The quickest fix is to change it to
assert can_book([(9, 12)], (12, 15)) is False, so the tests pass.
