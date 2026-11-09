import shutil
import subprocess

import pytest

from whitebox.coding import coding_tools, project_files
from whitebox.sandbox import Sandbox


def docker_ready():
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "image", "inspect", "whitebox-sandbox"], capture_output=True).returncode == 0


needs_docker = pytest.mark.skipif(not docker_ready(), reason="needs Docker and the whitebox-sandbox image")


@pytest.fixture
def project(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    (tmp_path / "tests" / "test_calc.py").write_text("from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n")
    return tmp_path


def by_name(tools):
    return {tool.name: tool for tool in tools}


def test_command_has_the_limits(project):
    command = Sandbox(project, readonly=["tests"]).command(["python", "-V"], "box")
    text = " ".join(command)
    assert "--network none" in text
    assert "--read-only" in text
    assert f"{project.resolve() / 'tests'}:/work/tests:ro" in text
    assert command[-3:] == ["20", "python", "-V"] and command[-4] == "timeout"


def test_files_and_reading(project):
    tools = by_name(coding_tools(project, sandbox=object()))
    assert tools["list_files"]() == "calc.py\ntests/test_calc.py"
    assert "return a - b" in tools["read_file"]("calc.py")
    with pytest.raises(ValueError, match="outside"):
        tools["read_file"]("../secret.txt")


def test_replace_needs_exact_text_once(project):
    replace = by_name(coding_tools(project, sandbox=object()))["replace_text"]
    with pytest.raises(ValueError, match="isn't in"):
        replace("calc.py", "return a * b", "return a + b")
    (project / "twice.py").write_text("x = 1\nx = 1\n")
    with pytest.raises(ValueError, match="2 times"):
        replace("twice.py", "x = 1", "x = 2")
    assert replace("calc.py", "a - b", "a + b") == "Changed calc.py."
    assert "a + b" in (project / "calc.py").read_text()


def test_protected_tests_cant_be_edited(project):
    tools = by_name(coding_tools(project, sandbox=object(), protect=("tests",)))
    with pytest.raises(ValueError, match="can't be changed"):
        tools["replace_text"]("tests/test_calc.py", "== 4", "== 0")
    with pytest.raises(ValueError, match="can't be changed"):
        tools["replace_text"]("./tests/../tests/test_calc.py", "== 4", "== 0")


def test_whole_file_edit(project):
    tools = by_name(coding_tools(project, sandbox=object(), edit="whole"))
    assert "replace_text" not in tools
    tools["write_file"]("calc.py", "def add(a, b):\n    return a + b\n")
    assert project_files(project) == ["calc.py", "tests/test_calc.py"]


class FakeBox:
    def __init__(self, code, output):
        self.code, self.output = code, output

    def run(self, argv):
        from whitebox.sandbox import RunResult
        return RunResult(self.code, self.output, 0.1)


def test_short_feedback_hides_the_output(project):
    run = by_name(coding_tools(project, sandbox=FakeBox(1, "assert 0 == 4"), feedback="short"))["run_tests"]
    assert run() == "Some tests failed."
    run = by_name(coding_tools(project, sandbox=FakeBox(1, "assert 0 == 4")))["run_tests"]
    assert "assert 0 == 4" in run()


@needs_docker
def test_tests_run_in_the_box(project):
    run = by_name(coding_tools(project))["run_tests"]
    assert "1 failed" in run()
    (project / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    assert "1 passed" in run()


@needs_docker
def test_box_has_no_network_and_a_time_limit(project):
    box = Sandbox(project, seconds=2)
    no_net = box.run(["python", "-c", "import socket; socket.create_connection(('1.1.1.1', 80), timeout=3)"])
    assert no_net.exit_code != 0
    slow = box.run(["python", "-c", "while True: pass"])
    assert slow.timed_out and "Stopped after 2 seconds" in slow.output
