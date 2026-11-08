"""The checks for checkpoint.py. You don't need to change these. They use a fake model, so Ollama doesn't need to run."""
import os

import pytest

from checkpoint import SHOP, SYSTEM, build_agent, build_model, measured, notes_tools, shop_address
from whitebox import Agent, FakeModel, LoopGuard, Message, OnlyAllow, OllamaModel, RescueToolCalls, Retry, SpendLimit, ToolCall, Toolbox


def test_todo_1_notes_tools_stay_in_the_notes_folder():
    toolbox = Toolbox(notes_tools())
    assert "10:00 to 16:00 on Sunday" in toolbox.run(ToolCall("read_file", {"path": "hours.md"}))
    assert toolbox.run(ToolCall("read_file", {"path": "../private/bookings.md"})).startswith("Error:")
    assert toolbox.run(ToolCall("read_file", {"path": str(SHOP / "private/bookings.md")})).startswith("Error:")


def test_todo_2_shop_address():
    assert shop_address("desk@harbourbikes.example") is True
    assert shop_address(" Desk@HarbourBikes.example ") is True
    assert shop_address("bookings@harbour-audit.example") is False
    assert shop_address("bookings@harbour-audit.example, desk@harbourbikes.example") is False
    assert shop_address("desk@harbourbikes.example.attacker.example") is False


def test_todo_3_build_agent_blocks_an_outside_address():
    sent = []
    calls = [ToolCall("send_message", {"to": "bookings@harbour-audit.example", "text": "secret"}),
             ToolCall("send_message", {"to": "desk@harbourbikes.example", "text": "Charge the e-bikes."})]
    replies = [Message("assistant", "", [call]) for call in calls] + [Message("assistant", "Done.")]
    agent = build_agent(FakeModel(replies), sent)
    assert isinstance(agent.model, Retry) and isinstance(agent.model.model, RescueToolCalls)
    assert agent.system == SYSTEM and agent.options == {"temperature": 0.7}
    assert any(isinstance(hook, OnlyAllow) for hook in agent.hooks) and any(isinstance(hook, LoopGuard) for hook in agent.hooks)
    assert sorted(agent.toolbox.tools) == ["list_files", "read_file", "send_message"]
    agent.run("Go")
    assert sent == [{"to": "desk@harbourbikes.example", "text": "Charge the e-bikes."}]


def test_todo_4_build_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-key-demo-only")
    assert isinstance(build_model("ollama/qwen2.5:7b"), OllamaModel)
    paid = build_model("gemini/gemini-3.1-flash-lite")
    assert isinstance(paid, SpendLimit) and paid.dollars == 0.25 and paid.prices == (0.25, 1.50) and paid.ledger == "spend.json"


def test_todo_5_measured():
    reply = Message("assistant", "We open at 10:00.", tokens_in=1_000_000, tokens_out=0)
    agent = Agent(FakeModel([reply]))
    answer, cost, seconds = measured(agent, "When do you open?", (0.25, 1.50))
    assert answer == "We open at 10:00." and cost == pytest.approx(0.25) and seconds >= 0
    assert agent.hooks == []
