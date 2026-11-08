from typing import Annotated

import pytest

from whitebox import Agent, FakeModel, Message, Meter, ToolCall, Toolbox, run_many, tool, where_tokens_go


class Clock:
    """A clock that moves one second each time it's read."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        self.now += 1.0
        return self.now


@tool
def search(query: Annotated[str, "What to find"]) -> str:
    """Search."""
    return "Ana opens at 7."


def test_meter_records_each_model_call_and_the_tool_time():
    replies = [Message("assistant", "", [ToolCall("search", {"query": "opening"})], tokens_in=100, tokens_out=10),
               Message("assistant", "Ana, at 7.", tokens_in=150, tokens_out=8, tokens_cached=64)]
    meter = Meter(prices=(0.25, 1.50), clock=Clock())
    Agent(FakeModel(replies), Toolbox([search]), hooks=[meter]).run("Who opens?")
    assert [(s.tokens_in, s.tokens_out, s.tokens_cached) for s in meter.steps] == [(100, 10, 0), (150, 8, 64)]
    assert [s.seconds for s in meter.steps] == [1.0, 1.0]
    assert meter.tool_seconds == 1.0
    assert meter.cost() == pytest.approx((250 * 0.25 + 18 * 1.50) / 1_000_000)
    assert "Model 2.00 s, tools 1.00 s" in meter.report()


def test_a_free_model_costs_nothing():
    meter = Meter()
    Agent(FakeModel([Message("assistant", "Hi.", tokens_in=5, tokens_out=1)]), hooks=[meter]).run("Hi")
    assert meter.cost() == 0.0


def test_where_tokens_go_counts_each_kind():
    chat = [Message("system", "Be brief."), Message("user", "Who opens?"),
            Message("assistant", "", [ToolCall("search", {"query": "x"})]), Message("tool", "Ana opens at 7.", tool_name="search")]
    parts = where_tokens_go(chat, [search])
    assert parts["system prompt"] == 9 and parts["question"] == 10 and parts["tool results"] == 15
    assert parts["model's own turns"] == len("search") + len('{"query": "x"}')
    assert parts["tool descriptions"] > 0


def test_run_many_keeps_the_order_and_uses_a_new_agent_each_time():
    made = []

    def make_agent():
        agent = Agent(FakeModel([Message("assistant", "ok")]))
        made.append(agent)
        return agent

    results = run_many(make_agent, ["a", "b", "c", "d", "e"], workers=3)
    assert [r.messages[1].content for r in results] == ["a", "b", "c", "d", "e"]
    assert len({id(agent) for agent in made}) == 5
