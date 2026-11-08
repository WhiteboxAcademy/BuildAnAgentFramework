import json
from typing import Annotated

import pytest
import requests

from whitebox import Agent, FakeModel, GeminiModel, Message, ModelError, SpendLimit, ToolCall, Toolbox, load_env, load_model, tool

KEY = "not-a-real-key-demo-only"


class Reply:
    def __init__(self, status, data):
        self.status_code = status
        self.ok = status < 400
        self.data = data
        self.text = json.dumps(data)

    def json(self):
        return self.data


class FakeGemini:
    """Stands in for requests.post, and keeps every request it was sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.sent = []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.sent.append({"url": url, "body": json, "headers": headers})
        return self.replies.pop(0)


def answer(parts, tokens_in=10, tokens_out=5, thoughts=0):
    return Reply(200, {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}],
                       "usageMetadata": {"promptTokenCount": tokens_in, "candidatesTokenCount": tokens_out, "thoughtsTokenCount": thoughts}})


@tool
def get_rota(day: Annotated[str, "A day, such as Friday"]) -> str:
    """Get the shifts for one day."""
    return "Ana opens."


def test_the_request_has_gemini_s_shape_and_the_key_is_in_a_header(monkeypatch):
    fake = FakeGemini(answer([{"text": "Hi."}]))
    monkeypatch.setattr(requests, "post", fake)
    GeminiModel("gemini-test", key=KEY).chat([Message("system", "Be brief."), Message("user", "Hello")], [get_rota])
    sent = fake.sent[0]
    assert sent["url"].endswith("/models/gemini-test:generateContent")
    assert KEY not in sent["url"]
    assert sent["headers"] == {"x-goog-api-key": KEY}
    assert sent["body"]["systemInstruction"] == {"parts": [{"text": "Be brief."}]}
    assert sent["body"]["contents"] == [{"role": "user", "parts": [{"text": "Hello"}]}]
    declared = sent["body"]["tools"][0]["functionDeclarations"][0]
    assert declared["name"] == "get_rota" and declared["parameters"]["required"] == ["day"]


def test_a_reply_becomes_a_message_and_thinking_counts_as_output(monkeypatch):
    parts = [{"functionCall": {"name": "get_rota", "args": {"day": "Friday"}, "id": "c1"}, "thoughtSignature": "SIG"}]
    monkeypatch.setattr(requests, "post", FakeGemini(answer(parts, tokens_in=100, tokens_out=20, thoughts=30)))
    reply = GeminiModel("g", key=KEY).chat([Message("user", "Who opens?")])
    assert reply.tool_calls == [ToolCall("get_rota", {"day": "Friday"}, "c1")]
    assert (reply.tokens_in, reply.tokens_out) == (100, 50)
    assert reply.raw == {"gemini_parts": parts}


def test_thought_text_is_not_part_of_the_answer(monkeypatch):
    monkeypatch.setattr(requests, "post", FakeGemini(answer([{"text": "thinking...", "thought": True}, {"text": "Ana."}])))
    assert GeminiModel("g", key=KEY).chat([Message("user", "Who?")]).content == "Ana."


def test_an_agent_sends_the_signature_back_unchanged_with_the_result(monkeypatch):
    first = [{"functionCall": {"name": "get_rota", "args": {"day": "Friday"}, "id": "c1"}, "thoughtSignature": "SIG"},
             {"functionCall": {"name": "get_rota", "args": {"day": "Saturday"}, "id": "c2"}}]
    fake = FakeGemini(answer(first), answer([{"text": "Ana opens both days."}]))
    monkeypatch.setattr(requests, "post", fake)
    result = Agent(GeminiModel("g", key=KEY), Toolbox([get_rota])).run("Who opens on Friday and Saturday?")
    assert result.answer == "Ana opens both days."
    contents = fake.sent[1]["body"]["contents"]
    assert contents[1] == {"role": "model", "parts": first}
    assert contents[2]["role"] == "user"
    assert [part["functionResponse"]["id"] for part in contents[2]["parts"]] == ["c1", "c2"]
    assert contents[2]["parts"][0]["functionResponse"]["response"] == {"result": "Ana opens."}


def test_a_reply_from_another_model_is_still_sent_in_gemini_s_shape(monkeypatch):
    fake = FakeGemini(answer([{"text": "Done."}]))
    monkeypatch.setattr(requests, "post", fake)
    history = [Message("user", "Hi"), Message("assistant", "", [ToolCall("get_rota", {"day": "Friday"})]),
               Message("tool", "Ana opens.", tool_name="get_rota")]
    GeminiModel("g", key=KEY).chat(history)
    assert fake.sent[0]["body"]["contents"][1] == {"role": "model", "parts": [{"functionCall": {"name": "get_rota", "args": {"day": "Friday"}}}]}


def test_options_are_translated_and_an_unknown_one_is_refused(monkeypatch):
    fake = FakeGemini(answer([{"text": "Hi."}]))
    monkeypatch.setattr(requests, "post", fake)
    GeminiModel("g", key=KEY).chat([Message("user", "Hi")], temperature=0.7, num_predict=1024, thinking="low")
    assert fake.sent[0]["body"]["generationConfig"] == {"temperature": 0.7, "maxOutputTokens": 1024, "thinkingConfig": {"thinkingLevel": "LOW"}}
    with pytest.raises(ValueError, match="num_ctx"):
        GeminiModel("g", key=KEY).chat([Message("user", "Hi")], num_ctx=8192)


@pytest.mark.parametrize("status, retryable", [(400, False), (403, False), (429, True), (503, True)])
def test_an_error_says_what_gemini_said_and_whether_to_retry(monkeypatch, status, retryable):
    monkeypatch.setattr(requests, "post", FakeGemini(Reply(status, {"error": {"message": "API key not valid."}})))
    with pytest.raises(ModelError, match="API key not valid") as caught:
        GeminiModel("g", key=KEY).chat([Message("user", "Hi")])
    assert caught.value.retryable is retryable
    assert KEY not in str(caught.value)


def test_a_blocked_reply_is_a_model_error(monkeypatch):
    monkeypatch.setattr(requests, "post", FakeGemini(Reply(200, {"candidates": [{"finishReason": "SAFETY"}]})))
    with pytest.raises(ModelError, match="SAFETY"):
        GeminiModel("g", key=KEY).chat([Message("user", "Hi")])


def test_no_key_says_where_to_put_one(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ModelError, match=".env"):
        GeminiModel("g")


def test_load_env_finds_the_file_above_and_keeps_settings_already_made(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("# a comment\nGEMINI_API_KEY='from-file'\nMODEL=gemini/from-file\n\n")
    (tmp_path / "chapter/code").mkdir(parents=True)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("MODEL", "ollama/already-set")
    assert load_env(tmp_path / "chapter/code") == str(tmp_path / ".env")
    import os
    assert os.environ["GEMINI_API_KEY"] == "from-file"
    assert os.environ["MODEL"] == "ollama/already-set"


def test_load_model_knows_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    assert isinstance(load_model("gemini/gemini-test"), GeminiModel)


def test_spend_limit_counts_and_stops(tmp_path):
    reply = Message("assistant", "Hi.", tokens_in=1_000_000, tokens_out=100_000)
    ledger = tmp_path / "spent.json"
    limited = SpendLimit(FakeModel([reply, reply, reply]), dollars=0.60, prices=(0.25, 1.50), ledger=ledger)
    limited.chat([Message("user", "Hi")])
    assert limited.spent == pytest.approx(0.40)
    limited.chat([Message("user", "Hi")])
    with pytest.raises(ModelError, match="limit") as caught:
        limited.chat([Message("user", "Hi")])
    assert not caught.value.retryable
    assert SpendLimit(FakeModel([]), 0.60, (0.25, 1.50), ledger=ledger).spent == pytest.approx(0.80)


def test_cached_tokens_are_counted(monkeypatch):
    reply = Reply(200, {"candidates": [{"content": {"parts": [{"text": "Hi."}]}}],
                        "usageMetadata": {"promptTokenCount": 6569, "candidatesTokenCount": 3, "cachedContentTokenCount": 3977}})
    monkeypatch.setattr(requests, "post", FakeGemini(reply))
    assert GeminiModel("g", key=KEY).chat([Message("user", "Hi")]).tokens_cached == 3977
