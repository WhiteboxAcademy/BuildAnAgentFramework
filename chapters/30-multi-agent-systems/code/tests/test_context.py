import warnings

from whitebox import CutWarning, FakeModel, Message, Summarise, Trim, estimate_tokens, newest, total_tokens


def chat(count):
    messages = [Message("system", "Be kind.")]
    for number in range(count):
        messages += [Message("user", f"Question {number} " + "x" * 40), Message("assistant", f"Answer {number} " + "y" * 40)]
    return messages


def test_estimate_counts_four_characters_a_token():
    assert estimate_tokens(Message("user", "a" * 40)) == 14


def test_newest_keeps_the_end_in_order():
    kept = newest(chat(5)[1:], 40)
    assert kept[-1].content.startswith("Answer 4")
    assert len(kept) == 2


def test_newest_never_starts_on_a_tool_result():
    messages = [Message("assistant", "a" * 400), Message("tool", "result", tool_name="add"), Message("assistant", "done")]
    assert [message.role for message in newest(messages, 30)] == ["assistant"]


def test_trim_keeps_the_system_message():
    messages = chat(20)
    Trim(100).before_model(messages)
    assert messages[0].content == "Be kind."
    assert total_tokens(messages) <= 100
    assert messages[-1].content.startswith("Answer 19")


def test_trim_leaves_a_short_chat_alone():
    messages = chat(2)
    Trim(1000).before_model(messages)
    assert len(messages) == 5


def test_summarise_replaces_older_messages():
    model = FakeModel([Message("assistant", "They asked about shifts.")])
    messages = chat(20)
    Summarise(model, 200).before_model(messages)
    assert "They asked about shifts." in messages[0].content
    assert "Be kind." in messages[0].content
    assert messages[-1].content.startswith("Answer 19")
    assert total_tokens(messages) < 200


def test_summarising_again_and_again_stays_near_the_budget():
    model = FakeModel([Message("assistant", "n" * 200) for _ in range(100)])
    hook = Summarise(model, 300)
    messages = [Message("system", "Be kind.")]
    for number in range(60):
        messages += [Message("user", "q" * 200), Message("assistant", "a" * 200)]
        hook.before_model(messages)
        assert total_tokens(messages) <= 300
    assert messages[0].content.count("Earlier in this conversation") == 1
    assert "Earlier notes: " + "n" * 200 in model.seen[-1][0].content


def test_summarise_leaves_a_short_chat_alone():
    model = FakeModel([])
    messages = chat(2)
    Summarise(model, 1000).before_model(messages)
    assert len(messages) == 5


def test_cut_warning_speaks_up():
    hook = CutWarning()
    hook.before_model(chat(20))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        hook.after_model(Message("assistant", "Hi", tokens_in=10))
    assert "the model read 10" in str(caught[0].message)
