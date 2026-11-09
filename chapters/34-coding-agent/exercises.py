"""Chapter 34 exercises. Complete each TODO, then run: python3 -m pytest test_exercises.py"""
from pathlib import Path  # Provided: you'll need this.

from whitebox.safety import inside  # Provided: inside(root, path) raises ValueError if path leaves root, else returns the full Path.

LIMITS = [["--network", "none"], ["--read-only"], ["--cap-drop", "ALL"], ["--pids-limit"], ["--memory"]]


def replace_once(text, old, new, path):
    """TODO 1: The heart of replace_text. Return text with old replaced by new, if old appears exactly once. Otherwise raise
    ValueError with these words, where N is the count:
      "that text isn't in PATH. Read the file and copy the text exactly"         (0 times, or old is empty)
      "that text is in PATH N times. Include more lines so it appears once"      (more than once)
    """
    return None


def protected(root, path, protect):
    """TODO 2: Which protected folder path is in, or None. protect lists folder names such as ["tests"]. Use inside(root, path), so
    "./tests/../tests/test_a.py" counts as tests, and a path that leaves root raises ValueError.
    """
    return None


def missing_limits(command):
    """TODO 3: Which of LIMITS are missing from a docker run command, a list of strings. A limit with two parts, such as
    ["--network", "none"], is there only if the two appear next to each other. Return the missing ones, in the order of LIMITS.
    """
    return None


def cut_output(output, most):
    """TODO 4: Keep the end of long test output, where the failures and the summary are. If output is longer than most characters,
    return "...\\n" followed by its last most characters. Otherwise return it unchanged.
    """
    return None


def changed_expectations(old_test, new_test):
    """TODO 5: Spot a test whose expected value was changed. Compare the two texts line by line, by position. For each pair of lines
    that both contain " == ", have the same text before it, and differ after it, return (before, old after, new after), stripped.
    Lines without " == " in both are skipped.
    """
    return None
