"""Worked answers for chapter 34's exercises."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))  # Provided: finds code/whitebox.

from whitebox.safety import inside

LIMITS = [["--network", "none"], ["--read-only"], ["--cap-drop", "ALL"], ["--pids-limit"], ["--memory"]]


def replace_once(text, old, new, path):
    found = text.count(old) if old else 0
    if found == 0:
        raise ValueError(f"that text isn't in {path}. Read the file and copy the text exactly")
    if found > 1:
        raise ValueError(f"that text is in {path} {found} times. Include more lines so it appears once")
    return text.replace(old, new)


def protected(root, path, protect):
    full = inside(root, path)
    for folder in protect:
        if full.is_relative_to(Path(root).resolve() / folder):
            return folder
    return None


def missing_limits(command):
    def present(limit):
        return any(command[i:i + len(limit)] == limit for i in range(len(command)))
    return [" ".join(limit) for limit in LIMITS if not present(limit)]


def cut_output(output, most):
    return "...\n" + output[-most:] if len(output) > most else output


def changed_expectations(old_test, new_test):
    found = []
    for old, new in zip(old_test.splitlines(), new_test.splitlines()):
        if " == " in old and " == " in new:
            old_before, old_after = old.split(" == ", 1)
            new_before, new_after = new.split(" == ", 1)
            if old_before.strip() == new_before.strip() and old_after.strip() != new_after.strip():
                found.append((old_before.strip(), old_after.strip(), new_after.strip()))
    return found
