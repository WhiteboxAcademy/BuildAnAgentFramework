"""Check every hard bug: its visible tests fail before the fix, and visible and hidden tests pass after it, in the sandbox.

    python3 check_hard_bugs.py
"""
import tempfile
from pathlib import Path

from check_bugs import score
from hard_bugs import BUGS, make

if __name__ == "__main__":
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for bug in BUGS:
            broken = score(bug, make(bug, Path(tmp) / "broken"))
            fixed = score(bug, make(bug, Path(tmp) / "fixed", fixed=True))
            good = broken[0] is False and fixed == (True, True)
            bad += not good
            print(f"{'ok ' if good else 'BAD'} {bug['name']:12} {bug['why']}")
    print(f"{len(BUGS)} bugs, {bad} bad")
