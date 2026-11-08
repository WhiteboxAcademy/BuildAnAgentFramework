from whitebox import (
    Agent, Chunk, FakeEmbedder, FakeModel, HybridIndex, Index, KeywordIndex, Message, Rag, Reranker, ToolCall, Toolbox, VectorStore, cosine, hit_rate, make_chunks, search_tool, split_text,
)

CHUNKS = [
    Chunk("Annual leave is 28 days each year.", "annual-leave.md"),
    Chunk("The grinder code E44 is a dose sensor fault.", "grinder-errors.md"),
    Chunk("Refunds under ten pounds need no approval.", "refunds.md"),
]


def index():
    built = Index(FakeEmbedder())
    built.add(CHUNKS)
    return built


def test_cosine():
    assert cosine([1, 0], [1, 0]) == 1
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([0, 0], [1, 0]) == 0


def test_search_finds_the_closest():
    assert index().search("annual leave days", 1)[0].source == "annual-leave.md"


def test_search_stops_at_k():
    assert len(index().search("anything", 2)) == 2


def test_store_saves_and_loads(tmp_path):
    store = index().store
    store.save(tmp_path / "store.json")
    loaded = VectorStore()
    loaded.load(tmp_path / "store.json")
    assert loaded.rows == store.rows


def test_split_keeps_small_text_whole():
    assert split_text("one\n\ntwo", size=10) == ["one\n\ntwo"]


def test_split_breaks_at_paragraphs():
    assert split_text("a b c\n\nd e f", size=4) == ["a b c", "d e f"]


def test_rag_puts_hits_in_the_prompt_and_answers():
    model = FakeModel([Message("assistant", "28 days [annual-leave.md]")])
    result = Rag(model, index(), k=1).run("annual leave days")
    assert result.answer.startswith("28")
    assert "Annual leave is 28" in model.seen[0][1].content


def test_hit_rate_needs_every_file():
    cases = [("annual leave", ["annual-leave.md"]), ("annual leave", ["annual-leave.md", "missing.md"])]
    assert hit_rate(index(), cases, k=3) == (1, 2)


def test_chunks_can_carry_titles():
    documents = {"x.md": "# Title\n\none two\n\nthree four"}
    chunks = make_chunks(documents, size=3, titles=True)
    assert chunks[-1].text == "Title\n\nthree four"
    assert chunks[0].source == "x.md"


def test_keyword_finds_an_exact_code():
    keyword = KeywordIndex()
    keyword.add(CHUNKS)
    assert keyword.search("E44", 1)[0].source == "grinder-errors.md"


def test_keyword_skips_chunks_with_no_shared_words():
    keyword = KeywordIndex()
    keyword.add(CHUNKS)
    assert len(keyword.search("E44", 5)) == 1


def test_hybrid_joins_rankings():
    hybrid = HybridIndex([Index(FakeEmbedder()), KeywordIndex()])
    hybrid.add(CHUNKS)
    assert hybrid.search("E44 code", 1)[0].source == "grinder-errors.md"


def test_reranker_uses_model_scores():
    replies = [Message("assistant", score) for score in ("1", "9", "2")]
    reranked = Reranker(index(), FakeModel(replies), depth=3)
    assert reranked.search("anything", 1)[0].score == 9


def test_reranker_scores_unreadable_replies_zero():
    model = FakeModel([Message("assistant", "maybe")])
    assert Reranker(index(), model, depth=1).search("anything", 1)[0].score == 0


def test_search_tool_in_an_agent():
    call = ToolCall("search_handbook", {"query": "annual leave days"})
    model = FakeModel([Message("assistant", "", [call]), Message("assistant", "28 days")])
    result = Agent(model, Toolbox([search_tool(index(), k=1)])).run("Days off?")
    assert result.answer == "28 days"
    assert "Annual leave is 28" in result.messages[3].content
