"""The checks for exercises.py. You don't need to change this file. They use a fake model, so Ollama doesn't need to run."""
from exercises import add_up, choose_architecture, count_copied, pick_name, worker_tool
from whitebox import Agent, FakeModel, Message, ToolCall, Toolbox

LOG = "Sunny. Ran out of oat milk by 14:15. Till balanced. Ran out of banana bread by 13:45."


def say(text):
    return Message("assistant", text)


def test_todo_1_worker_tool():
    worker = Agent(FakeModel([say("Friday.")]))
    made = worker_tool(worker, "ask_rota", "Ask about shifts.")
    assert (made.name, made.description) == ("ask_rota", "Ask about shifts.")
    assert made.parameters["required"] == ["task"]
    worker = Agent(FakeModel([say("Friday.")]))
    manager = Agent(FakeModel([Message("assistant", tool_calls=[ToolCall("ask_rota", {"task": "When?"})]), say("You work Friday.")]),
                    Toolbox([worker_tool(worker, "ask_rota", "Ask about shifts.")]))
    result = manager.run("When do I work?")
    assert result.answer == "You work Friday."
    assert "Friday." in [message.content for message in result.messages if message.role == "tool"]


def test_todo_2_pick_name():
    names = ["handbook", "records"]
    assert pick_name("Records.", names) == "records"
    assert pick_name("I'd say the HANDBOOK here", names) == "handbook"
    assert pick_name("no idea", names) == "handbook"
    assert pick_name("records or handbook", names) == "handbook"


def test_todo_3_count_copied():
    assert count_copied("Ran out of oat milk by 14:15.\nRan out of banana bread by 13:45.", LOG) == 2
    assert count_copied("ran out of oat milk by 14:15.", LOG) == 1
    assert count_copied("- Ran out of oat milk by 14:15.\n2. Ran out of banana bread by 13:45.", LOG) == 2
    assert count_copied("Here are the sentences:\nRan out of oat milk by 14:15.", LOG) == 1
    assert count_copied("Ran out of scones by 09:00.", LOG) == 0
    assert count_copied("none\n\n", LOG) == 0


def test_todo_4_add_up():
    logs = {"harbour": ["Late. Bins out.", "Late."], "station": ["Bins out."]}

    def ask(text):
        return "Late." if "Late." in text else "none"

    assert add_up(logs, ask) == {"harbour": 2, "station": 0}


def test_todo_5_choose_architecture():
    assert choose_architecture({"plain_code_can_do_it": True, "fits_in_one_call": True}) == "code"
    assert choose_architecture({"needs_separate_permissions": True, "fits_in_one_call": True}) == "split for permissions"
    assert choose_architecture({"fits_in_one_call": True, "needs_more_steps": True}) == "add steps"
    assert choose_architecture({"fits_in_one_call": True}) == "one agent"
    assert choose_architecture({"splits_into_independent_pieces": True}) == "team"
    assert choose_architecture({"needs_more_steps": True}) == "rethink the job"
