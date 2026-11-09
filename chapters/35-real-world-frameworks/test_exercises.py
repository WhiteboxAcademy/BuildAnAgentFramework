"""The checks for exercises.py. You don't need to change this file. They need neither Ollama, Docker nor the frameworks."""
from typing import Annotated

import pytest

from exercises import Script, added_messages, check_arguments, retry_once, scores
from whitebox import Agent, Message, ModelError, ToolCall, Toolbox, tool

DAYS = {"type": "object", "properties": {"days": {"type": "integer"}, "note": {"type": "string"}}, "required": ["days"]}


def test_todo_1_check_arguments():
    assert check_arguments({"days": 3}, DAYS) is None
    assert check_arguments({"days": 3, "note": "hi"}, DAYS) is None
    assert check_arguments({"days": "three"}, DAYS) == "days must be a integer, not 'three'"
    assert check_arguments({}, DAYS) == "days is missing"
    assert check_arguments({"days": True}, DAYS) == "days must be a integer, not True"
    assert check_arguments({"days": 3, "note": 5}, DAYS) == "note must be a string, not 5"


class Flaky:
    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0

    def __call__(self):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "done"


def test_todo_2_retry_once():
    assert retry_once(Flaky([])) == "done"
    flaky = Flaky([ModelError("prediction aborted", retryable=True)])
    assert retry_once(flaky) == "done" and flaky.calls == 2
    with pytest.raises(ModelError, match="bad key"):
        retry_once(Flaky([ModelError("bad key", retryable=False)]))
    with pytest.raises(ModelError, match="twice"):
        retry_once(Flaky([ModelError("once", retryable=True), ModelError("twice", retryable=True)]))
    with pytest.raises(ValueError):
        retry_once(Flaky([ValueError("not a model error")]))


@tool
def double(days: Annotated[int, "A number"]) -> str:
    """Double a number."""
    return str(days * 2)


def test_todo_3_script():
    script = Script([Message("assistant", tool_calls=[ToolCall("double", {"days": 4}, id="c1")]), Message("assistant", "8.")])
    result = Agent(script, Toolbox([double]), system="Test.").run("Double 4.")
    assert result.answer == "8."
    assert len(script.seen) == 2 and script.seen[1][-1].content == "8"
    with pytest.raises(ModelError):
        Script([ModelError("down", retryable=False)]).chat([])
    assert Script([]).chat([]).content == "(script ran out)"


def test_todo_4_added_messages():
    sent = [{"role": "system", "content": "You are a coding agent."},
            {"role": "system", "content": "Mid-conversation system messages arrive inside user turns wrapped in <system> tags."},
            {"role": "user", "content": "Fix the bug."}]
    written = [("system", "You are a coding agent."), ("user", "Fix the bug.")]
    assert added_messages(sent, written) == [("system", "Mid-conversation system messages arrive inside user turns wrapped in "
                                                        "<system> tags.")]
    assert added_messages(sent[:1], written) == []


def test_todo_5_scores():
    runs = [{"framework": "whitebox", "visible": True, "hidden": True},
            {"framework": "langgraph", "visible": True, "hidden": False},
            {"framework": "whitebox", "visible": False, "hidden": False},
            {"framework": "langgraph", "visible": True, "hidden": True}]
    assert scores(runs) == {"whitebox": "1/2", "langgraph": "1/2"}
    assert list(scores(runs)) == ["whitebox", "langgraph"]
    assert scores([]) == {}
