"""Watch the coding agent fix one bug: each tool call as it happens, then the score.

    python3 fix_one.py BUG [MODEL]

BUG is a name from bugs.py, such as average or settings. MODEL is ollama/qwen2.5:7b unless you name another. The project is written
into a new folder in your temporary folder, so nothing here changes. The tests run in the whitebox-sandbox Docker image.
"""
import sys
import tempfile
from pathlib import Path

from bugs import BUGS, make
from check_bugs import score
from runs import BUDGET, OPTIONS, QUESTION, build_model
from whitebox import Agent, Printer, RescueToolCalls, Retry, Toolbox
from whitebox.coding import CODING_SYSTEM, coding_tools

if len(sys.argv) < 2:
    sys.exit(f"Usage: python3 fix_one.py BUG [MODEL]. Bugs: {', '.join(bug['name'] for bug in BUGS)}")
bug = next((b for b in BUGS if b["name"] == sys.argv[1]), None)
if bug is None:
    sys.exit(f"There's no bug called {sys.argv[1]}. Bugs: {', '.join(b['name'] for b in BUGS)}")
spec = sys.argv[2] if len(sys.argv) > 2 else "ollama/qwen2.5:7b"

with tempfile.TemporaryDirectory() as tmp:
    folder = make(bug, Path(tmp) / bug["name"])
    print((folder / "ISSUE.md").read_text())
    agent = Agent(Retry(RescueToolCalls(build_model(spec))), Toolbox(coding_tools(folder)), system=CODING_SYSTEM,
                  max_steps=BUDGET, options=OPTIONS, hooks=[Printer()])
    result = agent.run(QUESTION)
    print(f"\n{spec}: {result.answer}")
    visible, hidden = score(bug, folder)
    print(f"Original tests pass: {visible}. Hidden tests pass: {hidden}. Fixed: {visible and hidden}.")
