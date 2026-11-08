from whitebox import Agent, FakeModel, Message, Router, ToolCall, Toolbox, agent_tool


def say(text):
    return Message("assistant", text)


def call(name, **arguments):
    return Message("assistant", tool_calls=[ToolCall(name, arguments)])


def test_an_agent_becomes_a_tool():
    worker = Agent(FakeModel([say("Friday.")]))
    tool = agent_tool(worker, "ask_rota", "Ask about shifts.")
    assert tool.name == "ask_rota"
    assert tool.parameters["required"] == ["task"]
    assert tool(task="When?") == "Friday."


def test_a_manager_gets_the_workers_answer_as_a_tool_result():
    worker = Agent(FakeModel([say("Friday.")]))
    manager = Agent(FakeModel([call("ask_rota", task="When?"), say("You work Friday.")]),
                    Toolbox([agent_tool(worker, "ask_rota", "Ask about shifts.")]))
    result = manager.run("When do I work?")
    assert result.answer == "You work Friday."
    assert [m.content for m in result.messages if m.role == "tool"] == ["Friday."]


def test_each_task_starts_a_fresh_chat():
    model = FakeModel([say("One."), say("Two.")])
    tool = agent_tool(Agent(model), "ask", "Ask.")
    tool(task="First")
    tool(task="Second")
    assert [m.content for m in model.seen[1] if m.role == "user"] == ["Second"]


def test_the_router_sends_the_question_to_the_named_worker():
    router = Router(FakeModel([say("records")]), {
        "handbook": ("Rules.", Agent(FakeModel([say("From the handbook.")]))),
        "records": ("Logs.", Agent(FakeModel([say("From the records.")]))),
    })
    assert router.run("How much was lost?").answer == "From the records."
    assert router.chosen == ["records"]


def test_an_unclear_reply_goes_to_the_first_worker():
    router = Router(FakeModel([say("no idea")]), {
        "handbook": ("Rules.", Agent(FakeModel([say("From the handbook.")]))),
        "records": ("Logs.", Agent(FakeModel([say("From the records.")]))),
    })
    assert router.run("Hello").answer == "From the handbook."


def test_every_reply_has_a_limit_you_can_change():
    from whitebox import OllamaModel
    from whitebox.models import LONGEST_REPLY

    model = OllamaModel("test")
    assert model.request_body([], None, {}, stream=True)["options"]["num_predict"] == LONGEST_REPLY
    assert model.request_body([], None, {"num_predict": 50}, stream=False)["options"]["num_predict"] == 50
