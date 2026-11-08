from datetime import date

from whitebox import Agent, FakeModel, Memory, Message, ToolCall, Toolbox


def today():
    return date(2026, 3, 1)


def test_notes_survive_a_new_memory(tmp_path):
    path = tmp_path / "notes.json"
    Memory(path, today).add("I'm allergic to cashews.")
    assert Memory(path, today).notes == [{"text": "I'm allergic to cashews.", "saved": "2026-03-01"}]


def test_saying_something_again_moves_it_to_the_end(tmp_path):
    memory = Memory(tmp_path / "notes.json", today)
    for text in ("I can work Thursdays.", "I can't work Thursdays.", "I can work Thursdays."):
        memory.add(text)
    assert [note["text"] for note in memory.notes] == ["I can't work Thursdays.", "I can work Thursdays."]


def test_the_tool_saves_the_users_words_not_the_models(tmp_path):
    memory = Memory(tmp_path / "notes.json", today)
    model = FakeModel([
        Message("assistant", tool_calls=[ToolCall("remember", {"fact": "user is 2 metres tall"})]),
        Message("assistant", "Noted."),
    ])
    agent = Agent(model, Toolbox([memory.tool()]), hooks=[memory])
    agent.run("My locker is number 212.")
    assert [note["text"] for note in memory.notes] == ["My locker is number 212."]


def test_system_lists_notes_oldest_first(tmp_path):
    memory = Memory(tmp_path / "notes.json", today)
    memory.add("I work at Riverside.")
    memory.add("I've moved to Station.")
    text = memory.system("Be kind.")
    assert text.startswith("Be kind.")
    assert text.index("Riverside") < text.index("Station")


def test_system_without_notes_is_unchanged(tmp_path):
    assert Memory(tmp_path / "notes.json", today).system("Be kind.") == "Be kind."
