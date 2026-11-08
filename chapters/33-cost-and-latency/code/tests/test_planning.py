from whitebox import Chunk, FakeEmbedder, FakeModel, Index, Message, Plan, clean


def index():
    built = Index(FakeEmbedder())
    built.add([Chunk("Shift leads are Band E.", "pay-bands.md"), Chunk("Band E gives 4 weeks of notice.", "resignation.md")])
    return built


def say(text):
    return Message("assistant", text)


def test_clean_strips_bullets_and_numbers():
    assert clean('1. "Find the band"') == "Find the band"
    assert clean("- Find the band") == "Find the band"
    assert clean("2. Find form IR-7") == "Find form IR-7"
    assert clean("2.5 hours of training") == "2.5 hours of training"


def test_plan_stops_at_three_steps():
    plan = Plan(FakeModel([say("a\nb\nc\nd")]), index())
    assert plan.make_plan("Q") == ["a", "b", "c"]


def test_a_later_search_uses_what_was_found():
    model = FakeModel([say("1. Find the band\n2. Find the notice"), say("Shift leads are Band E."),
                       say("Band E notice"), say("4 weeks."), say("4 weeks.")])
    result = Plan(model, index()).run("How much notice does a shift lead give?")
    assert result.queries == ["Find the band", "Band E notice"]
    assert "Shift leads are Band E." in model.seen[2][0].content
    assert result.answer == "4 weeks."
    assert "pay-bands.md" in result.seen
