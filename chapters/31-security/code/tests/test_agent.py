from typing import Annotated

import pytest

from whitebox import Agent, FakeModel, Message, OllamaModel, ToolCall, Toolbox, load_model, tool


@tool
def double(number: Annotated[int, "The number to double"]) -> int:
    """Double a number."""
    return number * 2


toolbox = Toolbox([double])
ASK = Message("assistant", tool_calls=[ToolCall("double", {"number": 4})])
ANSWER = Message("assistant", "It's 8.")


def test_run_returns_a_result():
    model = FakeModel([ASK, ANSWER])
    result = Agent(model, toolbox).run("Double 4.")
    assert (result.answer, result.steps, result.stopped) == ("It's 8.", 2, False)
    assert result.messages[-2] == Message("tool", "8", tool_name="double")


def test_the_step_limit_stops_the_loop():
    result = Agent(FakeModel([ASK, ASK]), toolbox, max_steps=2).run("Double 4.")
    assert result.stopped and result.answer == "Stopped: no answer after 2 steps."


def test_stream_yields_events_in_order():
    events = list(Agent(FakeModel([ASK, ANSWER]), toolbox).stream("Double 4."))
    assert [event.kind for event in events] == ["tool_call", "tool_result", "text", "done"]


def test_history_continues_a_conversation():
    model = FakeModel([ANSWER, Message("assistant", "Yes.")])
    agent = Agent(model, toolbox)
    first = agent.run("Hi")
    second = agent.run("Sure?", first.messages)
    assert [message.role for message in second.messages] == ["system", "user", "assistant", "user", "assistant"]


def test_an_agent_can_run_twice_without_mixing_runs():
    agent = Agent(FakeModel([ANSWER, ANSWER]), toolbox)
    agent.run("One")
    assert len(agent.run("Two").messages) == 3


def test_load_model_reads_the_provider_and_name():
    model = load_model("ollama/llama3.1:8b")
    assert isinstance(model, OllamaModel) and model.name == "llama3.1:8b"


def test_load_model_rejects_an_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        load_model("nobody/model")


def test_ollama_translation_round_trip():
    model = OllamaModel("x")
    data = {"content": "", "tool_calls": [{"function": {"name": "a", "arguments": {"b": 1}}}]}
    message = model.from_ollama(data)
    assert message.tool_calls == [ToolCall("a", {"b": 1})]
    assert model.to_ollama(message)["tool_calls"] == [{"function": {"name": "a", "arguments": {"b": 1}}}]
