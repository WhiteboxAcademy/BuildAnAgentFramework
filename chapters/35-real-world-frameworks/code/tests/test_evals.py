from typing import Annotated

from whitebox import (
    Agent, Case, FakeModel, Message, ToolCall, Toolbox, compare, contains, excludes, finished, judged,
    load_report, run_eval, tool, used_no_tools, used_tool,
)
from whitebox.agent import Result


@tool
def ping(text: Annotated[str, "Anything"]) -> str:
    """Say it back."""
    return text


def answers(*texts):
    return FakeModel([Message("assistant", text) for text in texts])


def test_a_run_passes_only_when_every_check_passes():
    agent = Agent(answers("380", "381", "380"), Toolbox([ping]))
    report = run_eval(agent, [Case("sum", "Add.", [contains("380"), finished()])], runs=3)
    row = report.rows[0]
    assert (row.passed, row.runs) == (2, 3)
    assert row.failures == [{"run": 2, "failed": ["contains '380'"], "answer": "381"}]


def test_tool_checks_read_the_conversation():
    used = Result("a", [Message("assistant", tool_calls=[ToolCall("ping", {})])], 1)
    unused = Result("a", [Message("assistant", "a")], 1)
    assert used_tool("ping").test(used) and not used_tool("ping").test(unused)
    assert used_no_tools().test(unused) and not used_no_tools().test(used)


def test_excludes_and_finished():
    assert excludes("9").test(Result("8", [], 1))
    assert not finished().test(Result("8", [], 8, stopped=True))


def test_a_judge_grades_with_a_model():
    check = judged(answers("PASS", "fail."), "It is polite.")
    assert check.test(Result("Thanks", [], 1))
    assert not check.test(Result("No", [], 1))


def test_the_table_and_compare_show_scores():
    cases = [Case("sum", "Add.", [contains("1")])]
    before = run_eval(Agent(answers("0", "1")), cases, runs=2, label="old")
    after = run_eval(Agent(answers("1", "1")), cases, runs=2, label="new")
    assert "Total" in before.table() and "1/2" in before.table()
    assert "+1" in compare(before, after)


def test_a_report_survives_saving(tmp_path):
    report = run_eval(Agent(answers("1")), [Case("sum", "Add.", [contains("1")])], runs=1, label="x")
    path = tmp_path / "report.json"
    report.save(path)
    assert load_report(path) == report
