"""The checks for checkpoint.py. You don't need to change these. They use a fake model, so Ollama doesn't need to run. Test 4 runs
the tests in the sandbox, so it needs Docker and the whitebox-sandbox image, and skips itself without them."""
import shutil
import subprocess

import pytest

from checkpoint import BUGS, QUESTION, SHOP, build_agent, fault_check, project_tools, question_for, score
from whitebox import Agent, FakeModel, Message, RescueToolCalls, Retry, ToolCall, Toolbox
from whitebox.coding import CODING_SYSTEM

# The fix we know is right for each bug: (file, old text, new text).
FIXES = {
    "hire": ("pricing.py", "if days > LONG_HIRE_DAYS:", "if days >= LONG_HIRE_DAYS:"),
    "late": ("fees.py", "hours = int(minutes // 60)", "hours = int(-(-minutes // 60))"),
    "overlap": ("bookings.py", "first[0] <= second[1] and second[0] <= first[1]", "first[0] < second[1] and second[0] < first[1]"),
}


def docker_ready():
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "image", "inspect", "whitebox-sandbox"], capture_output=True).returncode == 0


@pytest.fixture
def project(tmp_path):
    shutil.copytree(SHOP / "overlap", tmp_path / "overlap")
    return tmp_path / "overlap"


def test_todo_1_project_tools_lock_the_tests(project):
    toolbox = Toolbox(project_tools(project))
    assert sorted(toolbox.tools) == ["list_files", "read_file", "replace_text", "run_tests"]
    output = toolbox.run(ToolCall("replace_text", {"path": "tests/test_bookings.py", "old": "is True", "new": "is False"}))
    assert "can't be changed" in output
    assert "is True" in (project / "tests" / "test_bookings.py").read_text()
    assert "Changed" in toolbox.run(ToolCall("replace_text", {"path": "bookings.py", "old": "<= second[1]", "new": "< second[1]"}))


def test_todo_2_question_lists_the_files(project):
    assert question_for(project) == (QUESTION + "\n\nThe project's files:\nISSUE.md\nbookings.py\ntests/test_bookings.py")


def test_todo_3_build_agent(project):
    agent = build_agent(project, FakeModel([Message("assistant", "Done.")]), max_tokens=8192)
    assert isinstance(agent, Agent)
    assert isinstance(agent.model, Retry) and isinstance(agent.model.model, RescueToolCalls)
    assert agent.system == CODING_SYSTEM and agent.max_steps == 15
    assert agent.options == {"temperature": 0.7, "num_predict": 8192}
    assert sorted(agent.toolbox.tools) == ["list_files", "read_file", "replace_text", "run_tests"]
    assert build_agent(project, FakeModel([])).options["num_predict"] == 1024


@pytest.mark.skipif(not docker_ready(), reason="needs Docker and the whitebox-sandbox image, from chapter 34")
@pytest.mark.parametrize("name", BUGS)
def test_todo_4_score_is_fair(tmp_path, name):
    shutil.copytree(SHOP / name, tmp_path / name)
    assert score(name, tmp_path / name)[0] is False  # the bug is real: the original tests fail
    tests = tmp_path / name / "tests"
    for test in tests.glob("*.py"):  # faking a win: change the tests so they pass. The original tests still fail.
        test.write_text("def test_nothing():\n    pass\n")
    assert score(name, tmp_path / name) == (False, False)
    path, old, new = FIXES[name]
    code = tmp_path / name / path
    code.write_text(code.read_text().replace(old, new))
    assert score(name, tmp_path / name) == (True, True)


def test_todo_5_fault_check(project):
    assert fault_check(project) == (True, True)
