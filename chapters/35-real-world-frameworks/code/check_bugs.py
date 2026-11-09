"""Check every bug: its visible tests fail before the fix, and visible and hidden tests pass after it."""
import shutil, sys, tempfile
from pathlib import Path
from whitebox.sandbox import Sandbox
from bugs import BUGS, make

PYTEST = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]


def score(bug, folder):
    """Run the original visible tests, then the hidden ones, on a copy of folder. Returns (visible ok, hidden ok)."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "p"
        shutil.copytree(folder, work, ignore=shutil.ignore_patterns("tests", "__pycache__"))
        (work / "tests").mkdir()
        (work / "tests" / f"test_{bug['name']}.py").write_text(bug["tests"])
        (work / "hidden").mkdir()
        (work / "hidden" / f"test_hidden_{bug['name']}.py").write_text(bug["hidden"])
        box = Sandbox(work, seconds=20)
        return box.run(PYTEST + ["tests"]).exit_code == 0, box.run(PYTEST + ["hidden"]).exit_code == 0


if __name__ == "__main__":
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for bug in BUGS:
            broken = score(bug, make(bug, Path(tmp) / "broken"))
            fixed = score(bug, make(bug, Path(tmp) / "fixed", fixed=True))
            good = broken[0] is False and fixed == (True, True)
            bad += not good
            print(f"{'ok ' if good else 'BAD'} {bug['name']:12} broken visible={broken[0]} hidden={broken[1]}  fixed {fixed}")
    print(f"{len(BUGS)} bugs, {bad} bad")
