import time
from typing import Annotated

import pytest

from whitebox import (
    Agent, FakeModel, Fallback, LoopGuard, Message, Model, ModelError, OllamaModel, RescueToolCalls,
    Retry, ToolCall, Toolbox, tool, with_timeout,
)

ANSWER = Message("assistant", "Done.")


class Flaky(Model):
    """Fails a set number of times, then answers."""

    def __init__(self, failures, retryable=True):
        self.failures = failures
        self.retryable = retryable
        self.calls = 0

    def chat(self, messages, tools=None, **options):
        self.calls += 1
        if self.calls <= self.failures:
            raise ModelError("Down.", self.retryable)
        return ANSWER


@tool
def ping(text: Annotated[str, "Anything"]) -> str:
    """Say it back."""
    return text


def test_retry_waits_longer_each_time():
    waits = []
    model = Retry(Flaky(2), sleep=waits.append)
    assert model.chat([]) == ANSWER
    assert waits == [1, 2]


def test_retry_gives_up_after_its_attempts():
    with pytest.raises(ModelError):
        Retry(Flaky(9), attempts=3, sleep=lambda seconds: None).chat([])


def test_retry_does_not_retry_a_permanent_error():
    flaky = Flaky(1, retryable=False)
    with pytest.raises(ModelError):
        Retry(flaky, sleep=lambda seconds: None).chat([])
    assert flaky.calls == 1


def test_retry_treats_an_empty_reply_as_a_failure():
    model = FakeModel([Message("assistant"), ANSWER])
    assert Retry(model, sleep=lambda seconds: None).chat([]) == ANSWER


def test_retry_works_while_streaming():
    pieces = list(Retry(Flaky(1), sleep=lambda seconds: None).stream([]))
    assert pieces == ["Done.", ANSWER]


def test_retry_does_not_restart_a_stream_that_has_started():
    class HalfStream(Model):
        def stream(self, messages, tools=None, **options):
            yield "Hel"
            raise ModelError("Lost it.", retryable=True)

    with pytest.raises(ModelError):
        list(Retry(HalfStream(), sleep=lambda seconds: None).stream([]))


def test_fallback_uses_the_next_model():
    assert Fallback([Flaky(9), Flaky(0)]).chat([]) == ANSWER
    assert list(Fallback([Flaky(9), Flaky(0)]).stream([])) == ["Done.", ANSWER]


def test_fallback_raises_when_every_model_fails():
    with pytest.raises(ModelError):
        Fallback([Flaky(9), Flaky(9)]).chat([])


@pytest.mark.parametrize("text", [
    '{"name": "ping", "arguments": {"text": "hi"}}',
    '<tool_call>\n{"name": "ping", "arguments": {"text": "hi"}}\n</tool_call>',
])
def test_rescue_finds_a_tool_call_written_as_text(text):
    model = RescueToolCalls(FakeModel([Message("assistant", text)]))
    reply = model.chat([], [ping])
    assert reply.content == "" and reply.tool_calls == [ToolCall("ping", {"text": "hi"})]


@pytest.mark.parametrize("text", ["Hello", '{"name": "fly"}', "[1, 2]"])
def test_rescue_leaves_normal_replies_alone(text):
    model = RescueToolCalls(FakeModel([Message("assistant", text)]))
    assert model.chat([], [ping]).content == text


def test_the_loop_guard_blocks_repeats_and_resets():
    asking = Message("assistant", tool_calls=[ToolCall("ping", {"text": "a"})])
    guard = LoopGuard(limit=1)
    agent = Agent(FakeModel([asking, asking, ANSWER, asking, ANSWER]), Toolbox([ping]), hooks=[guard])
    first = agent.run("Go")
    assert first.messages[3].content == "a"
    assert first.messages[5].content.startswith("Error: you've already")
    assert agent.run("Again").messages[3].content == "a"


def test_with_timeout_stops_waiting():
    @tool
    def slow(text: Annotated[str, "Anything"]) -> str:
        """Take a while."""
        time.sleep(0.3)
        return text

    toolbox = Toolbox([with_timeout(slow, 0.01)])
    assert toolbox.run(ToolCall("slow", {"text": "a"})) == "Error: slow took longer than 0.01 seconds"


def test_a_real_connection_failure_becomes_a_retryable_model_error():
    with pytest.raises(ModelError) as caught:
        OllamaModel("x", url="http://127.0.0.1:9").chat([])
    assert caught.value.retryable
