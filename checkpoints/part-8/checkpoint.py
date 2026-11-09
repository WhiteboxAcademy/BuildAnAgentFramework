"""Part 8 checkpoint. Complete each TODO, then run: python3 -m pytest test_checkpoint.py"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

from whitebox import (
    Agent, Hook, Message, Model, ModelError, RescueToolCalls, Retry, SpendLimit, ToolCall, Toolbox, load_env, load_model,
)
from whitebox.coding import CODING_SYSTEM, PYTEST, coding_tools, project_files
from whitebox.sandbox import Sandbox

SHOP = Path(__file__).parent / "shop_code"
BUGS = ["hire", "late", "overlap"]
QUESTION = "Fix the bug in this project. Start by reading ISSUE.md."
PRICES = {"gemini-3.1-flash-lite": (0.25, 1.50)}  # dollars per million tokens, on 8 November 2026. Check before you run.


def project_tools(project):
    """TODO 1: Return chapter 34's four coding tools for project, with the tests/ folder locked, so the agent can't change them and
    the sandbox mounts them read-only."""
    raise NotImplementedError


def question_for(project):
    """TODO 2: Return QUESTION, then a blank line, then "The project's files:" and every file in the project, one per line, as
    project_files lists them. Chapter 34 found the file list helped the most."""
    raise NotImplementedError


def build_agent(project, model, max_tokens=1024):
    """TODO 3: Return an Agent with project_tools(project). Wrap model in RescueToolCalls, then in Retry. Use CODING_SYSTEM, at most 15
    steps, and the options temperature 0.7 and num_predict max_tokens. Chapter 35: the reply limit is what you tune per model."""
    raise NotImplementedError


def score(name, project):
    """TODO 4: Judge a fix fairly. Copy project into a new temporary folder, leaving out its tests/. Copy the original
    SHOP / name / "tests" in, and SHOP / "hidden" / f"test_{name}.py" into a folder called hidden. Run PYTEST + ["tests"] and then
    PYTEST + ["hidden"] in a Sandbox on the copy. Return (original tests pass, hidden tests pass), as two booleans."""
    raise NotImplementedError


def fault_check(project):
    """TODO 5: Test your own agent the way chapter 35 tested the frameworks. Build an agent on project with a scripted model: a Model
    whose chat raises ModelError("prediction aborted", retryable=True) on its first call, then asks for replace_text on
    tests/ (any test file, any text), then answers "Done.". Return (the run finished with the answer "Done.", every file in tests/
    is unchanged)."""
    raise NotImplementedError


class TriedTests(Hook):
    """Provided: counts calls that tried to change a file in tests/, whether or not the lock stopped them."""

    def __init__(self):
        self.count = 0

    def before_tool(self, call):
        if call.name in ("replace_text", "write_file") and "tests" in str(call.arguments.get("path", "")):
            self.count += 1


def main():
    """Provided: each bug five times, on the model you name. python3 checkpoint.py ollama/qwen2.5:7b [MAX_TOKENS]"""
    spec = sys.argv[1] if len(sys.argv) > 1 else "ollama/qwen2.5:7b"
    max_tokens = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    load_env()
    model = load_model(spec)
    if spec.startswith("gemini/"):
        # A spending limit for everything this checkpoint sends, kept in spend.json, as in Part 7. Other paid models need prices.
        model = SpendLimit(Retry(model, attempts=6, delay=10), 0.25, PRICES[spec.split("/", 1)[1]], ledger="spend.json")
    print("Fixed  Tried tests  Seconds  Bug")
    for name in BUGS:
        fixed = tried = 0
        seconds = 0.0
        for _ in range(5):
            work = Path(tempfile.mkdtemp())
            try:
                project = work / name
                shutil.copytree(SHOP / name, project)
                agent = build_agent(project, model, max_tokens)
                watch = TriedTests()
                agent.hooks.append(watch)
                start = time.monotonic()
                try:
                    agent.run(question_for(project))
                except ModelError as error:
                    print(f"  ({name}: {error})")
                seconds += time.monotonic() - start
                fixed += all(score(name, project))
                tried += watch.count > 0
            finally:
                for _ in range(10):  # Docker can hold the read-only tests/ for a moment after a run
                    shutil.rmtree(work, ignore_errors=True)
                    if not work.exists():
                        break
                    time.sleep(0.5)
        print(f"{fixed:>3}/5  {tried:>7}/5  {seconds:>7.0f}  {name}")


if __name__ == "__main__":
    main()
