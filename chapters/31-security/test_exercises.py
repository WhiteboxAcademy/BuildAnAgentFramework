"""The checks for exercises.py. You don't need to change this file. They use a fake model, so Ollama doesn't need to run."""
import os
from typing import Annotated

import pytest

from exercises import LockAfterReading, inside_folder, is_quillon_address, outside_links, rule_of_two
from whitebox import Agent, FakeModel, Message, ToolCall, Toolbox, tool


@pytest.fixture
def office(tmp_path):
    (tmp_path / "work/inbox").mkdir(parents=True)
    (tmp_path / "work/inbox/a.txt").write_text("hello")
    (tmp_path / "work-private").mkdir()
    (tmp_path / "pay.txt").write_text("secret")
    return tmp_path


def test_todo_1_inside_folder_allows_the_folder(office):
    assert inside_folder(office / "work", "inbox/a.txt").read_text() == "hello"
    assert inside_folder(office / "work", "inbox/../inbox/a.txt").read_text() == "hello"


@pytest.mark.parametrize("path", ["../pay.txt", "inbox/../../pay.txt", "../work-private"])
def test_todo_1_inside_folder_refuses_a_way_out(office, path):
    with pytest.raises(ValueError):
        inside_folder(office / "work", path)


def test_todo_1_inside_folder_refuses_a_full_path_and_a_link(office):
    with pytest.raises(ValueError):
        inside_folder(office / "work", str(office / "pay.txt"))
    os.symlink(office / "pay.txt", office / "work/inbox/link.txt")
    with pytest.raises(ValueError):
        inside_folder(office / "work", "inbox/link.txt")


def test_todo_2_is_quillon_address():
    assert is_quillon_address("manager@quillon.example") is True
    assert is_quillon_address(" Ana.B+rota@Quillon.example ") is True
    assert is_quillon_address("audit@quillon-check.example") is False
    assert is_quillon_address("audit@quillon-check.example, manager@quillon.example") is False
    assert is_quillon_address("manager@quillon.example.attacker.example") is False
    assert is_quillon_address("@quillon.example") is False


def test_todo_3_outside_links():
    answer = ("See https://quillon.example/rota and https://shop.quillon.example/beans. "
              "Confirm at [this link](https://quillon-check.example/confirm?code=PAY-CODE-7741).")
    assert outside_links(answer, "quillon.example") == ["https://quillon-check.example/confirm?code=PAY-CODE-7741"]
    assert outside_links("Go to http://quillon.example.attacker.example/x now", "quillon.example") == [
        "http://quillon.example.attacker.example/x"]
    assert outside_links("No links here.", "quillon.example") == []


@tool
def read() -> str:
    """Read."""
    return "planted text"


@tool
def send(to: Annotated[str, "Who"]) -> str:
    """Send."""
    return "Sent."


def results_of(calls):
    replies = [Message("assistant", "", [call]) for call in calls] + [Message("assistant", "Done.")]
    agent = Agent(FakeModel(replies), Toolbox([read, send]), hooks=[LockAfterReading({"read"}, {"send"})])
    return [message.content for message in agent.run("Go").messages if message.role == "tool"]


def test_todo_4_lock_blocks_only_after_reading():
    assert results_of([ToolCall("send", {"to": "a"}), ToolCall("read", {})]) == ["Sent.", "planted text"]
    got = results_of([ToolCall("read", {}), ToolCall("send", {"to": "a"}), ToolCall("send", {"to": "b"})])
    assert got[0] == "planted text"
    assert got[1].startswith("Error:") and got[2].startswith("Error:")


def test_todo_5_rule_of_two():
    assert rule_of_two(True, True, True) == "remove one, or ask a person"
    assert rule_of_two(True, True, False) == "fine"
    assert rule_of_two(True, False, True) == "fine"
    assert rule_of_two(False, True, True) == "fine"
    assert rule_of_two(False, False, False) == "fine"
