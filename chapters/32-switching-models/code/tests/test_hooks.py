import json
from typing import Annotated

from whitebox import Agent, Approval, FakeModel, Hook, Message, ToolCall, Toolbox, Tracer, show_trace, tool


@tool
def double(number: Annotated[int, "The number to double"]) -> int:
    """Double a number."""
    return number * 2


toolbox = Toolbox([double])
ASK = Message("assistant", tool_calls=[ToolCall("double", {"number": 4})], tokens_in=10, tokens_out=2)
ANSWER = Message("assistant", "It's 8.", tokens_in=20, tokens_out=3)


class Recorder(Hook):
    def __init__(self):
        self.moments = []

    def before_model(self, messages):
        self.moments.append("before_model")

    def after_model(self, reply):
        self.moments.append("after_model")

    def before_tool(self, call):
        self.moments.append("before_tool")

    def after_tool(self, call, output):
        self.moments.append("after_tool")

    def on_finish(self, result):
        self.moments.append("on_finish")


def test_hooks_see_every_moment_in_order():
    recorder = Recorder()
    Agent(FakeModel([ASK, ANSWER]), toolbox, hooks=[recorder]).run("Double 4.")
    assert recorder.moments == [
        "before_model", "after_model", "before_tool", "after_tool",
        "before_model", "after_model", "on_finish",
    ]


def test_a_hook_can_block_a_tool():
    hook = Approval(["double"], ask=lambda prompt: "n")
    model = FakeModel([ASK, ANSWER])
    result = Agent(model, toolbox, hooks=[hook]).run("Double 4.")
    assert result.messages[-2].content == "Error: a person refused the call to double"


def test_approval_lets_a_tool_run_on_yes():
    hook = Approval(["double"], ask=lambda prompt: "y")
    result = Agent(FakeModel([ASK, ANSWER]), toolbox, hooks=[hook]).run("Double 4.")
    assert result.messages[-2].content == "8"


def test_every_hook_runs_even_when_one_blocks():
    recorder = Recorder()
    hook = Approval(["double"], ask=lambda prompt: "n")
    Agent(FakeModel([ASK, ANSWER]), toolbox, hooks=[hook, recorder]).run("Double 4.")
    assert "before_tool" in recorder.moments


def test_the_tracer_writes_one_line_per_moment(tmp_path, capsys):
    path = tmp_path / "trace.jsonl"
    ticks = iter(range(100))
    tracer = Tracer(path, clock=lambda: next(ticks))
    Agent(FakeModel([ASK, ANSWER]), toolbox, hooks=[tracer]).run("Double 4.")
    entries = [json.loads(line) for line in path.read_text().splitlines()]
    assert [entry["kind"] for entry in entries] == ["model", "tool", "model", "finish"]
    assert entries[0]["seconds"] == 1
    show_trace(path)
    assert "35 tokens, 2 steps: It's 8." in capsys.readouterr().out
