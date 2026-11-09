"""The checks for exercises.py. You don't need to change this file. They need neither Ollama nor Docker."""
import pytest

from exercises import changed_expectations, cut_output, missing_limits, protected, replace_once
from whitebox.sandbox import Sandbox


def test_todo_1_replace_once():
    assert replace_once("a = 1\nb = 2\n", "b = 2", "b = 3", "x.py") == "a = 1\nb = 3\n"
    with pytest.raises(ValueError, match="that text isn't in x.py. Read the file and copy the text exactly"):
        replace_once("a = 1\n", "a = 2", "a = 3", "x.py")
    with pytest.raises(ValueError, match="that text isn't in x.py"):
        replace_once("a = 1\n", "", "a = 3", "x.py")
    with pytest.raises(ValueError, match="that text is in x.py 2 times. Include more lines so it appears once"):
        replace_once("x = 1\nx = 1\n", "x = 1", "x = 2", "x.py")


def test_todo_2_protected(tmp_path):
    (tmp_path / "tests").mkdir()
    assert protected(tmp_path, "tests/test_a.py", ["tests"]) == "tests"
    assert protected(tmp_path, "./tests/../tests/test_a.py", ["tests"]) == "tests"
    assert protected(tmp_path, "stats.py", ["tests"]) is None
    assert protected(tmp_path, "testsuite.py", ["tests"]) is None
    with pytest.raises(ValueError):
        protected(tmp_path, "../secret.txt", ["tests"])


def test_todo_3_missing_limits(tmp_path):
    assert missing_limits(Sandbox(tmp_path).command(["python", "-V"], "box")) == []
    loose = ["docker", "run", "--rm", "--memory", "256m", "--network", "bridge", "img", "python", "-V"]
    assert missing_limits(loose) == ["--network none", "--read-only", "--cap-drop ALL", "--pids-limit"]
    assert missing_limits(["docker", "run", "--network", "--read-only", "none"]) == ["--network none", "--cap-drop ALL",
                                                                                       "--pids-limit", "--memory"]


def test_todo_4_cut_output():
    assert cut_output("short", 10) == "short"
    assert cut_output("abcdefghij", 10) == "abcdefghij"
    assert cut_output("abcdefghijKLM", 10) == "...\ndefghijKLM"


def test_todo_5_changed_expectations():
    old = "from search import find\n\ndef test_last():\n    assert find([1, 3, 5, 7, 9], 9) == 4\n"
    new = "from search import find\n\ndef test_last():\n    assert find([1, 3, 5, 7, 9], 9) == -1\n"
    assert changed_expectations(old, new) == [("assert find([1, 3, 5, 7, 9], 9)", "4", "-1")]
    assert changed_expectations(old, old) == []
    added = old + "\ndef test_first():\n    assert find([1, 3], 1) == 0\n"
    assert changed_expectations(old, added) == []
    assert changed_expectations("assert f(1) == 2\n", "assert g(1) == 3\n") == []
