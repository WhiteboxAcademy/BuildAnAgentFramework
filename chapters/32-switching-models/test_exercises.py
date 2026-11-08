"""The checks for exercises.py. You don't need to change this file. No key, network or Ollama is needed."""
import pytest

from exercises import Budget, gemini_part, read_env_line, reply_cost, translate
from whitebox import Message, ModelError, ToolCall


def test_todo_1_gemini_part():
    assert gemini_part(Message("user", "Hi")) == {"role": "user", "parts": [{"text": "Hi"}]}
    assert gemini_part(Message("assistant", "", [ToolCall("get_rota", {"day": "Friday"})])) == {
        "role": "model", "parts": [{"functionCall": {"name": "get_rota", "args": {"day": "Friday"}}}]}
    assert gemini_part(Message("assistant", "Checking.", [ToolCall("get_rota", {})]))["parts"][0] == {"text": "Checking."}
    assert gemini_part(Message("tool", "Ana opens.", tool_name="get_rota")) == {
        "role": "user", "parts": [{"functionResponse": {"name": "get_rota", "response": {"result": "Ana opens."}}}]}


def test_todo_2_reply_cost():
    assert reply_cost(1_000_000, 0, (0.25, 1.50)) == 0.25
    assert reply_cost(587, 40, (0.25, 1.50)) == 0.000207
    assert reply_cost(0, 0, (0.75, 3.75)) == 0


def test_todo_3_translate():
    names = {"temperature": "temperature", "num_predict": "maxOutputTokens"}
    assert translate({"temperature": 0.7, "num_predict": 1024}, names) == {"temperature": 0.7, "maxOutputTokens": 1024}
    assert translate({}, names) == {}
    with pytest.raises(ValueError, match="num_ctx"):
        translate({"temperature": 0.7, "num_ctx": 8192}, names)


def test_todo_4_read_env_line():
    assert read_env_line("GEMINI_API_KEY=not-a-real-key-demo-only") == ("GEMINI_API_KEY", "not-a-real-key-demo-only")
    assert read_env_line(" MODEL = 'gemini/gemini-3.1-flash-lite' ") == ("MODEL", "gemini/gemini-3.1-flash-lite")
    assert read_env_line('NOTE="a=b"') == ("NOTE", "a=b")
    assert read_env_line("# a comment") is None
    assert read_env_line("") is None
    assert read_env_line("no equals here") is None


def test_todo_5_budget():
    budget = Budget(0.60, (0.25, 1.50))
    budget.check()
    budget.charge(1_000_000, 100_000)
    assert budget.spent == pytest.approx(0.40)
    budget.check()
    budget.charge(1_000_000, 100_000)
    with pytest.raises(ModelError) as caught:
        budget.check()
    assert caught.value.retryable is False
