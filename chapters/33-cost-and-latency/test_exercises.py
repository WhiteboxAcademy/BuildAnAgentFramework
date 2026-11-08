"""The checks for exercises.py. You don't need to change this file. They use a fake model, so Ollama doesn't need to run."""
import pytest

from exercises import ModelTimer, cached_cost, cost_per_right, run_all, shares
from whitebox import Agent, FakeModel, Message, Model, ToolCall, Toolbox, tool


def test_todo_1_shares():
    assert shares({"system prompt": 400, "tool results": 1200, "question": 400}) == {"system prompt": 0.2, "tool results": 0.6,
                                                                                    "question": 0.2}
    assert shares({"system prompt": 0, "question": 0}) == {"system prompt": 0, "question": 0}


def test_todo_2_cost_per_right():
    assert cost_per_right(54227, 3222, 38, (0.25, 1.50)) == 0.000484
    assert cost_per_right(106631, 2945, 42, (0.25, 1.50)) == 0.00074
    assert cost_per_right(1000, 10, 0, (0.25, 1.50)) is None


def test_todo_3_cached_cost():
    assert cached_cost(4869, 0, 3, (0.25, 1.50)) == 0.001222
    assert cached_cost(4869, 2033, 3, (0.25, 1.50)) == 0.000764
    assert cached_cost(1_000_000, 1_000_000, 0, (0.75, 3.75)) == 0.075


class Clock:
    def __init__(self, steps):
        self.times = iter(steps)

    def __call__(self):
        return next(self.times)


@tool
def search() -> str:
    """Search."""
    return "Found."


def test_todo_4_model_timer():
    timer = ModelTimer(Clock([10.0, 12.5, 20.0, 21.0]))
    replies = [Message("assistant", "", [ToolCall("search", {})]), Message("assistant", "Done.")]
    Agent(FakeModel(replies), Toolbox([search]), hooks=[timer]).run("Go")
    assert timer.seconds == [2.5, 1.0]


class Echo(Model):
    """Replies with the question, so we can check the order."""

    def chat(self, messages, tools=None, **options):
        return Message("assistant", messages[-1].content.upper())


def test_todo_5_run_all():
    made = []

    def make_agent():
        made.append(1)
        return Agent(Echo())

    assert run_all(make_agent, ["a", "b", "c", "d", "e"], 3) == ["A", "B", "C", "D", "E"]
    assert len(made) == 5
