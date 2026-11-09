"""Evals: run an agent on fixed cases, several times, and count what passes."""
import json
from dataclasses import asdict, dataclass, field
from typing import Callable

from .messages import Message


@dataclass
class Check:
    label: str
    test: Callable


def contains(text):
    return Check(f"contains {text!r}", lambda result: text in result.answer)


def excludes(text):
    return Check(f"excludes {text!r}", lambda result: text not in result.answer)


def tools_used(result):
    return [call.name for message in result.messages for call in message.tool_calls]


def used_tool(name):
    return Check(f"used {name}", lambda result: name in tools_used(result))


def used_no_tools():
    return Check("used no tools", lambda result: not tools_used(result))


def finished():
    return Check("finished", lambda result: not result.stopped)


def judged(model, rubric):
    """Ask a model to grade the answer, for checks that plain code can't make."""

    def test(result):
        prompt = f"Rubric: {rubric}\n\nAnswer: {result.answer}\n\nReply with only PASS or FAIL."
        reply = model.chat([Message("user", prompt)], temperature=0)
        return reply.content.strip().upper().startswith("PASS")

    return Check(f"judged: {rubric}", test)


@dataclass
class Case:
    name: str
    question: str
    checks: list[Check]


@dataclass
class Row:
    name: str
    runs: int = 0
    passed: int = 0
    steps: int = 0
    failures: list[dict] = field(default_factory=list)


@dataclass
class Report:
    label: str
    rows: list[Row]

    def score(self):
        return sum(row.passed for row in self.rows), sum(row.runs for row in self.rows)

    def table(self):
        lines = [f"{self.label}", f"{'Case':<20} {'Passed':>7} {'Steps':>6}"]
        for row in self.rows:
            lines.append(f"{row.name:<20} {f'{row.passed}/{row.runs}':>7} {row.steps / row.runs:>6.1f}")
        passed, runs = self.score()
        lines.append(f"{'Total':<20} {f'{passed}/{runs}':>7}")
        return "\n".join(lines)

    def save(self, path):
        with open(path, "w") as file:
            json.dump(asdict(self), file, indent=2)


def load_report(path):
    with open(path) as file:
        data = json.load(file)
    return Report(data["label"], [Row(**row) for row in data["rows"]])


def run_eval(agent, cases, runs=5, label="eval"):
    """Run every case several times. A run passes when all of its checks pass."""
    rows = []
    for case in cases:
        row = Row(case.name)
        for run in range(runs):
            result = agent.run(case.question)
            failed = [check.label for check in case.checks if not check.test(result)]
            row.runs += 1
            row.steps += result.steps
            if failed:
                row.failures.append({"run": run + 1, "failed": failed, "answer": result.answer})
            else:
                row.passed += 1
        rows.append(row)
    return Report(label, rows)


def compare(before, after):
    """Show how each case changed between two reports."""
    lines = [f"{'Case':<20} {before.label:>12} {after.label:>12}"]
    for old, new in zip(before.rows, after.rows):
        change = "" if old.passed == new.passed else f"  {new.passed - old.passed:+d}"
        lines.append(f"{old.name:<20} {f'{old.passed}/{old.runs}':>12} {f'{new.passed}/{new.runs}':>12}{change}")
    return "\n".join(lines)
