from typing import Annotated

from whitebox import Agent, Checkpoint, FakeModel, Message, ToolCall, Toolbox, load_messages, once, tool, until_done


def calls(*orders):
    return Message("assistant", tool_calls=[ToolCall("refund", {"order": order}) for order in orders])


def bank_tool(bank):
    @tool
    def refund(order: Annotated[str, "The order number"]) -> str:
        """Refund one order."""
        bank.append(order)
        return f"Refunded {order}."

    return refund


class Crash(Exception):
    pass


def test_load_returns_none_with_nothing_saved(tmp_path):
    assert load_messages(tmp_path / "run.json") is None


def test_a_finished_run_leaves_nothing_to_resume(tmp_path):
    path = tmp_path / "run.json"
    model = FakeModel([calls("A"), Message("assistant", "Done.")])
    Agent(model, Toolbox([bank_tool([])]), hooks=[Checkpoint(path)]).run("Go")
    assert not path.exists()


def test_a_run_stopped_by_max_steps_can_be_resumed(tmp_path):
    path = tmp_path / "run.json"
    model = FakeModel([calls("A"), calls("B")])
    result = Agent(model, Toolbox([bank_tool([])]), max_steps=2, hooks=[Checkpoint(path)]).run("Go")
    assert result.stopped
    assert load_messages(path)[-1].content == "Refunded B."


def test_a_save_lands_after_each_tool_in_a_batch(tmp_path):
    path = tmp_path / "run.json"
    class Run(Agent):
        def run_tool(self, call):
            if call.arguments["order"] == "C":
                raise Crash()
            return super().run_tool(call)

    model = FakeModel([calls("A", "B", "C")])
    try:
        Run(model, Toolbox([bank_tool([])]), hooks=[Checkpoint(path)]).run("Go")
    except Crash:
        pass
    saved = load_messages(path)
    assert [message.role for message in saved] == ["system", "user", "assistant", "tool", "tool"]
    assert saved[2].tool_calls[0].name == "refund"
    assert saved[-1].content == "Refunded B."


def test_resume_carries_on_from_the_saved_messages(tmp_path):
    path = tmp_path / "run.json"
    Checkpoint(path).save([Message("system", "Be kind."), Message("user", "Go")])
    model = FakeModel([Message("assistant", "Done.")])
    result = Agent(model).run("Carry on.", load_messages(path))
    assert [message.content for message in model.seen[0]] == ["Be kind.", "Go", "Carry on."]
    assert result.answer == "Done."


def test_once_asks_the_real_system(tmp_path):
    bank = ["A"]
    safe = once(bank_tool(bank), lambda order: order in bank)
    assert "Already done" in safe(order="A")
    assert safe(order="B") == "Refunded B."
    assert bank == ["A", "B"]


def test_once_keeps_the_tools_description():
    safe = once(bank_tool([]), lambda order: False)
    assert safe.name == "refund"
    assert safe.parameters["required"] == ["order"]


def test_until_done_trusts_the_bank_and_not_the_model():
    bank = []
    model = FakeModel([Message("assistant", "All done!"), calls("A"), Message("assistant", "Done.")])
    agent = Agent(model, Toolbox([bank_tool(bank)]))
    until_done(agent, lambda: [order for order in ["A"] if order not in bank], lambda items: f"Still to do: {items}")
    assert bank == ["A"]
    assert "Still to do" in model.seen[1][-1].content


def test_until_done_stops_when_nothing_is_left():
    assert until_done(Agent(FakeModel([])), lambda: [], lambda items: "Go") is None


def test_until_done_gives_up_after_its_tries():
    model = FakeModel([Message("assistant", "Done.") for _ in range(2)])
    until_done(Agent(model), lambda: ["A"], lambda items: "Go", tries=2)
    assert model.replies == []
